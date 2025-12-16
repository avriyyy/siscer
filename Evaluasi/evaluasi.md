# Dokumentasi Folder Evaluasi

Folder ini berisi kumpulan skrip untuk menguji, memvalidasi, dan membandingkan kinerja sistem pakar (Forward Chaining) dengan model LLM.

## 1. Pembuatan Data Uji & Validasi Logika

### `backward_chaining.py`

**Tujuan:** Membuat "Kunci Jawaban" (_Ground Truth_).
**Fungsi:**

- Bekerja mundur dari profil ideal jurusan.
- Menentukan kombinasi jawaban "Ya" apa saja yang diperlukan untuk mendapatkan skor maksimal di jurusan tertentu.
- **Output:** `answer_keys.csv` (Berisi daftar jurusan target dan jawaban kuesioner yang seharusnya menghasilkan jurusan tersebut).

### `validate_keys.py`

**Tujuan:** Memastikan logika Forward Chaining berfungsi 100% benar.
**Fungsi:**

- Membaca `answer_keys.csv`.
- Menjalankan mesin Forward Chaining (`riasec_engine.py`) menggunakan input jawaban dari file tersebut.
- Memverifikasi apakah output sistem sesuai dengan target jurusan.
- **Output:** `validation_output.txt` (Log hasil validasi: PASS/FAIL).

---

## 2. Pengujian & Perbandingan Model (FC vs LLM)

### `testing_model.py`

**Tujuan:** Mengukur performa teknis (Akurasi & Latency).
**Fungsi:**

- Menjalankan serangkaian tes kasus (synthetic test cases).
- Membandingkan hasil rekomendasi antara **Forward Chaining** vs **LLM**.
- Mengukur waktu eksekusi (seberapa cepat sistem merespons).
- Mengecek akurasi (apakah LLM merekomendasikan jurusan yang sesuai dengan tipe RIASEC dominan).
- **Output:** Grafik `perbandingan_model.png`.

### `skor_model.py`

**Tujuan:** Visualisasi detail distribusi skor.
**Fungsi:**

- Menggunakan satu profil siswa (dummy) yang spesifik.
- Menghitung skor kecocokan untuk **SEMUA jurusan** menggunakan kedua metode.
- Menampilkan grafik batang (bar chart) yang menyandingkan skor FC vs skor LLM untuk melihat pola distribusi dan konsistensi penilaian.
- **Output:** Grafik `perbandingan_skor.png`.

---

## 3. File Output (Artifacts)

- **`answer_keys.csv`**: Dataset pengujian yang dihasilkan oleh backward chaining.
- **`validation_output.txt`**: Laporan teks hasil validasi logika.
- **`perbandingan_model.png`**: Grafik perbandingan Latency dan Akurasi.
- **`perbandingan_skor.png`**: Grafik perbandingan skor kecocokan per jurusan.
