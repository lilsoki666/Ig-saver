[app]
title = IG Saver
package.name = igsaver
package.domain = com.syauqi
source.dir = .
source.include_exts = py,png,jpg,jpeg,txt
version = 1.0.4
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.2.1
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 35
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.debug_artifact = apk
icon.filename = %(source.dir)s/assets/icon.png

p4a.fork = kivy
p4a.branch = v2024.01.21
p4a.commit = 957a3e5

[buildozer]
log_level = 2
warn_on_root = 1
