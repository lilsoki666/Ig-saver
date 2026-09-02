[app]

title = IGSaver
package.name = igsaver
package.domain = com.syauqi

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0.0

requirements = python3,kivy==2.3.0,requests,certifi

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 28c

android.permissions = INTERNET

android.archs = arm64-v8a

android.debug_artifact = apk
android.accept_sdk_license = True

p4a.branch = master
p4a.commit = 957a3e5

[buildozer]

log_level = 2
warn_on_root = 1
