# Penjelasan Kode Forward Chaining (Sistem Pakar)

Kode implementasi Forward Chaining terdapat di dalam file `app.py`, khususnya pada class `ForwardChainingEngine`. Berikut adalah bedah kodenya:

## 1. Class `ForwardChainingEngine`

Ini adalah "otak" dari sistem pakar. Class ini bertugas menerima fakta (jawaban user) dan memprosesnya berdasarkan aturan (rules) untuk menghasilkan kesimpulan (skor RIASEC).

```python
class ForwardChainingEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.facts = set()  # Menyimpan fakta-fakta (jawaban "Ya")
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
```

## 2. Metode `run()` - Inti Forward Chaining

Ini adalah algoritma utama Forward Chaining. Disebut "Forward" karena bergerak maju dari **Data (Fakta)** menuju **Kesimpulan (Skor)**.

```python
    def run(self):
        # 1. Reset skor ke 0 sebelum memulai
        self.scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}

        # 2. Iterasi (Looping) melalui semua ATURAN yang ada di Knowledge Base
        for rule in self.kb.rules:
            # 3. Pengecekan Kondisi (IF)
            # Apakah kondisi aturan ini (misal: "Q1Y") ada di dalam fakta user?
            if rule.condition in self.facts:

                # 4. Eksekusi Aksi (THEN) -> Rule Fired!
                # Jika kondisi terpenuhi, tambahkan poin ke kategori yang sesuai
                for category, points in rule.action.items():
                    self.scores[category] += points

        return self.scores
```

**Analogi:** Bayangkan saklar lampu. Jika saklar ditekan (Fakta), maka lampu menyala (Aksi). Kode ini mengecek semua saklar yang ditekan user.

## 3. Metode `recommend_majors()` - Pencocokan Pola

Setelah skor RIASEC didapatkan dari proses `run()`, sistem mencari jurusan yang paling cocok.

```python
    def recommend_majors(self):
        results = []
        # Loop semua jurusan di database
        for major_name, major_profile in self.kb.majors.items():
            # Hitung kemiripan antara profil user (self.scores) dengan profil jurusan
            match_score = self._calculate_similarity(self.scores, major_profile)

            # ... (kode formatting hasil) ...

            results.append({ ... })

        # Urutkan hasil dari skor tertinggi ke terendah
        results.sort(key=lambda x: x['matching_score'], reverse=True)
        return results
```

## 4. Metode `_calculate_similarity()` - Cosine Similarity

Sistem menggunakan rumus matematika **Cosine Similarity** untuk menghitung seberapa mirip profil user dengan profil jurusan.

```python
    def _calculate_similarity(self, user_scores, major_profile):
        types = ['R', 'I', 'A', 'S', 'E', 'C']

        # Buat vektor user dan vektor jurusan
        user_vec = [user_scores[t] for t in types]
        major_vec = [major_profile[t] for t in types]

        # Rumus Cosine Similarity: (A . B) / (||A|| * ||B||)
        dot_product = sum(u * m for u, m in zip(user_vec, major_vec))
        user_mag = sum(u**2 for u in user_vec) ** 0.5
        major_mag = sum(m**2 for m in major_vec) ** 0.5

        if user_mag == 0 or major_mag == 0:
            return 0

        # Normalisasi hasil ke skala 0-100% (atau 0-10)
        return (dot_product / (user_mag * major_mag)) * 10
```

**Kenapa Cosine Similarity?**
Metode ini melihat "arah" minat, bukan hanya besaran angkanya. Jadi, jika pola minat user (misal: Tinggi di R dan I) mirip dengan pola jurusan (Tinggi di R dan I), maka skornya akan tinggi, meskipun nilai absolutnya berbeda.
