# IGSaver build fixes

- Removed invalid `p4a.branch = 2024.1.21`.
- Removed redundant pip installation of python-for-android.
- Pins python-for-android to commit `957a3e5`.
- Keeps Ubuntu 22.04, Java 17, Python 3.11, Cython 0.29.37, SDK 35 and Build Tools 35.0.0.
- Keeps the Buildozer sdkmanager compatibility wrapper.
- Verifies AIDL before the build.
