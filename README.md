# Dokumentasi Teknis Sistem Rekomendasi Jurusan

Dokumen ini menjelaskan struktur kode dan logika backend yang digunakan dalam aplikasi JurusanFinder.

---

## 1. File Utama: `riasec_engine.py`

File ini adalah otak dari sistem yang menangani pemrosesan logika Forward Chaining dan integrasi dengan Large Language Model (LLM).

### Kelas & Fungsi Utama

#### `class Rule`

Objek sederhana untuk merepresentasikan aturan logika "IF-THEN".

- **Atribut**:
  - `condition`: Kode kondisi (misal: jawaban dari pertanyaan tertentu).
  - `action`: Poin skor yang diberikan ke kategori RIASEC tertentu (R/I/A/S/E/C) jika kondisi terpenuhi.

#### `class KnowledgeBase`

Bertugas mengelola data statis yang dimuat dari file CSV.

- **Fungsi Utama**:
  - `load_data()`: Memuat semua data penting saat aplikasi dijalankan.
  - `_load_questions()`: Membaca daftar pertanyaan dari `questions.csv`.
  - `_load_rules()`: Membaca aturan penilaian dari `rules.csv`.
  - `_load_majors()`: Membaca profil ideal setiap jurusan dari `jurusan.csv`.

#### `class ForwardChainingEngine`

Mesin inferensi yang menghitung skor profil siswa berdasarkan jawaban mereka.

- **`add_fact(fact)`**: Menerima input jawaban user (fakta baru).
- **`run()`**: Menjalankan algoritma Forward Chaining. Mencocokkan fakta user dengan `Rule` yang ada di Knowledge Base untuk menghitung skor RIASEC siswa.
- **`recommend_majors()`**:
  - Mengambil skor RIASEC siswa (hasil `run()`).
  - Membandingkannya dengan profil ideal setiap jurusan di Knowledge Base.
  - Menggunakan metode **Cosine Similarity (`_calculate_similarity`)** untuk menghitung tingkat kecocokan (0-10).
  - Mengurutkan jurusan dari skor tertinggi ke terendah.

#### `get_llm_recommendation(student_scores)`

Fungsi independen untuk mengakses kecerdasan buatan (Groq/LLM).

- **Input**: Skor RIASEC siswa (Dictionary).
- **Proses**:
  - Menyusun prompt engineer yang berisi profil siswa dan Knowledge Base jurusan.
  - Memberikan instruksi ketat ke LLM untuk menilai **semua jurusan** dengan presisi tinggi (2 desimal).
  - Meminta LLM untuk memberikan alasan (reasoning) kualitatif dalam Bahasa Indonesia hanya untuk top 3 rekomendasi.
- **Output**: JSON yang berisi skor match AI dan analisis tekstual.

---

## 2. Aplikasi Web: `app.py`

File ini menggunakan framework **Flask** untuk mengatur antarmuka pengguna (UI) dan alur aplikasi.

### Route (Jalur Aplikasi)

#### 1. Dashboard (`/`)

- **Fungsi**: `index()`
- **Tujuan**: Menampilkan halaman utama dashboard.
- **Proses**: Memuat Knowledge Base dan menghitung statistik distribusi kategori RIASEC pada jurusan yang tersedia untuk ditampilkan dalam grafik.

#### 2. Kuis (`/quiz`)

- **Fungsi**: `quiz()`
- **Tujuan**: Menampilkan halaman kuesioner.
- **Proses**: Mengelompokkan pertanyaan berdasarkan kategori (Realistic, Investigative, dll) agar tampilan di UI lebih terstruktur dan rapi.

#### 3. Proses Rekomendasi (`/rekomendasi` - POST)

- **Fungsi**: `rekomendasi()`
- **Tujuan**: Memproses jawaban kuis dan menampilkan hasil Forward Chaining.
- **Proses**:
  - Menerima input form dari user.
  - Menginstansiasi `ForwardChainingEngine` dan memberikan fakta-fakta jawaban user.
  - Menjalankan mesin (`engine.run()`) untuk dapat skor profil.
  - Menyimpan skor ke dalam **Session** (agar bisa dipakai oleh fitur AI nanti).
  - Merender halaman `result.html` dengan hasil perhitungan Cosine Similarity.

#### 4. Analisis AI (`/analyze_ai` - POST)

- **Fungsi**: `analyze_ai()`
- **Tujuan**: API Endpoint untuk memberikan opini kedua (Second Opinion) dari AI.
- **Proses**:
  - Dipanggil via AJAX (JavaScript) dari halaman hasil.
  - Mengambil skor siswa dari Session.
  - Memanggil fungsi `get_llm_recommendation()` dari `riasec_engine.py`.
  - Menggabungkan hasil analisis teks dari AI dengan data detail profil jurusan dari Knowledge Base.
  - Mengembalikan data JSON ke frontend untuk ditampilkan secara dinamis.

---

## Alur Data Singkat

1. User isi Kuis -> `app.py` terima data.
2. `app.py` panggil `riasec_engine.ForwardChainingEngine` -> Hitung skor RIASEC.
3. `engine` hitung Cosine Similarity -> Tampil hasil matematis (Forward Chaining).
4. (Opsional) User klik "Analisis AI" -> `app.py` panggil `riasec_engine.get_llm_recommendation` -> Tampil hasil analisis LLM.
