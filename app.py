from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from openai import OpenAI
import json
import os
import csv
from dotenv import load_dotenv
from groq import Groq
from riasec_engine import KnowledgeBase, ForwardChainingEngine

load_dotenv()

app = Flask(__name__)
app.secret_key = 'siscer_secret_key_2024'

kb = KnowledgeBase()

def get_llm_recommendation(student_scores):
    api_key = os.getenv("GROQ_API_KEY")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_base_text = ""
    with open(os.path.join(base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knowledge_base_text += f"- Major: {row['nama_jurusan']}, Faculty: {row['fakultas']}, RIASEC Profile: R={row['R']}, I={row['I']}, A={row['A']}, S={row['S']}, E={row['E']}, C={row['C']}\n"

    scores_text = ", ".join([f"{k}: {v}" for k, v in student_scores.items()])
    
    prompt = f"""
    You are an expert academic counselor. Your task is to recommend the best university majors for a student based on their RIASEC scores.
    
    STUDENT PROFILE (RIASEC SCORES - Scale 0-10):
    {scores_text}
    
    KNOWLEDGE BASE (AVAILABLE MAJORS AND THEIR IDEAL PROFILES - Scale 0-10):
    {knowledge_base_text}
    
    INSTRUCTIONS:
    1. Compare the student's scores with the ideal profiles in the Knowledge Base.
    2. Select exactly 3 majors that are the best match.
    3. You MUST ONLY select majors from the KNOWLEDGE BASE list above.
    4. Provide a reasoning for each recommendation based on the score comparison.
    5. IMPORTANT: PROVIDE THE "reasoning" AND "analysis" IN BAHASA INDONESIA.
    
    Please provide the response in the following JSON format:
    {{
        "recommendations": [
            {{
                "major": "Exact Major Name from Knowledge Base",
                "reasoning": "Explanation in Bahasa Indonesia referencing the student's scores vs the major's profile."
            }},
            ...
        ],
        "analysis": "A brief overall analysis of the student's profile in Bahasa Indonesia."
    }}
    """
    
    client = Groq(api_key=api_key)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
              {
                "role": "user",
                "content": prompt
              }
            ],
            temperature=0.6,
            max_completion_tokens=4096,
            top_p=0.95,
            stop=None,
            stream=False
        )
        
        content = completion.choices[0].message.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
        
    except Exception as e:
        print(f"LLM Exception: {e}")
        return None

@app.route('/')
def index():
    kb.load_data()
    
    riasec_counts = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    for major, profile in kb.majors.items():
        profile_only = {k: v for k, v in profile.items() if k in riasec_counts}
        dominant = max(profile_only, key=profile_only.get)
        riasec_counts[dominant] += 1
            
    return render_template('dashboard.html', chart_data=riasec_counts)

@app.route('/quiz')
def quiz():
    ordered_categories = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
    grouped_questions = {cat: [] for cat in ordered_categories}
    
    for q in kb.questions:
        if q['kategori'] in grouped_questions:
            grouped_questions[q['kategori']].append(q)
            
    questions_grouped = [(cat, grouped_questions[cat]) for cat in ordered_categories]
    
    return render_template('quiz.html', questions_grouped=questions_grouped)

@app.route('/rekomendasi', methods=['POST'])
def rekomendasi():
    engine = ForwardChainingEngine(kb)
    
    for q in kb.questions:
        qid = q['id']
        answer_val = request.form.get(qid)
        if answer_val:
            fact = f"{qid}{answer_val}"
            engine.add_fact(fact)
        else:
             return render_template('quiz.html', 
                                 questions=kb.questions, 
                                 error="Mohon jawab semua pertanyaan.")

    student_scores = engine.run()
    
    session['student_scores'] = student_scores
    
    results = engine.recommend_majors()
    top_3 = results[:3]
    
    sorted_scores = sorted(student_scores.items(), key=lambda x: x[1], reverse=True)
    student_profile_code = ''.join([x[0] for x in sorted_scores[:3]])

    return render_template('result.html', 
                         top_3=top_3, 
                         student_profile=student_profile_code, 
                         student_scores=student_scores)

@app.route('/analyze_ai', methods=['POST'])
def analyze_ai():
    student_scores = session.get('student_scores')
    if not student_scores:
        return jsonify({'error': 'No scores found in session'}), 400
        
    llm_result = get_llm_recommendation(student_scores)
    return jsonify(llm_result)

if __name__ == '__main__':
    app.run(debug=True)