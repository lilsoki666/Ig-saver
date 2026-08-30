# main.py
# IG Saver - untuk media yang Anda miliki atau berhak menyimpannya.
# Input harus berupa DIRECT URL media (image/video), bukan halaman Instagram.
# Caption opsional disimpan sebagai file .txt.

import os
import re
import threading
from datetime import datetime
from urllib.parse import urlparse

from urllib.request import Request, urlopen
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Download", "IGSaver")


def safe_filename(name):
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:100] or "instagram_media"


def guess_extension(content_type, url):
    ct = (content_type or "").lower()
    for mime, ext in (
        ("image/jpeg", ".jpg"), ("image/png", ".png"),
        ("image/webp", ".webp"), ("video/mp4", ".mp4"),
        ("video/webm", ".webm"),
    ):
        if mime in ct:
            return ext
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".mov"):
        if path.endswith(ext):
            return ext
    return ".bin"


class DownloaderLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16),
                         spacing=dp(10), **kwargs)

        title = Label(text="[b]IG Saver[/b]", markup=True,
                      font_size=dp(26), size_hint_y=None, height=dp(45))
        self.add_widget(title)

        info = Label(
            text="Simpan media yang Anda miliki atau yang Anda punya izin untuk menyimpannya.",
            halign="left", valign="middle", size_hint_y=None, height=dp(55))
        info.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(info)

        self.url_input = TextInput(
            hint_text="Tempel direct URL foto/video di sini",
            multiline=False, size_hint_y=None, height=dp(52))
        self.add_widget(self.url_input)

        self.caption_input = TextInput(
            hint_text="Caption postingan (opsional)",
            multiline=True, size_hint_y=None, height=dp(110))
        self.add_widget(self.caption_input)

        self.download_button = Button(
            text="Simpan Media", size_hint_y=None, height=dp(52))
        self.download_button.bind(on_release=self.start_download)
        self.add_widget(self.download_button)

        self.status = Label(text="Siap.", halign="left", valign="top",
                            size_hint_y=None, height=dp(70))
        self.status.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(self.status)

        scroll = ScrollView()
        self.history = Label(
            text="Riwayat file akan tampil di sini.",
            halign="left", valign="top", size_hint_y=None)
        self.history.bind(texture_size=lambda o, v: setattr(o, "height", v[1]))
        scroll.add_widget(self.history)
        self.add_widget(scroll)

    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", text))

    def add_history(self, text):
        def update(dt):
            current = self.history.text
            if current == "Riwayat file akan tampil di sini.":
                current = ""
            self.history.text = text + ("\n\n" + current if current else "")
        Clock.schedule_once(update)

    def start_download(self, *_):
        url = self.url_input.text.strip()
        caption = self.caption_input.text.strip()
        if not url.startswith(("http://", "https://")):
            self.set_status("URL tidak valid.")
            return

        self.download_button.disabled = True
        self.set_status("Mengunduh media...")
        threading.Thread(target=self.download_media,
                         args=(url, caption), daemon=True).start()

    def download_media(self, url, caption):
        try:
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            request = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Android)"}
            )

            with urlopen(request, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "")
                final_url = response.geturl()

                if not (content_type.startswith("image/") or
                        content_type.startswith("video/")):
                    raise ValueError(
                        "URL bukan direct URL foto/video. "
                        "Aplikasi ini tidak melakukan scraping halaman Instagram."
                    )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base = safe_filename("instagram_" + timestamp)
                media_path = os.path.join(
                    DOWNLOAD_DIR,
                    base + guess_extension(content_type, final_url)
                )

                with open(media_path, "wb") as file:
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        file.write(chunk)

            caption_path = None
            if caption:
                caption_path = os.path.join(DOWNLOAD_DIR, base + "_caption.txt")
                with open(caption_path, "w", encoding="utf-8") as file:
                    file.write(caption)

            result = f"Berhasil disimpan:\n{media_path}"
            if caption_path:
                result += f"\nCaption:\n{caption_path}"
            self.set_status("Download berhasil.")
            self.add_history(result)

        except Exception as exc:
            self.set_status(f"Gagal: {exc}")
        finally:
            Clock.schedule_once(
                lambda dt: setattr(self.download_button, "disabled", False))

class IGSaverApp(App):
    title = "IG Saver"
    def build(self):
        return DownloaderLayout()

if __name__ == "__main__":
    IGSaverApp().run()
