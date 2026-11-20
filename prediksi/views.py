import json
import os
import urllib.error
import urllib.request
import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import redirect, render
from .models import RiwayatPrediksi

# Memuat paket model dan dataset referensi sekali saat server Django dijalankan
MODEL_PATH = os.path.join(settings.BASE_DIR, "model_kos.joblib")
CSV_PATH = os.path.join(settings.BASE_DIR, "kos_madiun.csv")
PAKET_MODEL = joblib.load(MODEL_PATH)
DF_DATASET = pd.read_csv(CSV_PATH)


def format_rupiah(nominal):
    """Mengubah angka nominal menjadi format Rupiah bertitik (contoh: Rp 1.057.000)."""
    return f"Rp {int(round(nominal)):,}".replace(",", ".")


def analisis_ai_lokal(jarak_val, ac_raw, rating_val, prediksi_rupiah, rata_pasar_rupiah, kategori):
    """Engine analisis lokal bawaan untuk menjelaskan kewajaran harga kos tanpa API key."""
    selisih = prediksi_rupiah - rata_pasar_rupiah
    persen = abs(selisih) / rata_pasar_rupiah * 100

    if selisih > 30000:
        posisi = f"lebih tinggi sekitar {format_rupiah(abs(selisih))} ({persen:.1f}%) dari rata-rata pasar kos Madiun ({format_rupiah(rata_pasar_rupiah)}/bulan)"
    elif selisih < -30000:
        posisi = f"lebih hemat sekitar {format_rupiah(abs(selisih))} ({persen:.1f}%) dibandingkan rata-rata pasar kos Madiun ({format_rupiah(rata_pasar_rupiah)}/bulan)"
    else:
        posisi = f"sangat mendekati rata-rata tarif standar pasar kos Madiun ({format_rupiah(rata_pasar_rupiah)}/bulan)"

    if jarak_val <= 1.5:
        catatan_jarak = f"Jarak {jarak_val} km tergolong sangat dekat dengan area kampus sehingga menghemat biaya serta waktu transportasi harian."
    elif jarak_val <= 3.5:
        catatan_jarak = f"Jarak {jarak_val} km berada pada radius menengah sekitar kampus yang masih nyaman ditempuh kendaraan bermotor."
    elif jarak_val <= 5.0:
        catatan_jarak = f"Jarak {jarak_val} km berada di batas luar area survei kampus sehingga tarif sewanya cenderung lebih rendah."
    else:
        catatan_jarak = f"Catatan: Jarak {jarak_val} km berada di luar rentang data latih utama (0,6–5,0 km), sehingga angka ini merupakan hasil ekstrapolasi linear."

    catatan_fasilitas = (
        f"Fasilitas AC dan rating {rating_val}/5,0 memberikan nilai tambah kenyamanan kamar."
        if ac_raw == "ya"
        else f"Tipe kamar Non-AC dengan rating {rating_val}/5,0 menjadi pilihan ekonomis untuk menekan biaya bulanan."
    )

    return (
        f"Estimasi tarif {format_rupiah(prediksi_rupiah)}/bulan (Segmen {kategori}) ini {posisi}. "
        f"{catatan_jarak} {catatan_fasilitas}"
    )


def panggil_api_ai(provider, api_key, prompt_teks):
    """Memanggil API Groq atau Google Gemini dengan header User-Agent agar tidak diblokir WAF/Cloudflare."""
    headers_umum = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HitungKos/2.0",
    }

    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = json.dumps({
            "model": "openai/gpt-oss-20b",
            "messages": [
                {
                    "role": "system",
                    "content": "Kamu adalah asisten konsultan properti kos mahasiswa di Madiun. Berikan analisis singkat, objektif, dan praktis dalam 2-3 kalimat bahasa Indonesia.",
                },
                {"role": "user", "content": prompt_teks},
            ],
            "temperature": 0.4,
            "max_completion_tokens": 220,
        }).encode("utf-8")

        headers_groq = dict(headers_umum)
        headers_groq["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, data=payload, headers=headers_groq, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()

    elif provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt_teks}]}],
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers_umum, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    return None


def index(request):
    model_ml = PAKET_MODEL["model"]
    rata_pasar_rupiah = float(PAKET_MODEL["rata_harga"]) * 1000
    tarif_min_rupiah = float(DF_DATASET["harga"].min()) * 1000
    tarif_max_rupiah = float(DF_DATASET["harga"].max()) * 1000

    # Pengaturan provider AI dari session browser pengguna
    ai_provider = request.session.get("ai_provider", "lokal")
    ai_api_key = request.session.get("ai_api_key", "")
    pesan_ai_setting = None

    info_model = {
        "nama_model": PAKET_MODEL["nama_model"],
        "metrik": PAKET_MODEL["metrik"],
        "perbandingan": PAKET_MODEL["perbandingan"],
        "jumlah_data": PAKET_MODEL["jumlah_data"],
        "rata_harga_rupiah": format_rupiah(rata_pasar_rupiah),
        "tarif_min_rupiah": format_rupiah(tarif_min_rupiah),
        "tarif_max_rupiah": format_rupiah(tarif_max_rupiah),
    }

    form_data = {
        "jarak_km": "1.5",
        "ac": "ya",
        "rating": "4.2",
    }

    hasil_prediksi = None
    pesan_error = None

    if request.method == "POST":
        aksi = request.POST.get("aksi", "hitung")

        # 1. Simpan pengaturan API AI (Groq / Gemini / Lokal) ke session
        if aksi == "simpan_ai":
            provider_baru = request.POST.get("ai_provider", "lokal").strip().lower()
            key_baru = request.POST.get("ai_api_key", "").strip()

            if provider_baru in ("lokal", "groq", "gemini"):
                request.session["ai_provider"] = provider_baru
                ai_provider = provider_baru

                if provider_baru == "lokal":
                    request.session["ai_api_key"] = ""
                    ai_api_key = ""
                    pesan_ai_setting = "Mode Analisis Lokal Bawaan diaktifkan."
                elif key_baru:
                    request.session["ai_api_key"] = key_baru
                    ai_api_key = key_baru
                    pesan_ai_setting = f"Provider {provider_baru.upper()} dan API Key berhasil disimpan ke session."
                elif ai_api_key:
                    pesan_ai_setting = f"Provider {provider_baru.upper()} aktif menggunakan API Key yang sudah tersimpan."
                else:
                    pesan_ai_setting = f"Provider {provider_baru.upper()} dipilih, tetapi API Key belum diisi (akan memakai Analisis Lokal sampai key diisi)."

        # 2. Hapus seluruh riwayat pencarian
        elif aksi == "hapus_riwayat":
            RiwayatPrediksi.objects.all().delete()
            return redirect("/#riwayat")

        # 3. Jalankan kalkulasi prediksi harga kos + analisis AI
        elif aksi == "hitung":
            jarak_raw = request.POST.get("jarak_km", "").strip()
            ac_raw = request.POST.get("ac", "").strip().lower()
            rating_raw = request.POST.get("rating", "").strip()

            form_data = {
                "jarak_km": jarak_raw,
                "ac": ac_raw,
                "rating": rating_raw,
            }

            try:
                jarak_val = float(jarak_raw)
                rating_val = float(rating_raw)

                if jarak_val < 0.1 or jarak_val > 25.0:
                    pesan_error = "Jarak kos harus berada di antara 0,1 km hingga 25,0 km."
                elif rating_val < 1.0 or rating_val > 5.0:
                    pesan_error = "Rating kos harus berada pada skala 1,0 hingga 5,0."
                elif ac_raw not in ("ya", "tidak"):
                    pesan_error = "Pilihan fasilitas AC tidak valid. Pilih Ya atau Tidak."
                else:
                    ac_num = 1 if ac_raw == "ya" else 0
                    data_baru = pd.DataFrame({
                        "jarak_km": [jarak_val],
                        "rating": [rating_val],
                        "ac_num": [ac_num],
                    })

                    prediksi_ribu = float(model_ml.predict(data_baru)[0])
                    if prediksi_ribu < 0:
                        prediksi_ribu = 0.0

                    prediksi_rupiah = prediksi_ribu * 1000

                    # Klasifikasi segmen harga berdasarkan rata-rata pasar kos Madiun
                    if prediksi_ribu < 1000:
                        kategori = "Terjangkau"
                    elif prediksi_ribu <= 1100:
                        kategori = "Menengah"
                    else:
                        kategori = "Premium"

                    # Susun ulasan AI (Lokal Bawaan / Groq / Gemini)
                    ulasan_lokal = analisis_ai_lokal(
                        jarak_val, ac_raw, rating_val, prediksi_rupiah, rata_pasar_rupiah, kategori
                    )
                    label_provider = "Analisis Lokal Bawaan"
                    ulasan_ai = ulasan_lokal

                    if ai_provider in ("groq", "gemini"):
                        if not ai_api_key:
                            label_provider = f"Analisis Lokal ({ai_provider.upper()} Key Kosong)"
                        else:
                            prompt_ai = (
                                f"Analisis kewajaran harga sewa kos mahasiswa di Madiun berikut dalam 3 kalimat singkat bahasa Indonesia:\n"
                                f"- Jarak ke kampus: {jarak_val} km\n"
                                f"- Fasilitas AC: {'Ya (Ber-AC)' if ac_raw == 'ya' else 'Tidak (Non-AC)'}\n"
                                f"- Rating kos: {rating_val}/5.0\n"
                                f"- Hasil estimasi model: {format_rupiah(prediksi_rupiah)}/bulan (Segmen {kategori})\n"
                                f"- Rata-rata harga pasar dataset Madiun: {format_rupiah(rata_pasar_rupiah)}/bulan (rentang {format_rupiah(tarif_min_rupiah)} - {format_rupiah(tarif_max_rupiah)})."
                            )
                            try:
                                respons_eksternal = panggil_api_ai(ai_provider, ai_api_key, prompt_ai)
                                if respons_eksternal:
                                    ulasan_ai = respons_eksternal
                                    label_provider = "Groq AI (GPT OSS 20B)" if ai_provider == "groq" else "Google Gemini AI"
                            except urllib.error.HTTPError as err:
                                label_provider = f"Analisis Lokal (HTTP {err.code} {ai_provider.upper()})"
                                ulasan_ai = ulasan_lokal
                            except Exception:
                                label_provider = f"Analisis Lokal (Koneksi {ai_provider.upper()} Gagal)"
                                ulasan_ai = ulasan_lokal

                    # Simpan riwayat pencarian ke database SQLite
                    RiwayatPrediksi.objects.create(
                        jarak_km=jarak_val,
                        ac=ac_raw,
                        rating=rating_val,
                        estimasi_harga=round(prediksi_rupiah, 0),
                        kategori=kategori,
                        provider_ai=label_provider,
                        analisis_ai=ulasan_ai,
                    )

                    hasil_prediksi = {
                        "harga_ribu": round(prediksi_ribu, 1),
                        "harga_rupiah": format_rupiah(prediksi_rupiah),
                        "kategori": kategori,
                        "jarak_km": jarak_val,
                        "ac_teks": "Ya (Ber-AC)" if ac_raw == "ya" else "Tidak (Non-AC)",
                        "rating": rating_val,
                        "provider_ai": label_provider,
                        "analisis_ai": ulasan_ai,
                    }

            except ValueError:
                pesan_error = "Pastikan jarak dan rating diisi dengan format angka yang valid (contoh: 1.5 atau 4.2)."

    # Data untuk grafik interaktif Chart.js & tabel referensi 30 data kos Madiun
    dataset_list = []
    for idx, row in DF_DATASET.iterrows():
        dataset_list.append({
            "no": idx + 1,
            "nama": row.get("nama", f"Kos #{idx + 1}"),
            "jarak_km": float(row["jarak_km"]),
            "rating": float(row["rating"]),
            "ac": str(row["ac"]).strip().lower(),
            "harga_ribu": float(row["harga"]),
            "harga_rupiah": format_rupiah(float(row["harga"]) * 1000),
        })

    rata_ac = DF_DATASET.groupby("ac")["harga"].mean().to_dict()
    chart_payload = json.dumps({
        "points": dataset_list,
        "rata_ac": round(float(rata_ac.get("ya", 0)), 1),
        "rata_non_ac": round(float(rata_ac.get("tidak", 0)), 1),
    })

    # Ambil 15 riwayat pencarian terbaru & total hitungan pengecekan
    riwayat_qs = RiwayatPrediksi.objects.order_by("-waktu")[:15]
    riwayat_list = [
        {
            "waktu": item.waktu.strftime("%d %b %Y, %H:%M"),
            "jarak_km": item.jarak_km,
            "rating": item.rating,
            "ac": "Ber-AC" if item.ac == "ya" else "Non-AC",
            "estimasi_harga": format_rupiah(item.estimasi_harga),
            "kategori": item.kategori,
            "provider_ai": item.provider_ai,
            "analisis_ai": item.analisis_ai,
        }
        for item in riwayat_qs
    ]
    total_dicek = RiwayatPrediksi.objects.count()

    context = {
        "info_model": info_model,
        "form_data": form_data,
        "hasil_prediksi": hasil_prediksi,
        "pesan_error": pesan_error,
        "ai_provider": ai_provider,
        "has_api_key": bool(ai_api_key),
        "pesan_ai_setting": pesan_ai_setting,
        "dataset_list": dataset_list,
        "chart_payload": chart_payload,
        "riwayat_list": riwayat_list,
        "total_dicek": total_dicek,
    }
    return render(request, "index.html", context)