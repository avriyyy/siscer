from flask import Flask, render_template, request, redirect, url_for
import json
import os
import csv

app = Flask(__name__)


def load_knowledge_base():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    

    questions = []
    current_q = None
    with open(os.path.join(base_dir, 'questions.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if current_q is None or current_q['id'] != row['id']:
                if current_q:
                    questions.append(current_q)
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
            questions.append(current_q)


    rules = {}
    with open(os.path.join(base_dir, 'rules.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores = {}
            for type_ in ['R', 'I', 'A', 'S', 'E', 'C']:
                val = int(row[type_])
                if val > 0:
                    scores[type_] = val
            rules[row['code']] = scores


    jurusan = {}
    with open(os.path.join(base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            profil_ideal = {
                'R': int(row['R']),
                'I': int(row['I']),
                'A': int(row['A']),
                'S': int(row['S']),
                'E': int(row['E']),
                'C': int(row['C'])
            }
            jurusan[row['nama_jurusan']] = profil_ideal

    return questions, rules, jurusan


def get_major_explanation(major, student_profile, riasec_code):

    _, _, jurusan = load_knowledge_base()
    ideal_profile = jurusan.get(major, {})

    R, I, A, S, E, C = (ideal_profile.get('R', 0), ideal_profile.get('I', 0),
                        ideal_profile.get('A', 0), ideal_profile.get('S', 0),
                        ideal_profile.get('E', 0), ideal_profile.get('C', 0))


    profile_sorted = sorted([('R', R), ('I', I), ('A', A), ('S', S), ('E', E), ('C', C)],
                           key=lambda x: x[1], reverse=True)
    primary_orientation = profile_sorted[0][0] if profile_sorted[0][1] > 0 else "R"
    secondary_orientation = profile_sorted[1][0] if profile_sorted[1][1] > 0 else "I"
    

    riasec_names = {
        'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
        'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
    }


    return f"Jurusan {major} sangat cocok dengan profilmu. Jurusan ini membutuhkan dominasi tipe {riasec_names.get(primary_orientation)} dan {riasec_names.get(secondary_orientation)}. Berdasarkan analisis, minat dan potensimu selaras dengan kompetensi inti di bidang ini."


def inference_engine(answers):

    questions, rules, jurusan = load_knowledge_base()


    skor = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}


    for answer in answers:
        if answer in rules:
            for riasec_type, points in rules[answer].items():
                skor[riasec_type] += points


    sorted_skor = sorted(skor.items(), key=lambda x: x[1], reverse=True)
    student_profile = ''.join([item[0] for item in sorted_skor[:3]])


    results = []
    for major, profil_ideal in jurusan.items():
        matching_score = calculate_matching_score_v2(skor, profil_ideal)

        riasec_code_str = ''.join([item[0] for item in sorted(profil_ideal.items(), key=lambda x: x[1], reverse=True)[:3]])
        explanation = get_major_explanation(major, student_profile, riasec_code_str)
        results.append({
            'major': major,
            'riasec_code': riasec_code_str,
            'matching_score': matching_score,
            'explanation': explanation,
            'profil_detail': profil_ideal
        })


    results.sort(key=lambda x: x['matching_score'], reverse=True)

    return student_profile, results, skor


def calculate_matching_score_v2(student_scores, major_profile):

    types = ['R', 'I', 'A', 'S', 'E', 'C']


    student_total = sum(student_scores.values())
    major_total = sum(major_profile.values())

    if student_total == 0 or major_total == 0:
        return 0


    student_norm = {t: student_scores[t] / student_total if student_total > 0 else 0 for t in types}
    major_norm = {t: major_profile[t] / major_total if major_total > 0 else 0 for t in types}


    dot_product = sum(student_norm[t] * major_norm[t] for t in types)


    student_magnitude = sum(v**2 for v in student_norm.values()) ** 0.5
    major_magnitude = sum(v**2 for v in major_norm.values()) ** 0.5

    if student_magnitude == 0 or major_magnitude == 0:
        return 0


    cosine_similarity = dot_product / (student_magnitude * major_magnitude)


    score = cosine_similarity * 10

    return round(score, 2)

@app.route('/')
def index():
    _, _, jurusan = load_knowledge_base()
    

    riasec_counts = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    
    for major, profile in jurusan.items():

        dominant_type = max(profile, key=profile.get)
        if dominant_type in riasec_counts:
            riasec_counts[dominant_type] += 1
            
    return render_template('dashboard.html', chart_data=riasec_counts)

@app.route('/quiz')
def quiz():
    questions, _, _ = load_knowledge_base()
    return render_template('quiz.html', questions=questions)

@app.route('/rekomendasi', methods=['POST'])
def rekomendasi():

    answers = []
    questions, _, _ = load_knowledge_base()
    total_questions = len(questions)
    
    for i in range(1, total_questions + 1):
        answer = request.form.get(f'Q{i}')
        if answer:
            answers.append(f'Q{i}{answer}')
        else:

            return render_template('quiz.html', 
                                 questions=questions, 
                                 error="Mohon jawab semua pertanyaan sebelum melanjutkan.")
    

    student_profile, results, student_scores = inference_engine(answers)
    
    # Ambil 3 teratas
    top_3 = results[:3]
    
    return render_template('result.html', top_3=top_3, student_profile=student_profile, student_scores=student_scores)

if __name__ == '__main__':
    app.run(debug=True)