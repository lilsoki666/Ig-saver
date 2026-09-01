# IGSaver v1.2.1

IGSaver is a Kivy Android application for reading public Instagram post/reel pages without asking users for an Instagram Session ID.

## What changed in v1.2.1
- Removed Session ID from the source and normal user flow.
- Uses the public Instagram page/embed as the first retrieval route.
- Uses `certifi` for HTTPS certificate verification.
- Gives a clear message when Instagram returns HTTP 403/404 instead of telling users to provide a Session ID.
- Keeps the project small and suitable for GitHub Actions.

## Important limitation
Instagram controls access to its public pages and may return HTTP 403, rate-limit automated requests, or require login depending on the post, account, region, device, and current anti-bot policy. Therefore no standalone client can honestly guarantee that every Instagram URL will work. Private or restricted posts are not supported.

## Build on GitHub
Push the project to GitHub and run **Actions → Build IGSaver APK → Run workflow**. The generated debug APK is uploaded as the `IGSaver-debug-apk` artifact.

## Normal use
1. Open IGSaver.
2. Paste a public Instagram post/reel URL.
3. Tap **Ambil Posting**.
4. If Instagram permits public access, the app reads the preview image and available caption.

No Session ID is requested or stored.
