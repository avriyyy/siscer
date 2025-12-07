from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from openai import OpenAI
import json
import os
import csv
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'siscer_secret_key_2024' # Required for session

# ==========================================
# 1. KNOWLEDGE BASE & RULE DEFINITIONS
# ==========================================
# ... (No changes to classes) ...

class Rule:
    """Represents a production rule: IF condition THEN action"""
    def __init__(self, condition, action):
        self.condition = condition  # Antecedent (e.g., 'Q1Y')
        self.action = action        # Consequent (e.g., {'R': 2})

class KnowledgeBase:
    """Holds the domain knowledge: Rules, Questions, and Major Profiles"""
    def __init__(self):
        self.rules = []
        self.questions = []
        self.majors = {}
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_data()

    def load_data(self):
        self._load_questions()
        self._load_rules()
        self._load_majors()

    def _load_questions(self):
        self.questions = []
        current_q = None
        with open(os.path.join(self.base_dir, 'questions.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if current_q is None or current_q['id'] != row['id']:
                    if current_q:
                        self.questions.append(current_q)
                    current_q = {
                        'id': row['id'],
                        'kategori': row['kategori'],
                        'teks': row['teks'],
                        'pilihan': []
                    }
                current_q['pilihan'].append({
                    'value': row['option_value'],
                    'teks': row['option_text']
                })
            if current_q:
                self.questions.append(current_q)

    def _load_rules(self):
        self.rules = []
        with open(os.path.join(self.base_dir, 'rules.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores = {}
                for type_ in ['R', 'I', 'A', 'S', 'E', 'C']:
                    val = int(row[type_])
                    if val > 0:
                        scores[type_] = val
                # Rule: IF Answer == Code THEN Add Scores
                self.rules.append(Rule(row['code'], scores))

    def _load_majors(self):
        self.majors = {}
        with open(os.path.join(self.base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.majors[row['nama_jurusan']] = {
                    'R': int(row['R']),
                    'I': int(row['I']),
                    'A': int(row['A']),
                    'S': int(row['S']),
                    'E': int(row['E']),
                    'C': int(row['C']),
                    'fakultas': row['fakultas']
                }

# Initialize Knowledge Base
kb = KnowledgeBase()

# ==========================================
# 2. INFERENCE ENGINE (FORWARD CHAINING)
# ==========================================

class ForwardChainingEngine:
    """
    Inference Engine that uses Forward Chaining to deduce the user's RIASEC profile
    based on their answers (Facts) and the Rule Base.
    """
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.facts = set()
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}

    def add_fact(self, fact):
        self.facts.add(fact)

    def run(self):
        """
        Execute the Forward Chaining cycle.
        1. Match Facts against Rules.
        2. Fire Rules to update State (Scores).
        """
        # Reset scores
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        
        # Cycle through all rules (Data-Driven)
        for rule in self.kb.rules:
            if rule.condition in self.facts:
                # Rule Fired! Apply consequent
                for category, points in rule.action.items():
                    self.scores[category] += points
        
        return self.scores

    def recommend_majors(self):
        """
        Uses the derived scores to find matching majors.
        Uses Cosine Similarity as the matching heuristic.
        """
        results = []
        for major_name, major_profile in self.kb.majors.items():
            match_score = self._calculate_similarity(self.scores, major_profile)
            
            # Determine Major's RIASEC Code
            profile_items = [(k, v) for k, v in major_profile.items() if k in ['R','I','A','S','E','C']]
            sorted_profile = sorted(profile_items, key=lambda x: x[1], reverse=True)
            riasec_code = ''.join([p[0] for p in sorted_profile[:3]])
            
            # Generate Explanation
            explanation = self._generate_explanation(major_name, self.scores, riasec_code)

            results.append({
                'major': major_name,
                'riasec_code': riasec_code,
                'matching_score': match_score,
                'explanation': explanation,
                'profil_detail': major_profile
            })
        
        # Sort by score
        results.sort(key=lambda x: x['matching_score'], reverse=True)
        return results

    def _calculate_similarity(self, user_scores, major_profile):
        types = ['R', 'I', 'A', 'S', 'E', 'C']
        
        user_vec = [user_scores[t] for t in types]
        major_vec = [major_profile[t] for t in types]
        
        dot_product = sum(u * m for u, m in zip(user_vec, major_vec))
        user_mag = sum(u**2 for u in user_vec) ** 0.5
        major_mag = sum(m**2 for m in major_vec) ** 0.5
        
        if user_mag == 0 or major_mag == 0:
            return 0
            
        similarity = dot_product / (user_mag * major_mag)
        return round(similarity * 10, 2)

    def _generate_explanation(self, major, user_scores, major_code):
        riasec_names = {
            'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
            'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
        }
        primary = major_code[0]
        secondary = major_code[1]
        return f"Jurusan {major} sangat cocok dengan profilmu. Jurusan ini membutuhkan dominasi tipe {riasec_names.get(primary, primary)} dan {riasec_names.get(secondary, secondary)}."

# ==========================================
# 3. LLM HELPER
# ==========================================

from groq import Groq

def get_llm_recommendation(student_scores):
    # API Key provided by user
    api_key = os.getenv("GROQ_API_KEY")
    
    # Load full knowledge base from CSV to include Faculty and Scores
    base_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_base_text = ""
    with open(os.path.join(base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knowledge_base_text += f"- Major: {row['nama_jurusan']}, Faculty: {row['fakultas']}, RIASEC Profile: R={row['R']}, I={row['I']}, A={row['A']}, S={row['S']}, E={row['E']}, C={row['C']}\n"

    # Format scores for prompt
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
    
    Please provide the response in the following JSON format:
    {{
        "recommendations": [
            {{
                "major": "Exact Major Name from Knowledge Base",
                "reasoning": "Explanation referencing the student's scores vs the major's profile."
            }},
            ...
        ],
        "analysis": "A brief overall analysis of the student's profile."
    }}
    """
    
    client = Groq(api_key=api_key)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        completion = client.chat.completions.create(
            model=model_name, # Switched to a supported model
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
            stream=False # We need the full response for JSON parsing, not stream
        )
        
        content = completion.choices[0].message.content
        
        # Try to parse JSON from content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
        
    except Exception as e:
        print(f"LLM Exception: {e}")
        return None

# ==========================================
# 4. FLASK ROUTES
# ==========================================

@app.route('/')
def index():
    # Reload KB to ensure fresh data
    kb.load_data()
    
    # Calculate distribution for dashboard
    riasec_counts = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    for major, profile in kb.majors.items():
        # Find dominant type
        profile_only = {k: v for k, v in profile.items() if k in riasec_counts}
        dominant = max(profile_only, key=profile_only.get)
        riasec_counts[dominant] += 1
            
    return render_template('dashboard.html', chart_data=riasec_counts)

@app.route('/quiz')
def quiz():
    # Group questions by category in RIASEC order
    ordered_categories = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
    grouped_questions = {cat: [] for cat in ordered_categories}
    
    for q in kb.questions:
        if q['kategori'] in grouped_questions:
            grouped_questions[q['kategori']].append(q)
            
    # Convert to list of tuples for easy iteration in template
    questions_grouped = [(cat, grouped_questions[cat]) for cat in ordered_categories]
    
    return render_template('quiz.html', questions_grouped=questions_grouped)

@app.route('/rekomendasi', methods=['POST'])
def rekomendasi():
    # 1. Collect Facts (User Answers)
    engine = ForwardChainingEngine(kb)
    
    # Iterate through all questions to get answers
    for q in kb.questions:
        qid = q['id']
        answer_val = request.form.get(qid)
        if answer_val:
            # Fact format: Q1Y (Question ID + Answer Value)
            fact = f"{qid}{answer_val}"
            engine.add_fact(fact)
        else:
             return render_template('quiz.html', 
                                 questions=kb.questions, 
                                 error="Mohon jawab semua pertanyaan.")

    # 2. Run Inference (Forward Chaining)
    student_scores = engine.run()
    
    # Save scores to session for AI analysis
    session['student_scores'] = student_scores
    
    # 3. Get Recommendations
    results = engine.recommend_majors()
    top_3 = results[:3]
    
    # Determine Student Profile Code
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