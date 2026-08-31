[app]

title = IGSaver
package.name = igsaver
package.domain = com.lilsoki666
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 1.0.5

# Hanya dependency yang benar-benar dipakai aplikasi.
requirements = python3,kivy==2.3.0,plyer

# Build stabil dengan python-for-android rilis yang kompatibel.
p4a.source_dir = /home/runner/p4a

android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

orientation = portrait
fullscreen = 0

# Android 13+ memakai READ_MEDIA_IMAGES; izin lama dipertahankan untuk perangkat lama.
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
