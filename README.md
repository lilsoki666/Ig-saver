# IGSaver v1.1.0

Aplikasi Android Kivy untuk mengambil media publik dari URL posting Instagram dan menyimpan media serta caption.

## Build
Workflow GitHub Actions mempertahankan toolchain v1.0.8 yang sudah terbukti berhasil: Ubuntu 22.04, Python 3.11.9, Kivy 2.3.0, Buildozer 1.5.0, p4a commit 957a3e5, NDK 25b, ARM64.

## Catatan
Downloader bergantung pada metadata publik halaman Instagram (OpenGraph). Postingan privat, halaman yang meminta login, atau perubahan struktur Instagram dapat membuat media/caption tidak tersedia.
