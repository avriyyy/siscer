import matplotlib.pyplot as plt
import time
import os
from dotenv import load_dotenv
from riasec_engine import KnowledgeBase, ForwardChainingEngine
from app import get_llm_recommendation

load_dotenv()

def run_comparative_evaluation():
    test_cases = []
    types = ['R', 'I', 'A', 'S', 'E', 'C']
    kb = KnowledgeBase()
    
    for target_type in types:
        facts = set()
        scores = {t: 0 for t in types}
        for q in kb.questions:
            cat_map = {'Realistic': 'R', 'Investigative': 'I', 'Artistic': 'A',
                       'Social': 'S', 'Enterprising': 'E', 'Conventional': 'C'}
            q_type = cat_map.get(q['kategori'])
            if q_type == target_type:
                facts.add(f"{q['id']}Y")
                scores[q_type] += 2
            else:
                facts.add(f"{q['id']}N")
        test_cases.append({'target_type': target_type, 'facts': facts, 'expected_scores': scores})

    engine = ForwardChainingEngine(kb)
    fc_latencies = []
    fc_correct = 0
    
    for case in test_cases:
        engine.facts = set()
        for fact in case['facts']:
            engine.add_fact(fact)
        
        start = time.time()
        engine.run()
        recs = engine.recommend_majors()
        fc_latencies.append(time.time() - start)
        
        if recs and recs[0]['riasec_code'].startswith(case['target_type']):
            fc_correct += 1
            
    fc_acc = (fc_correct / len(test_cases)) * 100
    fc_avg_lat = sum(fc_latencies) / len(fc_latencies)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm_latencies = []
    llm_correct = 0
    print(f"Running LLM Evaluation (Groq: {model_name})...")
    
    for case in test_cases:
        start = time.time()
        res = get_llm_recommendation(case['expected_scores'])
        llm_latencies.append(time.time() - start)
        
        if res and 'recommendations' in res and len(res['recommendations']) > 0:
            top_rec = res['recommendations'][0]['major']
            if top_rec in kb.majors:
                p_only = {k: v for k, v in kb.majors[top_rec].items() if k in types}
                if max(p_only, key=p_only.get) == case['target_type']:
                    llm_correct += 1
    
    llm_acc = (llm_correct / len(test_cases)) * 100
    llm_avg_lat = sum(llm_latencies) / len(llm_latencies)
    
    riasec_counts = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    for major, profile in kb.majors.items():
        p_only = {k: v for k, v in profile.items() if k in ['R','I','A','S','E','C']}
        dominant = max(p_only, key=p_only.get)
        riasec_counts[dominant] += 1
        
    return {
        'FC': {'Accuracy': fc_acc, 'Latency': fc_avg_lat},
        'LLM': {'Accuracy': llm_acc, 'Latency': llm_avg_lat},
        'Distribution': riasec_counts,
        'TotalMajors': len(kb.majors),
        'ModelName': model_name
    }

def create_comparison_visualization(results):
    fig = plt.figure(figsize=(12, 10))
    
    plt.suptitle("Laporan Evaluasi & Distribusi Data Sistem Pakar", fontsize=16, fontweight='bold', y=0.96)
    
    ax1 = plt.subplot2grid((2, 1), (0, 0))
    ax1.axis('off')
    ax1.set_title("Perbandingan Performa Model", fontsize=12, fontweight='bold', loc='left', pad=10)
    
    col_labels = ['Metrik Evaluasi', 'Forward Chaining (Rule-Based)', f"LLM({results['ModelName']})"]
    table_data = [
        ['Akurasi (Kesesuaian Profil)', f"{results['FC']['Accuracy']:.1f}%", f"{results['LLM']['Accuracy']:.1f}%"],
        ['Rata-rata Waktu Respon (Latency)', f"{results['FC']['Latency']:.4f} detik", f"{results['LLM']['Latency']:.4f} detik"],
        ['Metode Inferensi', 'Deterministik (Rules)', 'Probabilistik (Generative)'],
        ['Konsistensi', 'Sangat Tinggi (Selalu sama)', 'Bervariasi (Tergantung Prompt/Temp)'],
        ['Ketergantungan', 'Lokal (Tidak butuh internet)', 'API Eksternal (Butuh internet)']
    ]
    
    table = ax1.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2C241B')
        else:
            cell.set_facecolor('#FAFAF8')
            
    ax2 = plt.subplot2grid((2, 1), (1, 0))
    ax2.axis('off')
    ax2.set_title("Distribusi Jurusan per Tipe RIASEC", fontsize=12, fontweight='bold', loc='left', pad=10)
    
    dist_labels = ['Tipe RIASEC', 'Jumlah Jurusan', 'Persentase']
    
    riasec_names = {
        'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
        'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
    }
    
    dist_data = []
    total = results['TotalMajors']
    
    for code in ['R', 'I', 'A', 'S', 'E', 'C']:
        count = results['Distribution'].get(code, 0)
        percentage = (count / total) * 100 if total > 0 else 0
        label = f"{code} - {riasec_names[code]}"
        dist_data.append([label, count, f"{percentage:.1f}%"])
    
    table2 = ax2.table(cellText=dist_data, colLabels=dist_labels, loc='center', cellLoc='center')
    table2.scale(1, 2)
    table2.auto_set_font_size(False)
    table2.set_fontsize(11)
    
    for (row, col), cell in table2.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2C241B')
        else:
            cell.set_facecolor('#FAFAF8')

    plt.tight_layout()
    plt.savefig('tabel_perbandingan_model.png')
    print("\nTabel perbandingan telah disimpan sebagai 'tabel_perbandingan_model.png'")

if __name__ == "__main__":
    results = run_comparative_evaluation()
    
    create_comparison_visualization(results)
