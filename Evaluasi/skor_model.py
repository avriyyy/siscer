import matplotlib.pyplot as plt
import numpy as np
import json
import os
import difflib
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from riasec_engine import KnowledgeBase, ForwardChainingEngine, get_llm_recommendation

load_dotenv()

def main():
    kb = KnowledgeBase()
    engine = ForwardChainingEngine(kb)
    
    test_student_scores = {'R': 8, 'I': 8, 'A': 2, 'S': 2, 'E': 4, 'C': 8}
    print(f"Menggunakan skor profil: {test_student_scores}")
    
    majors_names = list(kb.majors.keys())
    
    fc_scores = {}
    print("Menghitung skor Forward Chaining...")
    for major in majors_names:
        profile = kb.majors[major]
        score = engine._calculate_similarity(test_student_scores, profile)
        fc_scores[major] = score

    print("Meminta rekomendasi dari LLM (via riasec_engine)...")
    llm_result = get_llm_recommendation(test_student_scores)
    
    llm_scores_map = {}
    if llm_result:
        if 'all_matches' in llm_result:
             llm_scores_map = llm_result['all_matches']
        elif 'recommendations' in llm_result:
            for rec in llm_result['recommendations']:
                llm_scores_map[rec['major']] = rec.get('match_score', 0)

    print(f"DEBUG: LLM Scores Map Size: {len(llm_scores_map)}")
    
    llm_scores = []
    fc_scores_list = []
    
    for major in majors_names:
        fc_scores_list.append(fc_scores.get(major, 0))
        
        val = llm_scores_map.get(major, 0)
        
        if val == 0:
             for k, v in llm_scores_map.items():
                 if major.lower() in k.lower() or k.lower() in major.lower():
                     val = v
                     break
                 if difflib.SequenceMatcher(None, major.lower(), k.lower()).ratio() > 0.8:
                     val = v
                     break
        llm_scores.append(val)

    x = np.arange(len(majors_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(15, 8))
    rects1 = ax.bar(x - width/2, fc_scores_list, width, label='Forward Chaining + Cosine Similarity', color='#2C241B')
    rects2 = ax.bar(x + width/2, llm_scores, width, label='LLM (llama-3.3-70b-versatile)', color='#4285F4')
    
    ax.set_ylabel('Match Score (0-10)')
    ax.set_title('Perbandingan Skor Kecocokan Jurusan (FC + Cosine Similarity vs LLM)')
    ax.set_xticks(x)
    ax.set_xticklabels(majors_names, rotation=45, ha='right')
    ax.legend()
    
    ax.set_ylim(0, 11)
    
    plt.tight_layout()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'perbandingan_skor.png')
    plt.savefig(output_path)
    print(f"\nGrafik telah disimpan sebagai '{output_path}'")
    print("\nGrafik telah disimpan sebagai 'perbandingan_skor.png'")

if __name__ == "__main__":
    main()
