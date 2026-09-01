[app]
title = IGSaver
package.name = igsaver
package.domain = org.igsaver
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,txt,json
version = 1.2.4

# Keep dependencies minimal and compatible with the pinned p4a release.
requirements = python3==3.11.9,kivy==2.3.0,plyer,requests==2.32.5,urllib3==2.5.0,certifi==2025.8.3

android.api = 35
android.minapi = 23
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.debug_artifact = apk
android.private_storage = True
android.permissions = INTERNET,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
orientation = portrait
fullscreen = 0

p4a.fork = kivy
p4a.branch = master
p4a.commit = 957a3e5

[buildozer]
log_level = 2
warn_on_root = 1
