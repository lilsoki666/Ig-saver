from __future__ import annotations

__version__ = "1.0.0"

import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse

import certifi
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import platform


# ============================================================
# IMPORTANT:
# After deploying the backend, replace this URL.
# Example:
# API_BASE_URL = "https://igsaver-api.example.com"
# ============================================================
API_BASE_URL = "https://YOUR-BACKEND-URL"


def rounded_background(widget, rgba=(0.10, 0.12, 0.16, 1), radius=14):
    with widget.canvas.before:
        Color(*rgba)
        rect = RoundedRectangle(
            pos=widget.pos,
            size=widget.size,
            radius=[dp(radius)],
        )

    def update(*_):
        rect.pos = widget.pos
        rect.size = widget.size

    widget.bind(pos=update, size=update)
    return rect


class IGSaverApp(App):
    def build(self):
        self.title = "IGSaver"
        self.media_url = ""
        self.media_type = ""
        self.caption = ""
        self.busy = False

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(10),
        )
        rounded_background(root, (0.035, 0.045, 0.06, 1), 0)

        title = Label(
            text="[b]IGSaver[/b]",
            markup=True,
            font_size=dp(28),
            size_hint_y=None,
            height=dp(48),
            color=(0.95, 0.97, 1, 1),
        )
        root.add_widget(title)

        subtitle = Label(
            text="Simpan posting publik Instagram tanpa login",
            font_size=dp(14),
            size_hint_y=None,
            height=dp(28),
            color=(0.65, 0.70, 0.78, 1),
        )
        root.add_widget(subtitle)

        self.url_input = TextInput(
            hint_text="Tempel link posting Instagram di sini",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=[dp(14), dp(12)],
            font_size=dp(16),
        )
        root.add_widget(self.url_input)

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))

        clear_btn = self.make_button("Bersihkan")
        clear_btn.bind(on_release=self.clear_all)
        row.add_widget(clear_btn)

        fetch_btn = self.make_button("Ambil Posting")
        fetch_btn.bind(on_release=self.fetch_post)
        row.add_widget(fetch_btn)
        root.add_widget(row)

        self.status = Label(
            text="Tempel link lalu tekan Ambil Posting.",
            font_size=dp(14),
            size_hint_y=None,
            height=dp(42),
            color=(0.80, 0.84, 0.90, 1),
            halign="center",
            valign="middle",
        )
        self.status.bind(size=lambda *_: setattr(
            self.status, "text_size", self.status.size
        ))
        root.add_widget(self.status)

        self.preview = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint_y=1,
        )
        root.add_widget(self.preview)

        caption_title = Label(
            text="Caption",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(15),
            color=(0.70, 0.76, 0.84, 1),
            halign="left",
        )
        caption_title.bind(size=lambda *_: setattr(
            caption_title, "text_size", caption_title.size
        ))
        root.add_widget(caption_title)

        self.caption_box = TextInput(
            text="",
            hint_text="Caption akan tampil di sini...",
            readonly=True,
            multiline=True,
            size_hint_y=0.8,
            font_size=dp(15),
            padding=[dp(12), dp(12)],
        )
        root.add_widget(self.caption_box)

        save_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))

        self.save_media_btn = self.make_button("Simpan ke HP")
        self.save_media_btn.bind(on_release=self.save_media)
        self.save_media_btn.disabled = True
        save_row.add_widget(self.save_media_btn)

        self.save_caption_btn = self.make_button("Simpan Caption")
        self.save_caption_btn.bind(on_release=self.save_caption)
        self.save_caption_btn.disabled = True
        save_row.add_widget(self.save_caption_btn)

        root.add_widget(save_row)

        return root

    def make_button(self, text):
        btn = Button(
            text=text,
            font_size=dp(16),
            bold=True,
            background_normal="",
            background_color=(0.10, 0.42, 0.84, 1),
        )
        return btn

    def set_status(self, text, error=False):
        def update(_dt):
            self.status.text = text
            self.status.color = (
                (1, 0.45, 0.45, 1)
                if error
                else (0.65, 0.92, 0.72, 1)
            )
        Clock.schedule_once(update)

    def clear_all(self, *_):
        self.url_input.text = ""
        self.preview.texture = None
        self.caption_box.text = ""
        self.media_url = ""
        self.media_type = ""
        self.caption = ""
        self.save_media_btn.disabled = True
        self.save_caption_btn.disabled = True
        self.set_status("Form dibersihkan.")

    def fetch_post(self, *_):
        if self.busy:
            return

        url = self.url_input.text.strip()
        parsed = urlparse(url)

        if not url or parsed.scheme not in ("http", "https"):
            self.set_status("Masukkan link Instagram yang valid.", True)
            return

        if "instagram.com" not in (parsed.hostname or "").lower():
            self.set_status("Link harus berasal dari instagram.com.", True)
            return

        if "YOUR-BACKEND-URL" in API_BASE_URL:
            self.set_status(
                "Backend belum diatur. Isi API_BASE_URL di main.py terlebih dahulu.",
                True,
            )
            return

        self.busy = True
        self.save_media_btn.disabled = True
        self.save_caption_btn.disabled = True
        self.set_status("Mengambil posting publik...")

        threading.Thread(
            target=self._fetch_worker,
            args=(url,),
            daemon=True,
        ).start()

    def _fetch_worker(self, url):
        try:
            response = requests.post(
                API_BASE_URL.rstrip("/") + "/api/fetch",
                json={"url": url},
                timeout=45,
                verify=certifi.where(),
            )

            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", "Server error")
                except Exception:
                    detail = response.text[:300]
                raise RuntimeError(f"HTTP {response.status_code}: {detail}")

            data = response.json()

            if not data.get("ok"):
                raise RuntimeError(data.get("message") or "Posting tidak dapat dibaca.")

            Clock.schedule_once(lambda _dt: self._apply_result(data))
        except requests.exceptions.SSLError:
            self.set_status(
                "SSL gagal. Pastikan waktu/tanggal HP benar dan backend HTTPS valid.",
                True,
            )
        except requests.exceptions.RequestException as exc:
            self.set_status(f"Gagal terhubung ke backend: {exc}", True)
        except Exception as exc:
            self.set_status(str(exc), True)
        finally:
            self.busy = False

    def _apply_result(self, data):
        self.media_url = data.get("media_url", "")
        self.media_type = data.get("type", "")
        self.caption = data.get("caption", "")

        self.caption_box.text = self.caption or "Tidak ada caption yang dapat dibaca."

        msg = data.get("message") or "Posting berhasil dibaca."
        self.status.text = msg
        self.status.color = (0.65, 0.92, 0.72, 1)

        self.save_media_btn.disabled = not bool(self.media_url)
        self.save_caption_btn.disabled = not bool(self.caption.strip())

        thumbnail = data.get("thumbnail_url", "")
        if thumbnail:
            threading.Thread(
                target=self._load_preview_worker,
                args=(thumbnail,),
                daemon=True,
            ).start()

    def _load_preview_worker(self, url):
        try:
            r = requests.get(
                url,
                timeout=30,
                verify=certifi.where(),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            r.raise_for_status()
            from io import BytesIO
            data = BytesIO(r.content)

            def apply(_dt):
                try:
                    self.preview.texture = CoreImage(data, ext="jpg").texture
                except Exception:
                    pass

            Clock.schedule_once(apply)
        except Exception:
            # Preview is optional. Saving can still work if media_url is available.
            pass

    def save_media(self, *_):
        if not self.media_url:
            self.set_status("Belum ada media untuk disimpan.", True)
            return

        self.set_status("Mengunduh media...")
        threading.Thread(
            target=self._save_media_worker,
            daemon=True,
        ).start()

    def _save_media_worker(self):
        try:
            r = requests.get(
                self.media_url,
                timeout=90,
                stream=True,
                verify=certifi.where(),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            r.raise_for_status()

            content_type = r.headers.get("content-type", "")
            ext = ".mp4" if ("video" in content_type or self.media_type == "video") else ".jpg"

            # Android app-specific external Downloads folder.
            # This is intentionally permission-light. The file can be shared from
            # Android's file manager. A later version can add MediaStore/SAF.
            if platform == "android":
                try:
                    from android.storage import primary_external_storage_path
                    base = Path(primary_external_storage_path())
                    folder = base / "Download" / "IGSaver"
                except Exception:
                    folder = Path("/storage/emulated/0/Download/IGSaver")
            else:
                folder = Path.home() / "Downloads" / "IGSaver"

            folder.mkdir(parents=True, exist_ok=True)

            filename = f"IGSaver_{self._safe_stamp()}{ext}"
            path = folder / filename

            with path.open("wb") as f:
                for chunk in r.iter_content(1024 * 256):
                    if chunk:
                        f.write(chunk)

            self.set_status(f"Tersimpan: {path.name}")
        except Exception as exc:
            self.set_status(f"Gagal menyimpan media: {exc}", True)

    def save_caption(self, *_):
        if not self.caption.strip():
            self.set_status("Tidak ada caption.", True)
            return

        try:
            if platform == "android":
                try:
                    from android.storage import primary_external_storage_path
                    base = Path(primary_external_storage_path())
                    folder = base / "Download" / "IGSaver"
                except Exception:
                    folder = Path("/storage/emulated/0/Download/IGSaver")
            else:
                folder = Path.home() / "Downloads" / "IGSaver"

            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"IGSaver_{self._safe_stamp()}.txt"
            path.write_text(self.caption, encoding="utf-8")
            self.set_status(f"Caption tersimpan: {path.name}")
        except Exception as exc:
            self.set_status(f"Gagal menyimpan caption: {exc}", True)

    @staticmethod
    def _safe_stamp():
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    IGSaverApp().run()
