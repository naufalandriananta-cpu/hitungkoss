import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")  # Agar aman dijalankan dari skrip tanpa jendela GUI
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def main():
    # 1. Memuat dataset asli kos_madiun.csv (Modul 03)
    df = pd.read_csv("kos_madiun.csv")
    print("=== 1. EKSPLORASI DATA AWAL ===")
    print(f"Ukuran dataset: {df.shape[0]} baris, {df.shape[1]} kolom")
    print("Jumlah nilai kosong per kolom:")
    print(df.isnull().sum())
    print("\nStatistik deskriptif:")
    print(df.describe())

    # 2. Preprocessing data kategorikal (Modul 10 & 14)
    # Mengubah teks 'ya'/'tidak' menjadi angka 1/0 agar bisa diproses model
    df["ac_num"] = df["ac"].map({"ya": 1, "tidak": 0})

    # 3. Menentukan Fitur (X) dan Target (y) (Modul 09 & 14)
    # Kolom 'nama' tidak dimasukkan karena hanya identitas unik kos
    fitur_kolom = ["jarak_km", "rating", "ac_num"]
    X = df[fitur_kolom]
    y = df["harga"]  # Satuan dalam ribuan rupiah per bulan

    # 4. Pembagian Data Latih (80%) dan Data Uji (20%) (Modul 10)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nJumlah data latih: {len(X_train)} baris | data uji: {len(X_test)} baris")

    # 5. Melatih dan Membandingkan Dua Model Regresi
    model_lr = LinearRegression()
    model_lr.fit(X_train, y_train)

    model_dt = DecisionTreeRegressor(max_depth=3, random_state=42)
    model_dt.fit(X_train, y_train)

    def hitung_metrik(nama_model, model):
        pred_train = model.predict(X_train)
        pred_test = model.predict(X_test)

        mae_train = mean_absolute_error(y_train, pred_train)
        rmse_train = np.sqrt(mean_squared_error(y_train, pred_train))
        r2_train = r2_score(y_train, pred_train)

        mae_test = mean_absolute_error(y_test, pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, pred_test))
        r2_test = r2_score(y_test, pred_test)

        print(f"\n=== EVALUASI: {nama_model} ===")
        print(f"Data Latih -> MAE: {mae_train:.2f} | RMSE: {rmse_train:.2f} | R2: {r2_train:.4f}")
        print(f"Data Uji   -> MAE: {mae_test:.2f} | RMSE: {rmse_test:.2f} | R2: {r2_test:.4f}")

        return {
            "mae_train": round(float(mae_train), 2),
            "rmse_train": round(float(rmse_train), 2),
            "r2_train": round(float(r2_train), 4),
            "mae_test": round(float(mae_test), 2),
            "rmse_test": round(float(rmse_test), 2),
            "r2_test": round(float(r2_test), 4),
        }

    metrik_lr = hitung_metrik("Linear Regression", model_lr)
    metrik_dt = hitung_metrik("Decision Tree Regressor (max_depth=3)", model_dt)

    # 6. Pemilihan Model Terbaik berdasarkan MAE & RMSE Data Uji
    if metrik_lr["mae_test"] <= metrik_dt["mae_test"]:
        model_terbaik = model_lr
        nama_terbaik = "Linear Regression"
        metrik_terbaik = metrik_lr
    else:
        model_terbaik = model_dt
        nama_terbaik = "Decision Tree Regressor (max_depth=3)"
        metrik_terbaik = metrik_dt

    print(f"\n>>> Model terpilih: {nama_terbaik} (MAE Uji: {metrik_terbaik['mae_test']} ribu Rp)")

    # 7. Membekukan Model + Metadata ke File Joblib (Modul 14)
    paket_model = {
        "model": model_terbaik,
        "nama_model": nama_terbaik,
        "fitur": fitur_kolom,
        "metrik": metrik_terbaik,
        "perbandingan": {
            "linear_regression": metrik_lr,
            "decision_tree": metrik_dt,
        },
        "jumlah_data": int(len(df)),
        "rata_harga": round(float(df["harga"].mean()), 2),
    }
    joblib.dump(paket_model, "model_kos.joblib")
    print("File 'model_kos.joblib' berhasil disimpan.")

    # 8. Membuat Visualisasi Data dengan Matplotlib (Modul 03 & 14)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    # Grafik Kiri: Scatter Plot Jarak vs Harga berdasarkan AC
    df_ac = df[df["ac"] == "ya"]
    df_non_ac = df[df["ac"] == "tidak"]

    axes[0].scatter(
        df_ac["jarak_km"], df_ac["harga"],
        color="#2563eb", label="Ber-AC (ya)", s=65, alpha=0.85
    )
    axes[0].scatter(
        df_non_ac["jarak_km"], df_non_ac["harga"],
        color="#f59e0b", label="Non-AC (tidak)", s=65, alpha=0.85
    )
    axes[0].set_title("Hubungan Jarak ke Kampus dan Harga Kos")
    axes[0].set_xlabel("Jarak ke Kampus (km)")
    axes[0].set_ylabel("Harga Kos (Ribu Rp / Bulan)")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Grafik Kanan: Bar Chart Rata-Rata Harga per Kategori AC
    rata_ac = df.groupby("ac")["harga"].mean().reindex(["tidak", "ya"])
    bars = axes[1].bar(
        ["Non-AC (tidak)", "Ber-AC (ya)"],
        rata_ac.values,
        color=["#f59e0b", "#2563eb"],
        width=0.5,
    )
    axes[1].set_title("Rata-Rata Harga Kos Berdasarkan Fasilitas AC")
    axes[1].set_xlabel("Fasilitas AC")
    axes[1].set_ylabel("Rata-Rata Harga (Ribu Rp / Bulan)")
    axes[1].set_ylim(0, 1400)
    axes[1].grid(axis="y", alpha=0.3)

    for bar in bars:
        tinggi = bar.get_height()
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            tinggi + 25,
            f"Rp {tinggi:.0f} rb",
            ha="center",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig("grafik_analisis_kos.png", dpi=150)
    plt.close()
    print("File 'grafik_analisis_kos.png' berhasil disimpan.")


if __name__ == "__main__":
    main()