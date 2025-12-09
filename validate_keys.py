import csv
import os
from riasec_engine import KnowledgeBase, ForwardChainingEngine

def validate_answer_keys():
    print("\n--- VALIDASI KUNCI JAWABAN (BACKWARD vs FORWARD CHAINING) ---\n")
    
    kb = KnowledgeBase()
    engine = ForwardChainingEngine(kb)
    
    keys_path = 'answer_keys.csv'
    if not os.path.exists(keys_path):
        print(f"Error: {keys_path} not found.")
        return

    success_count = 0
    total_count = 0
    
    with open('validation_output.txt', 'w', encoding='utf-8') as f:
        f.write("\n--- VALIDASI KUNCI JAWABAN (BACKWARD vs FORWARD CHAINING) ---\n\n")
        f.write(f"{'TARGET JURUSAN':<25} | {'TOP REKOMENDASI':<25} | {'SKOR MATCH':<10} | {'STATUS'}\n")
        f.write("-" * 80 + "\n")

        with open(keys_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_count += 1
                target_major = row['Jurusan']
                
                engine.facts = set()
                for i in range(1, 31):
                    qid = f"Q{i}"
                    answer = row.get(qid)
                    if answer == 'Ya':
                        engine.add_fact(f"{qid}Y")
                
                engine.run()
                recommendations = engine.recommend_majors()
                
                if not recommendations:
                    f.write(f"{target_major:<25} | {'No Recs':<25} | {'0':<10} | ❌ ERROR\n")
                    continue
                    
                top_rec = recommendations[0]
                top_major_name = top_rec['major']
                match_score = top_rec['matching_score']
                
                if top_major_name == target_major:
                    status = "✅ PASS"
                    success_count += 1
                else:
                    top_3_names = [r['major'] for r in recommendations[:3]]
                    if target_major in top_3_names:
                         status = f"⚠️ TOP 3 (Rank {top_3_names.index(target_major) + 1})"
                    else:
                        status = f"❌ FAIL (Got {top_major_name})"

                f.write(f"{target_major:<25} | {top_major_name:<25} | {match_score:<10} | {status}\n")

        f.write("-" * 80 + "\n")
        f.write(f"Total Validasi: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)\n")
        
        if success_count == total_count:
            f.write("\nKESIMPULAN: Sistem Forward Chaining 100% KONSISTEN dengan Kunci Jawaban.\n")
        else:
            f.write("\nKESIMPULAN: Terdapat beberapa ketidakcocokan. Cek logika rule atau threshold similarity.\n")
            
    print("Validation results saved to validation_output.txt")

if __name__ == "__main__":
    validate_answer_keys()
