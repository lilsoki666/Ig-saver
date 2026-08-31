# IGSaver v1.1.1

Perbaikan utama pada v1.1.1:
- Memperbaiki SSL Android dengan CA bundle `certifi`.
- Pengambilan halaman Instagram memakai header yang lebih lengkap.
- Download media memakai SSL context yang sama dan timeout lebih aman.
- Tidak mengubah alur UI utama.

## Build
Workflow menggunakan Ubuntu 22.04, Python 3.11.9, Kivy 2.3.0, Buildozer 1.5.0, p4a commit 957a3e5, NDK 25b, ARM64.

## Catatan
Aplikasi hanya mengambil media dari posting Instagram yang dapat diakses publik. Perubahan struktur halaman Instagram, posting privat, atau halaman yang meminta login dapat membuat metadata media/caption tidak tersedia.
