# Changes

## 4.0.0
- Fixed the build failure caused by python-for-android master selecting Python 3.14.2 while the app requested Python 3.11.9.
- Pinned python-for-android to `2024.01.21`, which added Python 3.11 support and uses Python 3.11 by default.
- Removed the obsolete `p4a.branch = master` setting.
- Aligned the CI Android SDK packages with API 33 / Build Tools 33.0.2.
- Kept NDK r25b and Python 3.11.9 for compatibility with Kivy 2.3.0.
- Backend remains completely removed; the app uses direct extraction.
