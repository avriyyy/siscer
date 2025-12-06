import csv
import os

def generate_dataset():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Load Questions to map ID to Category
    q_category_map = {}
    # Hardcoding the map based on the known structure to ensure order
    # Q1-Q5: Realistic
    # Q6-Q10: Investigative
    # Q11-Q15: Artistic
    # Q16-Q20: Social
    # Q21-Q25: Enterprising
    # Q26-Q30: Conventional
    
    # Or better, read from file
    with open(os.path.join(base_dir, 'questions.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map 'Realistic' -> 'R', etc.
            cat_full = row['kategori']
            cat_code = cat_full[0] # 'Realistic' -> 'R'
            q_category_map[row['id']] = cat_code

    # 2. Load Majors and generate answers
    output_rows = []
    header = ['Jurusan', 'Top_RIASEC'] + [f'Q{i}' for i in range(1, 31)]
    
    with open(os.path.join(base_dir, 'jurusan.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get scores
            scores = {
                'R': int(row['R']),
                'I': int(row['I']),
                'A': int(row['A']),
                'S': int(row['S']),
                'E': int(row['E']),
                'C': int(row['C'])
            }
            
            # Determine Top 2 RIASEC types
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            # Take top 2 for the "Ideal Answer" generation
            # (If someone is R and I, they answer Yes to R and I questions)
            top_2_codes = [x[0] for x in sorted_scores[:2]]
            top_riasec_str = "".join(top_2_codes)
            
            # Generate Q1-Q30 answers
            answers = []
            for i in range(1, 31):
                qid = f"Q{i}"
                cat = q_category_map.get(qid)
                
                # Logic: If the question category is in the major's Top 2 types, Answer Y. Else N.
                if cat in top_2_codes:
                    answers.append('Y')
                else:
                    answers.append('N')
            
            output_row = [row['nama_jurusan'], top_riasec_str] + answers
            output_rows.append(output_row)

    # 3. Write to dataset_jawaban.csv
    with open(os.path.join(base_dir, 'dataset_jawaban.csv'), 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(output_rows)
        
    print("Successfully updated dataset_jawaban.csv with 30 questions format.")

if __name__ == "__main__":
    generate_dataset()
