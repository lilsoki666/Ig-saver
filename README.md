# IGSaver API v1.3

Backend FastAPI yang menerima URL posting/reel Instagram publik dan mencoba memperoleh metadata + media menggunakan yt-dlp.

Jalankan lokal:
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Tes:
`GET /health`

Endpoint:
`POST /api/fetch`
JSON:
```json
{"url":"https://www.instagram.com/p/POST_ID/"}
```

## Batasan
Tidak ada jaminan semua posting Instagram dapat diekstrak. Instagram dapat mengubah sistem, membatasi IP, meminta login, atau membatasi media tertentu. Backend ini tidak melakukan bypass login/challenge.

Untuk penggunaan produksi, tambahkan rate limit, authentication untuk API milik Anda, logging, timeout, dan validasi URL.
