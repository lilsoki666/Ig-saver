# IGSaver Android v1.3

Aplikasi Android Kivy untuk mengambil metadata/media posting Instagram publik melalui backend milik sendiri.

## Penting
Aplikasi ini **tidak meminta Session ID pengguna** dan tidak mencoba melewati login/challenge Instagram.

Sebelum build, ubah:
`API_URL = "https://YOUR-BACKEND.example.com"`
di `main.py` menjadi alamat backend Anda.

Build:
```bash
buildozer android debug
```

APK akan berada di `bin/`.

Catatan: media hanya dapat diambil jika backend berhasil memperoleh media dari posting publik dan Instagram/CDN mengizinkan aksesnya.
