import json
import csv
import os

class BackwardChainingEngine:
    """
    Mesin Backward Chaining untuk menelusuri fakta (jawaban) yang dibutuhkan
    untuk mencapai tujuan (Profil Jurusan).
    
    Goal: Jurusan Tertentu (misal: TEKNIK SIPIL)
    Sub-Goal: Skor RIASEC tertentu (misal: R >= 6, I >= 3)
    Action: Temukan pertanyaan yang harus dijawab 'Ya' untuk memenuhi skor tersebut.
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.majors = {}
        self.rules = []
        self.questions = {}
        self.load_data()

    def load_data(self):
        # 1. Load Jurusan (Goals)
        with open(os.path.join(self.base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.majors[row['nama_jurusan']] = {
                    'scores': {
                        'R': int(row['R']), 'I': int(row['I']), 'A': int(row['A']),
                        'S': int(row['S']), 'E': int(row['E']), 'C': int(row['C'])
                    },
                    'fakultas': row['fakultas']
                }

        # 2. Load Rules (Knowledge)
        # Format: Q1Y -> {'R': 2}
        with open(os.path.join(self.base_dir, 'rules.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                action = {}
                for t in ['R', 'I', 'A', 'S', 'E', 'C']:
                    if int(row[t]) > 0:
                        action[t] = int(row[t])
                
                # Hanya simpan rule yang memberikan poin (Jawaban Y)
                if 'Y' in row['code']:
                    self.rules.append({
                        'condition': row['code'], # e.g., Q1Y
                        'action': action          # e.g., {'R': 2}
                    })

        # 3. Load Questions (For readability)
        with open(os.path.join(self.base_dir, 'questions.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map ID to Text (Only need one entry per ID)
                if row['id'] not in self.questions:
                    self.questions[row['id']] = row['teks']

    def generate_answer_keys(self):
        """
        Menghasilkan kunci jawaban untuk setiap jurusan.
        """
        answer_keys = {}

        for major_name, profile in self.majors.items():
            target_scores = profile['scores']
            required_answers = {}
            
            # Strategi Backward Chaining:
            # Untuk setiap kategori (R, I, A...), cari rule yang bisa memenuhi skor target.
            
            current_scores = {k: 0 for k in target_scores}
            
            # Urutkan kategori berdasarkan skor target tertinggi (Prioritas)
            sorted_targets = sorted(target_scores.items(), key=lambda x: x[1], reverse=True)
            
            for category, target_val in sorted_targets:
                if target_val == 0:
                    continue
                    
                # Cari rule yang berkontribusi ke kategori ini
                # Filter rules that give points to 'category'
                potential_rules = [r for r in self.rules if category in r['action']]
                
                for rule in potential_rules:
                    # Cek apakah kita masih butuh poin untuk kategori ini
                    if current_scores[category] >= target_val:
                        break
                        
                    # Ambil ID Pertanyaan dari Condition (misal Q1Y -> Q1)
                    qid = rule['condition'][:-1] 
                    
                    # Jika pertanyaan belum dijawab, jawab 'Ya'
                    if qid not in required_answers:
                        required_answers[qid] = "Ya"
                        
                        # Update skor (Simulasi Rule Firing)
                        for cat, points in rule['action'].items():
                            current_scores[cat] += points
            
            # Isi sisa pertanyaan dengan 'Tidak' (Default)
            full_answers = {}
            for qid in self.questions:
                full_answers[qid] = required_answers.get(qid, "Tidak")

            # Determine RIASEC Code
            sorted_profile = sorted(target_scores.items(), key=lambda x: x[1], reverse=True)
            riasec_code = ''.join([p[0] for p in sorted_profile[:3]])

            answer_keys[major_name] = {
                "riasec_code": riasec_code,
                "target_scores": target_scores,
                "achieved_scores": current_scores,
                "key_answers": required_answers # Hanya jawaban 'Ya' yang krusial
            }
            
        return answer_keys

    def save_to_json(self, data, filename='answer_keys.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Kunci jawaban berhasil disimpan ke {filename}")

    def save_to_csv(self, data, filename='answer_keys.csv'):
        # Prepare headers
        headers = ['Jurusan', 'RIASEC_Code', 'R', 'I', 'A', 'S', 'E', 'C']
        # Add Q1 to Q30
        q_ids = sorted(self.questions.keys(), key=lambda x: int(x[1:])) # Sort Q1, Q2, ...
        headers.extend(q_ids)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for major, details in data.items():
                row = [
                    major,
                    details['riasec_code'],
                    details['achieved_scores']['R'],
                    details['achieved_scores']['I'],
                    details['achieved_scores']['A'],
                    details['achieved_scores']['S'],
                    details['achieved_scores']['E'],
                    details['achieved_scores']['C']
                ]
                
                # Add answers for Q1-Q30
                for qid in q_ids:
                    # Default to 'Tidak' if not in key_answers, but key_answers only stores 'Ya' usually
                    # The logic in generate_answer_keys puts 'Ya' in required_answers.
                    # We can check details['key_answers']
                    answer = details['key_answers'].get(qid, 'Tidak')
                    row.append(answer)
                
                writer.writerow(row)
        print(f"Kunci jawaban berhasil disimpan ke {filename}")

if __name__ == "__main__":
    engine = BackwardChainingEngine()
    keys = engine.generate_answer_keys()
    engine.save_to_json(keys)
    engine.save_to_csv(keys)
