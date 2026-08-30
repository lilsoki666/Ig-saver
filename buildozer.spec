[app]
title = IG Saver
package.name = igsaver
package.domain = com.syauqi
source.dir = .
source.include_exts = py,png,jpg,jpeg,txt
version = 1.0.0
requirements = python3,kivy==2.2.1,requests
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 35
android.minapi = 24
android.ndk = 28c
android.accept_sdk_license = True
android.debug_artifact = apk
icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
