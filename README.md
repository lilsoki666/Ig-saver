# IGSaver — Android Direct Mode

IGSaver 2.0 mengambil media **langsung dari perangkat Android**. Project ini tidak membutuhkan FastAPI, server, domain, atau backend milik sendiri.

## Cara kerja

1. Pengguna menempel link Post/Reel Instagram publik.
2. APK mencoba ekstraksi lokal dengan `yt-dlp`.
3. Jika metadata yt-dlp tidak tersedia, aplikasi mencoba fallback OpenGraph untuk media publik yang mengekspos metadata tersebut.
4. Media diunduh langsung ke `Download/IGSaver`.
5. Android 10+ memakai MediaStore sehingga tidak membutuhkan akses storage luas.

## Batasan

Instagram dapat mengubah proteksi/endpoint kapan saja. Posting private, posting yang meminta login, konten yang dibatasi umur/wilayah, atau permintaan yang diblokir Instagram dapat gagal tanpa cookies/login. Project ini sengaja tidak menyimpan username, password, atau cookies pengguna.

Gunakan hanya untuk konten yang memang berhak Anda simpan dan patuhi ketentuan Instagram serta hak cipta pemilik konten.

## Build APK di GitHub

Push seluruh project ke branch `main`, buka tab **Actions**, jalankan workflow **Build IGSaver APK**, lalu ambil artifact `IGSaver-debug-apk`.

Konfigurasi utama ada di `android/buildozer.spec`. Python target dikunci ke 3.11.9 dan Kivy ke 2.3.0 untuk menghindari kegagalan kompilasi yang sebelumnya muncul dengan Python 3.14.


## Build v3

- Android API 33 / NDK 25b untuk kompatibilitas Kivy 2.3.0 yang lebih konservatif.
- Python 3.11.9.
- `pyjnius` tidak dicantumkan sebagai pip requirement; akses JNI tetap memakai `jnius` yang disediakan toolchain Android/Kivy.
- Tidak ada backend/API milik sendiri.

## Build note
The CI pins `python-for-android==2024.01.21` because the current p4a master recipe uses Python 3.14.2, which conflicts with this Kivy 2.3.0 / Python 3.11 build. The 2024.01.21 release explicitly added Python 3.11 support.
