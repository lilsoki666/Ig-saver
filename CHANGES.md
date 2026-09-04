## 3.0.0
- Menyesuaikan Android API 33 dan NDK 25b untuk menghindari error clang/Kivy pada NDK 28.
- Menghapus `pyjnius` dari requirements Buildozer.
- Menghapus request permission Android lama dari runtime.

# Changes

## 2.0.0

- Menghapus ketergantungan backend FastAPI sepenuhnya.
- Ekstraksi Instagram dilakukan langsung di APK menggunakan yt-dlp.
- Menambahkan fallback OpenGraph untuk posting publik tertentu.
- Mendukung beberapa media yang dikembalikan extractor.
- Menghindari format yt-dlp yang membutuhkan FFmpeg merge.
- Penyimpanan Android 10+ menggunakan MediaStore ke Download/IGSaver.
- Android 9 dan lebih lama memakai WRITE_EXTERNAL_STORAGE sebagai fallback.
- Python Android dikunci ke 3.11.9 dan Kivy 2.3.0.
- yt-dlp dikunci ke 2026.8.19.
