# IGSaver v1.0.0

IGSaver adalah project Android + backend untuk mengambil posting Instagram **publik** melalui link, tanpa meminta pengguna memasukkan username/password Instagram.

## Batasan penting

- Hanya target posting yang dapat diakses publik.
- Tidak ada login Instagram di aplikasi.
- Instagram dapat membatasi/menolak permintaan otomatis. Karena itu aplikasi **tidak menjamin semua URL Instagram selalu dapat diunduh**.
- Jangan gunakan project ini untuk melewati login, konten privat, CAPTCHA, atau pembatasan akses Instagram.
- Pastikan Anda mempunyai hak untuk menyimpan/menggunakan media yang diunduh.

## Struktur

```text
IGSaver_v1.0.0/
├── android/
│   ├── main.py
│   └── buildozer.spec
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── .github/workflows/build-apk.yml
├── .gitignore
└── README.md
```

## Arsitektur

```text
Android APK
   |
   | POST /api/fetch
   v
FastAPI backend
   |
   | yt-dlp -> metadata/media publik
   v
Instagram public URL
```

Media dikirim kembali ke APK sebagai URL. APK kemudian mengunduh file dan menyimpannya ke folder Download/IGSaver pada perangkat.

## 1. Jalankan backend untuk testing

```bash
cd backend
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Tes:

```text
http://127.0.0.1:8000/health
```

## 2. Deploy backend

Backend membutuhkan server HTTPS yang dapat menjalankan Docker/Python. GitHub Actions sendiri dipakai untuk membangun APK, bukan sebagai server API permanen.

Setelah backend online, ubah:

```python
API_BASE_URL = "https://URL-BACKEND-ANDA"
```

di `android/main.py`.

## 3. Build APK di GitHub

Push seluruh project ke GitHub dengan struktur yang sama.

Kemudian:

1. Buka tab **Actions**.
2. Pilih **Build IGSaver APK**.
3. Tekan **Run workflow**.
4. Setelah selesai, buka **Artifacts**.
5. Download `IGSaver-debug-apk`.
6. Ekstrak ZIP dan install APK di Android.

Workflow sengaja menggunakan container Buildozer agar environment build tidak bergantung pada Python/Java yang kebetulan tersedia di runner.

## 4. Alur aplikasi

1. Pengguna paste link Instagram.
2. Tekan **Ambil Posting**.
3. APK mengirim URL ke backend.
4. Backend mencoba membaca metadata posting publik.
5. Jika berhasil, backend mengembalikan:
   - jenis media
   - URL media
   - caption
   - judul/author jika tersedia
6. APK menampilkan preview dan caption.
7. **Simpan ke HP** mengunduh media.
8. **Simpan Caption** menyimpan caption sebagai `.txt`.

## Troubleshooting

### HTTP 403 / 401
Biasanya Instagram menolak permintaan otomatis. Ini bukan masalah UI APK. Coba URL posting publik lain. Jangan memasukkan session ID ke aplikasi.

### Tidak ada media
Posting dapat berupa carousel, private, login-gated, atau Instagram mengubah struktur respons. Versi awal ini memprioritaskan kestabilan dan penanganan error yang jelas.

### APK gagal build
Periksa log bagian paling bawah yang pertama kali memunculkan `ERROR`, bukan hanya baris `Command failed: ...`.
