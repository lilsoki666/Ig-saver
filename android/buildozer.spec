[app]
title = IGSaver
package.name = igsaver
package.domain = com.syauqi
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,json
source.exclude_dirs = .git,.github,.buildozer,bin,__pycache__

version = 1.3.0

requirements = python3,kivy==2.2.1,requests,pyjnius

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.debug_artifact = apk
android.accept_sdk_license = True
android.permissions = INTERNET,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
