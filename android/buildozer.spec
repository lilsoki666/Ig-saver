[app]

title = IGSaver
package.name = igsaver
package.domain = com.syauqi

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 4.0.0

# yt-dlp is pure Python and runs inside the APK. No custom backend/API is required.
requirements = python3==3.11.9,kivy==2.3.0,requests,certifi,yt-dlp==2026.8.19

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk = 25b

# INTERNET is required to read/download public posts.
# WRITE_EXTERNAL_STORAGE is only used on Android 9 and older; Android 10+ uses MediaStore.
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE

android.archs = arm64-v8a
android.debug_artifact = apk
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

# python-for-android is pinned by the GitHub Actions workflow to the 2024.01.21 release,
# which supports Python 3.11 as its default recipe.
