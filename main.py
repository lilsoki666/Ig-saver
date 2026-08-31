import os
import re
import html
import threading
import urllib.request
import urllib.parse
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import platform

APP_NAME = "IGSaver"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36"
)


def clean_instagram_url(url):
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.lower() not in {"instagram.com", "www.instagram.com", "m.instagram.com"}:
        return ""
    return url.split("?")[0].rstrip("/") + "/"


def meta_content(page, prop):
    # Supports both property="og:image" and name="description" forms.
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\'](.*?)["\'][^>]*>',
        rf'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']{re.escape(prop)}["\'][^>]*>',
        rf'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\'](.*?)["\'][^>]*>',
        rf'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']{re.escape(prop)}["\'][^>]*>',
    ]
    for pattern in patterns:
        m = re.search(pattern, page, re.I | re.S)
        if m:
            value = html.unescape(m.group(1))
            value = value.replace("\\u0026", "&").replace("\\/", "/")
            return value
    return ""


def extract_caption(description):
    if not description:
        return ""
    # Instagram commonly formats the OpenGraph description as:
    # "username on Instagram: \"caption\""
    m = re.search(r'Instagram:\s*["“](.*?)["”]\s*$', description, re.S | re.I)
    if m:
        return m.group(1).strip()
    return description.strip()


def fetch_post(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(request, timeout=25) as response:
        page = response.read().decode("utf-8", "ignore")

    image_url = meta_content(page, "og:image")
    video_url = meta_content(page, "og:video") or meta_content(page, "og:video:url")
    description = meta_content(page, "og:description") or meta_content(page, "description")
    title = meta_content(page, "og:title")

    if not image_url and not video_url:
        raise RuntimeError(
            "Media tidak ditemukan. Pastikan postingan bersifat publik dan URL Instagram benar."
        )

    return {
        "image_url": image_url,
        "video_url": video_url,
        "caption": extract_caption(description),
        "title": title,
    }


def download_file(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, open(destination, "wb") as output:
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            output.write(chunk)


class MainWidget(BoxLayout):
    status_text = StringProperty("Tempel link postingan Instagram untuk memulai.")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(16), **kwargs)
        self.result = None
        self.result_file = None

        header = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        brand = Label(
            text="[b]IGSaver[/b]",
            markup=True,
            font_size=dp(25),
            halign="left",
            valign="middle",
            color=(0.08, 0.14, 0.23, 1),
        )
        brand.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        header.add_widget(brand)
        header.add_widget(Label(text="Simpan postingan", font_size=dp(14), color=(0.40, 0.45, 0.52, 1)))
        self.add_widget(header)

        self.url_input = TextInput(
            hint_text="Tempel link Instagram di sini",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=[dp(14), dp(14)],
            font_size=dp(16),
        )
        self.add_widget(self.url_input)

        actions = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.download_btn = Button(text="Download", background_normal="", background_color=(0.06, 0.43, 0.88, 1), bold=True)
        self.clear_btn = Button(text="Bersihkan", background_normal="", background_color=(0.88, 0.90, 0.94, 1), color=(0.10, 0.15, 0.22, 1))
        self.download_btn.bind(on_release=self.start_download)
        self.clear_btn.bind(on_release=self.clear)
        actions.add_widget(self.download_btn)
        actions.add_widget(self.clear_btn)
        self.add_widget(actions)

        self.status = Label(
            text=self.status_text,
            size_hint_y=None,
            height=dp(48),
            color=(0.35, 0.39, 0.46, 1),
            halign="left",
            valign="middle",
        )
        self.status.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self.status)

        self.preview = AsyncImage(source="", allow_stretch=True, keep_ratio=True, size_hint_y=0.44)
        self.add_widget(self.preview)

        self.caption = TextInput(
            hint_text="Caption akan tampil di sini",
            readonly=True,
            multiline=True,
            size_hint_y=0.25,
            font_size=dp(14),
            background_color=(0.96, 0.97, 0.98, 1),
        )
        self.add_widget(self.caption)

        footer = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.save_btn = Button(text="Simpan ke HP", background_normal="", background_color=(0.08, 0.62, 0.33, 1), bold=True, disabled=True)
        self.copy_btn = Button(text="Simpan Caption", background_normal="", background_color=(0.90, 0.92, 0.96, 1), color=(0.10, 0.15, 0.22, 1), disabled=True)
        self.save_btn.bind(on_release=self.save_result)
        self.copy_btn.bind(on_release=self.save_caption)
        footer.add_widget(self.save_btn)
        footer.add_widget(self.copy_btn)
        self.add_widget(footer)

        self.request_permissions()

    def request_permissions(self):
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                permissions = [Permission.INTERNET]
                for name in ("READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "WRITE_EXTERNAL_STORAGE"):
                    if hasattr(Permission, name):
                        permissions.append(getattr(Permission, name))
                request_permissions(permissions)
            except Exception:
                pass

    def set_status(self, text):
        self.status.text = text

    def start_download(self, *_):
        url = clean_instagram_url(self.url_input.text)
        if not url:
            self.set_status("URL Instagram tidak valid.")
            return
        self.download_btn.disabled = True
        self.save_btn.disabled = True
        self.copy_btn.disabled = True
        self.set_status("Mengambil data postingan…")
        threading.Thread(target=self.worker_download, args=(url,), daemon=True).start()

    def worker_download(self, url):
        try:
            result = fetch_post(url)
            media_url = result["video_url"] or result["image_url"]
            ext = ".mp4" if result["video_url"] else ".jpg"
            target_dir = Path(self._work_dir())
            target_dir.mkdir(parents=True, exist_ok=True)
            filename = "igsaver_media" + ext
            target = target_dir / filename
            download_file(media_url, str(target))
            self.result = result
            self.result_file = str(target)
            Clock.schedule_once(lambda dt: self.show_result(result, str(target)))
        except Exception as exc:
            message = str(exc)
            Clock.schedule_once(lambda dt: self.download_failed(message))

    def _work_dir(self):
        app = App.get_running_app()
        return os.path.join(app.user_data_dir, "downloads")

    def show_result(self, result, path):
        self.download_btn.disabled = False
        self.save_btn.disabled = False
        self.copy_btn.disabled = False
        self.caption.text = result.get("caption") or "Caption tidak tersedia dari halaman publik ini."
        # For video posts, og:image provides a thumbnail and remains useful as preview.
        self.preview.source = result.get("image_url", "")
        self.preview.reload()
        kind = "video" if result.get("video_url") else "foto"
        self.set_status(f"Berhasil mengambil {kind}. Tekan 'Simpan ke HP'.")

    def download_failed(self, message):
        self.download_btn.disabled = False
        self.set_status("Gagal: " + message)

    def save_result(self, *_):
        if not self.result_file or not os.path.exists(self.result_file):
            self.set_status("Belum ada media yang siap disimpan.")
            return
        try:
            download_dir = self._public_download_dir()
            os.makedirs(download_dir, exist_ok=True)
            name = "IGSaver_" + ("video.mp4" if self.result.get("video_url") else "foto.jpg")
            destination = os.path.join(download_dir, name)
            # Avoid overwriting previous downloads.
            stem, ext = os.path.splitext(destination)
            counter = 2
            while os.path.exists(destination):
                destination = f"{stem}_{counter}{ext}"
                counter += 1
            with open(self.result_file, "rb") as src, open(destination, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 256)
                    if not chunk:
                        break
                    dst.write(chunk)
            self.set_status("Media tersimpan di Download/IGSaver.")
        except Exception as exc:
            self.set_status("Gagal menyimpan media: " + str(exc))

    def _public_download_dir(self):
        if platform == "android":
            try:
                from plyer import storagepath
                base = storagepath.get_downloads_dir()
                if base:
                    return os.path.join(base, "IGSaver")
            except Exception:
                pass
            return "/storage/emulated/0/Download/IGSaver"
        return os.path.join(str(Path.home()), "Downloads", "IGSaver")

    def save_caption(self, *_):
        caption = self.caption.text.strip()
        if not caption:
            self.set_status("Tidak ada caption untuk disimpan.")
            return
        try:
            download_dir = self._public_download_dir()
            os.makedirs(download_dir, exist_ok=True)
            path = os.path.join(download_dir, "IGSaver_caption.txt")
            stem, ext = os.path.splitext(path)
            counter = 2
            while os.path.exists(path):
                path = f"{stem}_{counter}{ext}"
                counter += 1
            with open(path, "w", encoding="utf-8") as f:
                f.write(caption)
            self.set_status("Caption tersimpan di Download/IGSaver.")
        except Exception as exc:
            self.set_status("Gagal menyimpan caption: " + str(exc))

    def clear(self, *_):
        self.url_input.text = ""
        self.caption.text = ""
        self.preview.source = ""
        self.result = None
        self.result_file = None
        self.save_btn.disabled = True
        self.copy_btn.disabled = True
        self.set_status("Tempel link postingan Instagram untuk memulai.")


class IGSaverApp(App):
    def build(self):
        self.title = APP_NAME
        return MainWidget()


if __name__ == "__main__":
    IGSaverApp().run()
