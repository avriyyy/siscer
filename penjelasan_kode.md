# PENERAPAN METODE FORWARD CHAINING PADA SISTEM PAKAR UNTUK REKOMENDASI JURUSAN BERDASARKAN MINAT DAN BAKAT SISWA

Dokumen ini menjelaskan implementasi kode sistem pakar rekomendasi jurusan yang dibangun menggunakan metode **Forward Chaining** dan algoritma pencocokan profil (_Profile Matching_) menggunakan _Cosine Similarity_.

## 1. Konsep Dasar Forward Chaining dalam Sistem

Metode **Forward Chaining** adalah teknik pencarian dalam sistem pakar yang dimulai dari sekumpulan fakta yang diketahui (data-driven), kemudian menerapkan aturan inferensi untuk mengekstrak lebih banyak data atau mencapai kesimpulan (goal).

Dalam sistem ini:

- **Fakta Awal:** Jawaban pengguna terhadap pertanyaan kuesioner (Minat & Bakat).
- **Aturan (Rules):** Basis pengetahuan yang memetakan setiap jawaban ke skor tipe kepribadian RIASEC (Realistic, Investigative, Artistic, Social, Enterprising, Conventional).
- **Inferensi:** Proses akumulasi skor berdasarkan jawaban yang dipilih untuk membentuk Profil Pengguna.
- **Kesimpulan (Goal):** Rekomendasi jurusan yang paling sesuai dengan profil yang terbentuk.

## 2. Struktur Basis Pengetahuan (Knowledge Base)

Sistem menggunakan dua basis data utama dalam format CSV:

### a. Aturan Penilaian (`rules.csv`)

File ini berisi aturan inferensi. Setiap opsi jawaban memiliki bobot tertentu terhadap 6 tipe kepribadian RIASEC.

_Contoh Data:_
| Code | R | I | A | S | E | C |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Q1A | 0 | 2 | 0 | 0 | 0 | 0 |

_Artinya:_ Jika pengguna memilih jawaban **Q1A**, maka sistem akan menambahkan skor **Investigative (I) +2**.

### b. Profil Jurusan (`jurusan.csv`)

File ini berisi profil ideal untuk setiap jurusan, yang menjadi target pencocokan.

_Contoh Data:_
| Jurusan | R | I | A | S | E | C |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| INFORMATIKA | 4 | 10 | 1 | 1 | 3 | 9 |

## 3. Implementasi Kode

Berikut adalah penjelasan fungsi-fungsi utama dalam `app.py` yang merepresentasikan logika sistem pakar.

### A. Mesin Inferensi (`inference_engine`)

Fungsi ini adalah inti dari proses **Forward Chaining**. Fungsi ini menerima fakta berupa jawaban pengguna (`answers`), kemudian menelusuri aturan (`rules`) untuk menghitung total skor profil pengguna.

```python
def inference_engine(answers):
    # 1. Memuat Basis Pengetahuan
    questions, rules, jurusan = load_knowledge_base()

    # Inisialisasi skor awal (Fakta kosong)
    skor = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}

    # 2. Proses Forward Chaining (Data-Driven)
    # Bergerak dari Fakta (Answer) -> Aturan -> Kesimpulan (Skor)
    for answer in answers:
        if answer in rules:
            # Menerapkan aturan: Tambahkan bobot ke tipe kepribadian terkait
            for riasec_type, points in rules[answer].items():
                skor[riasec_type] += points

    # ... (lanjutan logika pencocokan)
```

### B. Pencocokan Profil (`calculate_matching_score_v2`)

Setelah profil pengguna terbentuk (hasil dari forward chaining), sistem melakukan pencocokan dengan profil jurusan menggunakan metode **Cosine Similarity**. Metode ini mengukur kemiripan antara dua vektor (Vektor User vs Vektor Jurusan).

```python
def calculate_matching_score_v2(student_scores, major_profile):
    # Menghitung kemiripan sudut antara vektor profil siswa dan jurusan
    # Nilai mendekati 1 (atau 10 dalam skala 0-10) berarti sangat mirip

    dot_product = sum(student_norm[t] * major_norm[t] for t in types)
    # ...
    score = cosine_similarity * 10
    return round(score, 2)
```

### C. Penjelasan Hasil (`get_major_explanation`)

Fungsi ini memberikan penjelasan naratif mengapa sebuah jurusan direkomendasikan, berdasarkan dominasi tipe kepribadian yang cocok (misal: "Jurusan ini membutuhkan dominasi tipe Investigative dan Conventional").

## 4. Alur Kerja Sistem

1.  **Input:** Pengguna mengisi kuesioner di halaman `/quiz`.
2.  **Proses:**
    - Sistem menerima jawaban (Fakta).
    - `inference_engine` mencocokkan jawaban dengan `rules.csv` untuk menghitung skor RIASEC (Forward Chaining).
    - Sistem membandingkan skor pengguna dengan data di `jurusan.csv`.
3.  **Output:** Sistem menampilkan 3 jurusan dengan nilai kecocokan tertinggi beserta penjelasannya.
