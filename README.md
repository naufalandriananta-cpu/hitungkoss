# 🏘️ HitungKos — Sistem Estimasi Tarif Sewa Kos di Madiun
* **Naufal Adriananta Halim** — NIM `253307058`

Platform web cerdas yang dikembangkan menggunakan framework **Django** serta integrasi **Machine Learning** guna membantu pengguna memperkirakan biaya sewa kamar kos per bulan di area **Madiun** berdasarkan kelengkapan fasilitas, dimensi ruangan, dan letak geografis.

---

## 🌟 Fitur Unggulan

* **Estimasi Harga Otomatis:** Menghitung perkiraan tarif sewa bulanan secara cepat dengan memanfaatkan algoritma regresi Scikit-learn (*Linear Regression* & *Decision Tree Regressor*) berbasis data lokal (`kos_madiun.csv`).
* **Grafik & Analisis Data:** Menyajikan visualisasi interaktif mengenai tren harga sewa serta pengaruh berbagai fasilitas terhadap besaran biaya bulanan.
* **Analisis Penjelasan AI:** Memberikan ulasan otomatis mengenai tingkat kewajaran harga hasil prediksi melalui koneksi API **Gemini** maupun **Groq** (dilengkapi sistem cadangan lokal).
* **Log Riwayat Perhitungan:** Menyimpan setiap aktivitas kalkulasi pengguna secara otomatis ke dalam basis data SQLite lewat tabel `RiwayatPrediksi`.
* **Tampilan Responsif & Elegan:** Mengusung konsep antarmuka *Powder Blue Elegant* yang nyaman diakses dari berbagai ukuran layar.

---

## 📁 Susunan Direktori

```text
HitungKos/
├── hitungkos_project/     # Pengaturan inti aplikasi Django (settings, urls, wsgi)
├── prediksi/              # Modul utama (views, models, forms, proses ML & integrasi AI)
├── static/images/         # Kumpulan aset visual statis
├── templates/             # Berkas antarmuka pengguna (HTML)
├── db.sqlite3             # Penyimpanan database lokal SQLite
├── kos_madiun.csv         # Data latih spesifikasi dan tarif kos wilayah Madiun
├── manage.py              # Utilitas baris perintah (CLI) Django
├── model_kos.joblib       # File model Machine Learning siap pakai
└── train_model.py         # Kode sumber untuk pelatihan dan pengujian akurasi model
```

---

## ⚙️ Tech Stack

* **Framework Backend:** Python, Django
* **Pemodelan Data & ML:** Scikit-learn, Pandas, Joblib
* **Layanan Kecerdasan Buatan:** Google Gemini API, Groq API
* **Antarmuka Pengguna:** HTML5, CSS3, JavaScript
* **Sistem Basis Data:** SQLite3

---

## 💻 Panduan Instalasi & Menjalankan Aplikasi

### 1. Unduh Source Code
```bash
git clone <url-repository-anda>
cd HitungKos
```

### 2. Siapkan Virtual Environment
* **Pengguna Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
* **Pengguna macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Pasang Paket Dependensi
```bash
pip install django scikit-learn pandas joblib python-dotenv google-genai groq
```

### 4. Atur Environment Variable (Opsional untuk Fitur Penjelasan AI)
Buat berkas baru bernama `.env` di direktori utama (satu level dengan `manage.py`), kemudian tambahkan kunci API berikut:
```env
GEMINI_API_KEY=isi_dengan_api_key_gemini_anda
GROQ_API_KEY=isi_dengan_api_key_groq_anda
```

### 5. Proses Pelatihan Ulang Model (Opsional)
Berkas model `model_kos.joblib` sudah disertakan di dalam proyek. Apabila ingin memperbarui model dari dataset `kos_madiun.csv`, jalankan perintah:
```bash
python train_model.py
```

### 6. Inisialisasi Database & Jalankan Server Lokal
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Setelah server aktif, silakan buka peramban (browser) dan kunjungi alamat **`[http://127.0.0.1:8000/](https://hitunggkos.vercel.app/)`**.

---


