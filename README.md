# IG Saver

Aplikasi Android Kivy untuk menyimpan media yang pengguna miliki atau punya izin untuk menyimpannya.

## Fitur starter
- Input direct URL foto/video
- Download media
- Caption opsional disimpan sebagai TXT
- Riwayat file di aplikasi
- Siap dibuild menjadi APK dengan Buildozer

## Penting
Versi ini sengaja tidak melakukan scraping halaman Instagram, tidak meminta password Instagram, dan tidak membypass login atau pembatasan akses.

Instagram/Meta menyediakan API resmi untuk akun Instagram Professional yang diotorisasi. Untuk mengambil media milik akun melalui API resmi, diperlukan autentikasi dan permission yang sesuai.

## Menjalankan di Android
Project ini disiapkan untuk dibuild melalui GitHub Actions. Upload seluruh folder project ke repository GitHub, lalu buka Actions dan jalankan workflow "Build IG Saver APK".

## Arah pengembangan berikutnya
1. UI lebih modern.
2. Input URL posting Instagram.
3. Integrasi API resmi Meta untuk akun yang diotorisasi.
4. Preview media.
5. Penyimpanan caption dan metadata.
6. Riwayat download.
7. Share hasil download.
