# IGSaver v1.3

## Struktur
- `android/` — aplikasi Android Kivy
- `backend/` — API FastAPI
- `.github/workflows/build-apk.yml` — workflow GitHub Actions

## Alur
1. Pengguna menempel URL posting/reel Instagram publik.
2. Android mengirim URL ke backend.
3. Backend mencoba mengambil metadata dan URL media.
4. Android menampilkan preview + caption.
5. Pengguna menekan Simpan ke HP.
6. Media dan caption disimpan ke `Download/IGSaver`.

## Catatan penting
Versi ini menghilangkan kebutuhan Session ID dari sisi pengguna. Namun pengambilan konten Instagram publik tetap bergantung pada akses yang tersedia dan dapat berubah sewaktu-waktu. Tidak ada bypass login/challenge.

## Build Android
Edit URL backend di `android/main.py`, lalu push ke GitHub. Workflow akan membuat APK.
