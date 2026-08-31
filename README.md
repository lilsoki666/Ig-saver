# IGSaver v1.0.6

Project Android Kivy untuk memilih dan menampilkan gambar dari galeri perangkat.

## Build GitHub Actions
1. Upload seluruh isi project ke repository.
2. Pastikan workflow `.github/workflows/build-apk.yml` ikut ter-upload.
3. Buka **Actions** → **Build IGSaver APK** → **Run workflow**.
4. APK tersedia pada **Artifacts** sebagai `IGSaver-v1.0.6-apk`.

## Build stack yang dikunci
- Ubuntu 24.04
- OpenJDK 17
- Python 3.11.9
- Buildozer 1.5.0
- Cython 0.29.37
- Kivy 2.3.0
- python-for-android commit `957a3e5` (v2024.01.21)
- Android NDK 25b
- ARM64-v8a
