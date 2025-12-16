import os
import csv
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class Rule:
    def __init__(self, condition, action):
        self.condition = condition
        self.action = action

    def __repr__(self):
        return f"IF {self.condition} THEN {self.action}"

class KnowledgeBase:
    def __init__(self, base_dir=None):
        self.rules = []
        self.questions = []
        self.majors = {}
        self.base_dir = base_dir if base_dir else os.path.dirname(os.path.abspath(__file__))
        self.load_data()

    def load_data(self):
        self._load_questions()
        self._load_rules()
        self._load_majors()

    def _load_questions(self):
        self.questions = []
        current_q = None
        path = os.path.join(self.base_dir, 'questions.csv')
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return

        with open(path, 'r', encoding='utf-8') as f:
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
        path = os.path.join(self.base_dir, 'rules.csv')
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores = {}
                for type_ in ['R', 'I', 'A', 'S', 'E', 'C']:
                    val = int(row[type_])
                    if val > 0:
                        scores[type_] = val
                
                self.rules.append(Rule(row['code'], scores))

    def _load_majors(self):
        self.majors = {}
        path = os.path.join(self.base_dir, 'jurusan.csv')
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return

        with open(path, 'r', encoding='utf-8') as f:
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

class ForwardChainingEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.facts = set()
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        self.execution_log = []

    def add_fact(self, fact):
        self.facts.add(fact)

    def run(self):
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        self.execution_log = []
        
        for rule in self.kb.rules:
            if rule.condition in self.facts:
                for category, points in rule.action.items():
                    self.scores[category] += points
            else:
                pass
        
        return self.scores

    def recommend_majors(self):
        results = []
        for major_name, major_profile in self.kb.majors.items():
            match_score = self._calculate_similarity(self.scores, major_profile)
            
            profile_items = [(k, v) for k, v in major_profile.items() if k in ['R','I','A','S','E','C']]
            sorted_profile = sorted(profile_items, key=lambda x: x[1], reverse=True)
            riasec_code = ''.join([p[0] for p in sorted_profile[:3]])
            
            explanation = self.generate_explanation(major_name, self.scores, riasec_code)

            results.append({
                'major': major_name,
                'riasec_code': riasec_code,
                'matching_score': match_score,
                'explanation': explanation,
                'profil_detail': major_profile
            })
        
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

    def generate_explanation(self, major, user_scores, major_code):
        riasec_names = {
            'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
            'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
        }
        primary = major_code[0]
        secondary = major_code[1] if len(major_code) > 1 else ''
        
        return (f"Jurusan {major} memiliki profil dominan {riasec_names.get(primary, primary)} "
                f"dan {riasec_names.get(secondary, secondary)}. "
                f"Ini cocok dengan profilmu yang memiliki skor tinggi di kategori tersebut.")

def get_llm_recommendation(student_scores):
    api_key = os.getenv("GROQ_API_KEY")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    scores_text = ", ".join([f"{k}: {v}" for k, v in student_scores.items()])

    knowledge_base_text = ""
    with open(os.path.join(base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knowledge_base_text += f"- Major: {row['nama_jurusan']}, Faculty: {row['fakultas']}\n"

    prompt = f"""
    You are an expert academic counselor. Your task is to recommend the best university majors for a student based on their RIASEC scores.
    
    STUDENT PROFILE (RIASEC SCORES - Scale 0-10):
    {scores_text}
    
    KNOWLEDGE BASE (AVAILABLE MAJORS AND THEIR IDEAL PROFILES - Scale 0-10):
    {knowledge_base_text}
    
    TASK:
    1. Analyze the compatibility of the student with EVERY major in the Knowledge Base.
    2. Assign a "match_score" (0.00 to 10.00) with 2 decimal precision for EVERY major.
    3. Select the Top 3 majors with the highest scores.
    5. IMPORTANT: DO NOT TRANSLATE MAJOR NAMES. USE THE EXACT INDONESIAN NAMES FROM THE KNOWLEDGE BASE (e.g., "TEKNIK ELEKTRO", not "Electrical Engineering").
    6. Provide a reasoning ONLY for the Top 3 majors (in Bahasa Indonesia).

    RESPONSE FORMAT (JSON ONLY):
    {{
        "all_matches": {{
            "Exact Indonesian Major Name 1": 9.55,
            "Exact Indonesian Major Name 2": 8.10,
            // ... (Include ALL majors from Knowledge Base, DO NOT TRANSLATE)
        }},
        "recommendations": [
            {{
                "major": "Exact Indonesian Major Name of Rank 1",
                "match_score": 9.55,
                "reasoning": "Explanation in Bahasa Indonesia..."
            }},
            // ... (Top 3 only)
        ],
        "analysis": "A brief overall analysis of the student's profile in Bahasa Indonesia, citing specific answers."
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
