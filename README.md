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


## v1.0.3 build fix

The Android build configuration uses min API 24. This avoids the
`preadv`/`pwritev` compilation failure seen when the Python 3.11
recipe is compiled with NDK r28c and target API 23.


## v1.0.3
Download uses Python standard-library urllib instead of requests for Android build compatibility.


## v1.0.3 build fix
Pinned python-for-android to v2024.01.21 (commit 957a3e5) to keep the Kivy 2.2.1 build on the Python 3.11-era toolchain. The previous failure occurred because newer p4a built hostpython 3.14, while Kivy 2.2.1's build environment imports the removed `cgi` module.
