from django.db import models


class RiwayatPrediksi(models.Model):
    # Menyimpan riwayat pencarian / kalkulasi tarif kos pengguna
    waktu = models.DateTimeField(auto_now_add=True)
    jarak_km = models.FloatField()
    ac = models.CharField(max_length=10)  # 'ya' atau 'tidak'
    rating = models.FloatField()
    estimasi_harga = models.FloatField()  # Satuan rupiah utuh
    kategori = models.CharField(max_length=50)  # Terjangkau, Menengah, Premium
    provider_ai = models.CharField(
        max_length=50, default="Analisis Lokal Bawaan"
    )
    analisis_ai = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.waktu.strftime('%d %b %Y, %H:%M')} — {self.jarak_km}km ({self.ac}) -> Rp {int(self.estimasi_harga):,}"