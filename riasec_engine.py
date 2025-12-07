import os
import csv

class Rule:
    """
    Representasi Aturan Produksi (Production Rule).
    Format: IF (Condition) THEN (Action)
    
    Contoh:
    IF (Jawaban Q1 adalah Ya) THEN (Tambah Skor Realistic +2)
    """
    def __init__(self, condition, action):
        self.condition = condition  # Antecedent (Sebab): Kode Jawaban (misal: 'Q1Y')
        self.action = action        # Consequent (Akibat): Update Skor (misal: {'R': 2})

    def __repr__(self):
        return f"IF {self.condition} THEN {self.action}"

class KnowledgeBase:
    """
    Basis Pengetahuan (Knowledge Base) yang menyimpan:
    1. Daftar Pertanyaan (Facts gathering instruments)
    2. Aturan-aturan Logika (Rules)
    3. Data Jurusan (Domain Knowledge)
    
    Referensi: reference_riasec.pdf
    """
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
        """Memuat 30 pertanyaan dari questions.csv"""
        self.questions = []
        current_q = None
        path = os.path.join(self.base_dir, 'questions.csv')
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Grouping options under the same question ID
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
        """
        Memuat aturan dari rules.csv.
        Setiap baris di rules.csv merepresentasikan implikasi skor RIASEC.
        """
        self.rules = []
        path = os.path.join(self.base_dir, 'rules.csv')
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores = {}
                # Kolom R, I, A, S, E, C berisi poin yang akan ditambahkan
                for type_ in ['R', 'I', 'A', 'S', 'E', 'C']:
                    val = int(row[type_])
                    if val > 0:
                        scores[type_] = val
                
                # Membuat Rule baru
                # Condition: Kode Jawaban (misal Q1Y)
                # Action: Dictionary skor (misal {'R': 2})
                self.rules.append(Rule(row['code'], scores))

    def _load_majors(self):
        """Memuat profil jurusan dari jurusan.csv"""
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
    """
    Mesin Inferensi (Inference Engine) menggunakan metode Forward Chaining.
    
    Konsep:
    1. Start dengan sekumpulan Fakta (Jawaban User).
    2. Cari Aturan (Rules) yang premisnya cocok dengan Fakta.
    3. Eksekusi Aturan tersebut (Fire) untuk mendapatkan kesimpulan baru (Skor).
    4. Ulangi sampai semua aturan diperiksa.
    """
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.facts = set() # Himpunan fakta yang diketahui (misal: {'Q1Y', 'Q2N', ...})
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        self.execution_log = [] # Untuk keperluan penjelasan/presentasi

    def add_fact(self, fact):
        """Menambahkan fakta baru ke dalam working memory"""
        self.facts.add(fact)

    def run(self):
        """
        Menjalankan proses Forward Chaining.
        """
        # Reset state
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        self.execution_log = []
        
        self.execution_log.append("Mulai Inferensi Forward Chaining...")
        self.execution_log.append(f"Fakta Awal: {len(self.facts)} jawaban user.")

        # Iterasi melalui semua aturan dalam Knowledge Base
        # Dalam implementasi sederhana ini, kita cek semua rule (Data-Driven)
        for rule in self.kb.rules:
            # Matching: Apakah kondisi rule ada di fakta?
            if rule.condition in self.facts:
                # Firing: Jalankan aksi rule
                for category, points in rule.action.items():
                    self.scores[category] += points
                    self.execution_log.append(f"Rule MATCH: {rule.condition} -> Tambah {category} +{points}")
            else:
                # Rule tidak cocok
                pass
        
        self.execution_log.append("Inferensi Selesai.")
        self.execution_log.append(f"Skor Akhir: {self.scores}")
        
        return self.scores

    def recommend_majors(self):
        """
        Mencocokkan skor hasil inferensi dengan profil jurusan menggunakan Cosine Similarity.
        """
        results = []
        for major_name, major_profile in self.kb.majors.items():
            match_score = self._calculate_similarity(self.scores, major_profile)
            
            # Menentukan Kode RIASEC Jurusan (3 teratas)
            profile_items = [(k, v) for k, v in major_profile.items() if k in ['R','I','A','S','E','C']]
            sorted_profile = sorted(profile_items, key=lambda x: x[1], reverse=True)
            riasec_code = ''.join([p[0] for p in sorted_profile[:3]])
            
            # Generate Penjelasan
            explanation = self._generate_explanation(major_name, self.scores, riasec_code)

            results.append({
                'major': major_name,
                'riasec_code': riasec_code,
                'matching_score': match_score,
                'explanation': explanation,
                'profil_detail': major_profile
            })
        
        # Urutkan berdasarkan skor kecocokan tertinggi
        results.sort(key=lambda x: x['matching_score'], reverse=True)
        return results

    def _calculate_similarity(self, user_scores, major_profile):
        """Menghitung Cosine Similarity antara vektor skor user dan vektor jurusan"""
        types = ['R', 'I', 'A', 'S', 'E', 'C']
        
        user_vec = [user_scores[t] for t in types]
        major_vec = [major_profile[t] for t in types]
        
        dot_product = sum(u * m for u, m in zip(user_vec, major_vec))
        user_mag = sum(u**2 for u in user_vec) ** 0.5
        major_mag = sum(m**2 for m in major_vec) ** 0.5
        
        if user_mag == 0 or major_mag == 0:
            return 0
            
        similarity = dot_product / (user_mag * major_mag)
        return round(similarity * 10, 2) # Skala 0-10

    def _generate_explanation(self, major, user_scores, major_code):
        riasec_names = {
            'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
            'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
        }
        primary = major_code[0]
        secondary = major_code[1] if len(major_code) > 1 else ''
        
        return (f"Jurusan {major} memiliki profil dominan {riasec_names.get(primary, primary)} "
                f"dan {riasec_names.get(secondary, secondary)}. "
                f"Ini cocok dengan profilmu yang memiliki skor tinggi di kategori tersebut.")
