# IGSaver v1.2.4

IGSaver adalah aplikasi Android sederhana untuk membaca posting Instagram publik.

## Perbaikan v1.2.4
- Menggunakan Instagram oEmbed sebagai jalur utama untuk thumbnail dan judul/caption publik.
- Fallback ke halaman embed Instagram.
- Parser metadata diperbaiki agar tidak bergantung pada urutan atribut HTML.
- Menambahkan fallback JSON-LD dan data caption Instagram.
- Respons HTTP 200 yang ternyata halaman login/challenge tidak lagi dianggap sukses palsu.
- Tidak memerlukan Session ID pengguna.
- Konfigurasi build v1.2.3 yang sudah berhasil dipertahankan.

## Catatan
Instagram dapat mengubah endpoint publik, menerapkan rate limit, atau membatasi konten tertentu. Aplikasi hanya mencoba membaca posting yang tersedia secara publik.
