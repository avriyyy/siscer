import json
import csv
import os

class BackwardChainingEngine:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.script_dir)
        self.majors = {}
        self.rules = []
        self.questions = {}
        self.load_data()

    def load_data(self):
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

        with open(os.path.join(self.base_dir, 'rules.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                action = {}
                for t in ['R', 'I', 'A', 'S', 'E', 'C']:
                    if int(row[t]) > 0:
                        action[t] = int(row[t])
                
                if 'Y' in row['code']:
                    self.rules.append({
                        'condition': row['code'], 
                        'action': action          
                    })

        with open(os.path.join(self.base_dir, 'questions.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] not in self.questions:
                    self.questions[row['id']] = row['teks']

    def generate_answer_keys(self):
        answer_keys = {}

        for major_name, profile in self.majors.items():
            target_scores = profile['scores']
            required_answers = {}
            
            current_scores = {k: 0 for k in target_scores}
            
            sorted_targets = sorted(target_scores.items(), key=lambda x: x[1], reverse=True)
            
            for category, target_val in sorted_targets:
                if target_val == 0:
                    continue
                    
                potential_rules = [r for r in self.rules if category in r['action']]
                
                for rule in potential_rules:
                    if current_scores[category] >= target_val:
                        break
                        
                    qid = rule['condition'][:-1] 
                    
                    if qid not in required_answers:
                        required_answers[qid] = "Ya"
                        
                        for cat, points in rule['action'].items():
                            current_scores[cat] += points
            
            full_answers = {}
            for qid in self.questions:
                full_answers[qid] = required_answers.get(qid, "Tidak")

            sorted_profile = sorted(target_scores.items(), key=lambda x: x[1], reverse=True)
            riasec_code = ''.join([p[0] for p in sorted_profile[:3]])

            answer_keys[major_name] = {
                "riasec_code": riasec_code,
                "target_scores": target_scores,
                "achieved_scores": current_scores,
                "key_answers": required_answers 
            }
            
        return answer_keys

    def save_to_csv(self, data, filename='answer_keys.csv'):
        headers = ['Jurusan', 'RIASEC_Code', 'R', 'I', 'A', 'S', 'E', 'C']
        q_ids = sorted(self.questions.keys(), key=lambda x: int(x[1:])) 
        headers.extend(q_ids)

        # Save to the same directory as this script (Evaluasi folder)
        output_path = os.path.join(self.script_dir, filename)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
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
                
                for qid in q_ids:
                    answer = details['key_answers'].get(qid, 'Tidak')
                    row.append(answer)
                
                writer.writerow(row)
        print(f"Kunci jawaban berhasil disimpan ke {output_path}")

if __name__ == "__main__":
    engine = BackwardChainingEngine()
    keys = engine.generate_answer_keys()
    engine.save_to_csv(keys)
