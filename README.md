# IGSaver v1.0.5

Project Android Kivy untuk IGSaver.

## Perbaikan build v1.0.5
- Python GitHub Actions dikunci ke 3.11.9.
- Buildozer dikunci ke 1.5.0.
- Cython dikunci ke 0.29.37.
- python-for-android dikunci ke release 2024.01.21.
- NDK dikunci ke 25b.
- Hanya ARM64 yang dibuild untuk mengurangi titik kegagalan.
- Workflow mencoba build sampai 3 kali untuk mengatasi kegagalan download sementara seperti HTTP 502.
- Dependency aplikasi dipersempit menjadi Kivy + Plyer.

## Build
GitHub → Actions → Build IGSaver APK → Run workflow.

APK akan tersedia pada Artifacts setelah job berhasil.
