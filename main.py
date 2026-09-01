import os
import threading
import requests
from datetime import datetime
from urllib.parse import urlparse
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

API_URL = os.environ.get("IGSAVER_API_URL", "https://YOUR-BACKEND.example.com")

def safe_name(s):
    import re
    s = re.sub(r'[\\/:*?"<>|]+', "_", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:70] or "instagram_post")

class IGSaverLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16), spacing=dp(10), **kwargs)

        title = Label(text="[b]IGSaver - Simpan Posting[/b]", markup=True,
                      font_size=dp(25), size_hint_y=None, height=dp(45))
        self.add_widget(title)

        self.url = TextInput(
            hint_text="Tempel URL posting Instagram publik",
            multiline=False, size_hint_y=None, height=dp(52))
        self.add_widget(self.url)

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        clear = Button(text="Bersihkan")
        fetch = Button(text="Ambil Posting")
        clear.bind(on_release=self.clear)
        fetch.bind(on_release=self.fetch)
        row.add_widget(clear)
        row.add_widget(fetch)
        self.add_widget(row)

        self.status = Label(text="Siap.", size_hint_y=None, height=dp(42),
                            halign="left", valign="middle")
        self.status.bind(size=lambda o, v: setattr(o, "text_size", v))
        self.add_widget(self.status)

        self.preview = AsyncImage(source="", size_hint_y=0.52, allow_stretch=True,
                                  keep_ratio=True)
        self.add_widget(self.preview)

        self.caption = TextInput(
            text="", hint_text="Caption akan tampil di sini...",
            readonly=True, multiline=True, size_hint_y=0.30)
        self.add_widget(self.caption)

        bottom = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self.save = Button(text="Simpan ke HP", disabled=True)
        self.save.bind(on_release=self.save_media)
        bottom.add_widget(self.save)
        self.add_widget(bottom)

        self.post = None

    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", text))

    def clear(self, *_):
        self.url.text = ""
        self.preview.source = ""
        self.caption.text = ""
        self.status.text = "Siap."
        self.post = None
        self.save.disabled = True

    def fetch(self, *_):
        url = self.url.text.strip()
        if "instagram.com/" not in url:
            self.set_status("Masukkan URL Instagram.")
            return
        self.save.disabled = True
        self.set_status("Mengambil posting...")
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _fetch(self, url):
        try:
            r = requests.post(
                API_URL.rstrip("/") + "/api/fetch",
                json={"url": url},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                raise RuntimeError(data.get("error", "Posting tidak dapat diproses."))

            self.post = data
            Clock.schedule_once(lambda dt: self._show_result(data))
        except Exception as e:
            self.set_status("Gagal: " + str(e))

    def _show_result(self, data):
        media = data.get("media") or []
        caption = data.get("caption") or "Tidak ada caption."
        self.caption.text = caption
        if media:
            self.preview.source = media[0].get("url", "")
            self.save.disabled = False
            self.set_status(
                f"Berhasil. Ditemukan {len(media)} media ({data.get('type','post')})."
            )
        else:
            self.set_status("Posting ditemukan, tetapi media tidak tersedia.")

    def save_media(self, *_):
        if not self.post:
            return
        threading.Thread(target=self._save_media, daemon=True).start()

    def _save_media(self):
        media = self.post.get("media") or []
        caption = self.post.get("caption") or ""
        if not media:
            self.set_status("Tidak ada media untuk disimpan.")
            return

        folder = os.path.join(
            os.path.expanduser("~"), "Download", "IGSaver"
        )
        os.makedirs(folder, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = safe_name(self.post.get("title") or ("instagram_" + stamp))

        saved = 0
        for i, item in enumerate(media, 1):
            url = item.get("url")
            if not url:
                continue
            try:
                rr = requests.get(url, stream=True, timeout=90,
                                   headers={"User-Agent": "IGSaver/1.3"})
                rr.raise_for_status()
                ct = (rr.headers.get("Content-Type") or "").lower()
                ext = ".mp4" if "video" in ct else ".jpg"
                path = os.path.join(folder, f"{base}_{i}{ext}")
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(262144):
                        if chunk:
                            f.write(chunk)
                saved += 1
            except Exception:
                pass

        if caption:
            with open(os.path.join(folder, base + "_caption.txt"),
                      "w", encoding="utf-8") as f:
                f.write(caption)

        self.set_status(f"Selesai. {saved} media disimpan ke Download/IGSaver.")

class IGSaverApp(App):
    title = "IGSaver"
    def build(self):
        return IGSaverLayout()

if __name__ == "__main__":
    IGSaverApp().run()
