# IGSaver App

Aplikasi Android berbasis Python & Kivy untuk memilih dan memuat gambar dari galeri perangkat.

## Cara Build APK via GitHub Actions
1. Push perubahan kode ke branch `main` atau `master`.
2. Masuk ke tab **Actions** di repositori GitHub Anda.
3. Jalankan workflow **Build Android APK** secara manual atau biarkan berjalan otomatis.
4. Unduh file APK dari bagian **Artifacts** setelah proses build selesai.

## Struktur Proyek
- `main.py`: Kode utama aplikasi Kivy
- `buildozer.spec`: Konfigurasi kompilasi Android
- `.github/workflows/build-apk.yml`: Script otomatisasi build APK
