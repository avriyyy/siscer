from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from openai import OpenAI
import json
import os
import csv
from dotenv import load_dotenv
from riasec_engine import KnowledgeBase, ForwardChainingEngine, get_llm_recommendation

load_dotenv()

app = Flask(__name__)
app.secret_key = 'siscer_secret_key_2024'

kb = KnowledgeBase()

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
        return jsonify({'error': 'Skor tidak ditemukan'}), 400
        
    llm_result = get_llm_recommendation(student_scores)
    
    if llm_result and 'recommendations' in llm_result:
        engine = ForwardChainingEngine(kb)
        
        for rec in llm_result['recommendations']:
            major_name = rec['major']
            
            if major_name in kb.majors:
                major_profile = kb.majors[major_name]
                
                match_score = engine._calculate_similarity(student_scores, major_profile)
                
                profile_items = [(k, v) for k, v in major_profile.items() if k in ['R','I','A','S','E','C']]
                sorted_profile = sorted(profile_items, key=lambda x: x[1], reverse=True)
                riasec_code = ''.join([p[0] for p in sorted_profile[:3]])
                
                rec['profil_detail'] = major_profile
                rec['matching_score'] = match_score
                rec['riasec_code'] = riasec_code
                
                # We do NOT overwrite reasoning here anymore. LLM reasoning is used.
            else:
                rec['profil_detail'] = {k:0 for k in ['R','I','A','S','E','C']}
                rec['matching_score'] = 0
                rec['riasec_code'] = "N/A"

        llm_result['student_scores'] = student_scores

    return jsonify(llm_result)

if __name__ == '__main__':
    app.run(debug=True)