[app]

# (str) Title of your application
title = IGSaver

# (str) Package name
package.name = igsaver

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 1.0.4

# Gunakan Cython versi 0.29.x pada requirements spec jika diperlukan
requirements = python3, kivy==2.2.1, hostpython3, pillow, android, plyer

# Konfigurasi API dan NDK yang stabil
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# (str) Custom source folders for requirements
# (str) Presplash of the application
# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, accept all GPGS dependencies
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
