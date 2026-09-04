from __future__ import annotations

__version__ = "3.0.0"

import datetime
import mimetypes
import re
import threading
from html import unescape
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

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
)
ALLOWED_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com"}


def rounded_background(widget, rgba=(0.10, 0.12, 0.16, 1), radius=14):
    with widget.canvas.before:
        Color(*rgba)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])

    def update(*_):
        rect.pos = widget.pos
        rect.size = widget.size

    widget.bind(pos=update, size=update)
    return rect


def is_instagram_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and (
            host in ALLOWED_HOSTS or host.endswith(".instagram.com")
        )
    except Exception:
        return False


def first_text(*values) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def media_from_info(info: dict) -> list[dict]:
    """Normalize yt-dlp output to a small list of direct downloadable media items."""
    result: list[dict] = []

    entries = info.get("entries")
    if entries:
        for entry in entries:
            if isinstance(entry, dict):
                result.extend(media_from_info(entry))
        return result

    direct_url = info.get("url")
    if not isinstance(direct_url, str) or not direct_url.startswith("http"):
        return result

    ext = first_text(info.get("ext"), "mp4")
    video_codec = info.get("vcodec")
    media_type = "image" if video_codec == "none" or ext.lower() in {
        "jpg", "jpeg", "png", "webp", "avif"
    } else "video"

    result.append(
        {
            "url": direct_url,
            "type": media_type,
            "ext": ext.lower(),
            "thumbnail": first_text(info.get("thumbnail")),
        }
    )
    return result


def extract_with_ytdlp(url: str) -> dict:
    """Extract a public Instagram post locally; no custom backend is used."""
    from yt_dlp import YoutubeDL

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": False,
        # Avoid formats that require ffmpeg merging inside the APK.
        "format": "best[protocol^=http]/best",
        "http_headers": {"User-Agent": USER_AGENT},
        "socket_timeout": 30,
        "retries": 2,
        "extractor_retries": 2,
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not isinstance(info, dict):
        raise RuntimeError("Instagram tidak mengembalikan data posting.")

    items = media_from_info(info)
    caption = first_text(info.get("description"), info.get("title"))
    thumbnail = first_text(info.get("thumbnail"))

    if items and not thumbnail:
        thumbnail = first_text(items[0].get("thumbnail"))

    if not items:
        raise RuntimeError("yt-dlp tidak menemukan URL media langsung.")

    return {
        "items": items,
        "caption": caption,
        "thumbnail": thumbnail,
        "source": "yt-dlp",
    }


def _meta_content(html: str, key: str) -> str:
    # Handles property/name appearing before content in normal OpenGraph markup.
    patterns = (
        rf'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return unescape(match.group(1)).strip()
    return ""


def extract_with_opengraph(url: str) -> dict:
    """Fallback for public pages exposing OpenGraph metadata (typically one media item)."""
    response = requests.get(
        url,
        timeout=35,
        verify=certifi.where(),
        headers={"User-Agent": USER_AGENT, "Accept-Language": "id-ID,id;q=0.9,en;q=0.7"},
    )
    response.raise_for_status()
    html = response.text

    video = first_text(_meta_content(html, "og:video"), _meta_content(html, "og:video:secure_url"))
    image = _meta_content(html, "og:image")
    caption = first_text(_meta_content(html, "og:description"), _meta_content(html, "description"))

    if video:
        items = [{"url": video, "type": "video", "ext": "mp4", "thumbnail": image}]
    elif image:
        items = [{"url": image, "type": "image", "ext": "jpg", "thumbnail": image}]
    else:
        raise RuntimeError("Metadata media publik tidak tersedia.")

    return {"items": items, "caption": caption, "thumbnail": image, "source": "OpenGraph"}


def extract_instagram(url: str) -> dict:
    errors: list[str] = []
    try:
        return extract_with_ytdlp(url)
    except Exception as exc:
        errors.append(str(exc))

    try:
        return extract_with_opengraph(url)
    except Exception as exc:
        errors.append(str(exc))

    detail = errors[-1] if errors else "media tidak ditemukan"
    raise RuntimeError(
        "Posting tidak bisa dibaca langsung dari perangkat. "
        "Pastikan posting bersifat publik dan link masih aktif. "
        f"Detail: {detail[:180]}"
    )


class IGSaverApp(App):
    def build(self):
        self.title = "IGSaver"
        self.media_items: list[dict] = []
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
            text="Simpan posting publik Instagram langsung dari HP",
            font_size=dp(14),
            size_hint_y=None,
            height=dp(28),
            color=(0.65, 0.70, 0.78, 1),
        )
        root.add_widget(subtitle)

        self.url_input = TextInput(
            hint_text="Tempel link Post / Reel Instagram",
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
            text="Tanpa backend. Tempel link lalu tekan Ambil Posting.",
            font_size=dp(14),
            size_hint_y=None,
            height=dp(48),
            color=(0.80, 0.84, 0.90, 1),
            halign="center",
            valign="middle",
        )
        self.status.bind(size=lambda *_: setattr(self.status, "text_size", self.status.size))
        root.add_widget(self.status)

        self.preview = Image(allow_stretch=True, keep_ratio=True, size_hint_y=1)
        root.add_widget(self.preview)

        caption_title = Label(
            text="Caption",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(15),
            color=(0.70, 0.76, 0.84, 1),
            halign="left",
        )
        caption_title.bind(size=lambda *_: setattr(caption_title, "text_size", caption_title.size))
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
        self.save_media_btn = self.make_button("Simpan Media")
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
        return Button(
            text=text,
            font_size=dp(16),
            bold=True,
            background_normal="",
            background_color=(0.10, 0.42, 0.84, 1),
        )

    def set_status(self, text, error=False):
        def update(_dt):
            self.status.text = text
            self.status.color = (1, 0.45, 0.45, 1) if error else (0.65, 0.92, 0.72, 1)

        Clock.schedule_once(update)

    def clear_all(self, *_):
        self.url_input.text = ""
        self.preview.texture = None
        self.caption_box.text = ""
        self.media_items = []
        self.caption = ""
        self.save_media_btn.disabled = True
        self.save_caption_btn.disabled = True
        self.set_status("Form dibersihkan.")

    def fetch_post(self, *_):
        if self.busy:
            return

        url = self.url_input.text.strip()
        if not is_instagram_url(url):
            self.set_status("Masukkan link Instagram yang valid.", True)
            return

        self.busy = True
        self.media_items = []
        self.save_media_btn.disabled = True
        self.save_caption_btn.disabled = True
        self.set_status("Mengambil posting langsung dari Instagram...")
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url):
        try:
            data = extract_instagram(url)
            Clock.schedule_once(lambda _dt: self._apply_result(data))
        except Exception as exc:
            self.set_status(str(exc), True)
        finally:
            self.busy = False

    def _apply_result(self, data):
        self.media_items = data.get("items") or []
        self.caption = data.get("caption") or ""
        self.caption_box.text = self.caption or "Tidak ada caption yang dapat dibaca."
        self.save_media_btn.disabled = not bool(self.media_items)
        self.save_caption_btn.disabled = not bool(self.caption.strip())

        count = len(self.media_items)
        source = data.get("source", "lokal")
        self.status.text = f"Berhasil: {count} media ditemukan ({source})."
        self.status.color = (0.65, 0.92, 0.72, 1)

        thumbnail = data.get("thumbnail") or first_text(
            self.media_items[0].get("thumbnail") if self.media_items else ""
        )
        if thumbnail:
            threading.Thread(target=self._load_preview_worker, args=(thumbnail,), daemon=True).start()

    def _load_preview_worker(self, url):
        try:
            r = requests.get(url, timeout=30, verify=certifi.where(), headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            from io import BytesIO

            payload = BytesIO(r.content)
            ext = "png" if "png" in r.headers.get("content-type", "") else "jpg"

            def apply(_dt):
                try:
                    self.preview.texture = CoreImage(payload, ext=ext).texture
                except Exception:
                    pass

            Clock.schedule_once(apply)
        except Exception:
            pass

    def save_media(self, *_):
        if not self.media_items:
            self.set_status("Belum ada media untuk disimpan.", True)
            return
        if self.busy:
            return

        self.busy = True
        self.save_media_btn.disabled = True
        self.set_status(f"Mengunduh {len(self.media_items)} media...")
        threading.Thread(target=self._save_media_worker, daemon=True).start()

    def _save_media_worker(self):
        saved = 0
        try:
            for index, item in enumerate(self.media_items, start=1):
                url = item.get("url") or ""
                if not url:
                    continue

                r = requests.get(
                    url,
                    timeout=90,
                    stream=True,
                    verify=certifi.where(),
                    headers={"User-Agent": USER_AGENT, "Referer": "https://www.instagram.com/"},
                )
                r.raise_for_status()

                content_type = (r.headers.get("content-type") or "").split(";")[0].strip()
                ext = self._choose_extension(item, content_type)
                filename = f"IGSaver_{self._safe_stamp()}_{index:02d}{ext}"

                if platform == "android":
                    self._save_response_android(r, filename, content_type or self._mime_for_ext(ext))
                else:
                    folder = Path.home() / "Downloads" / "IGSaver"
                    folder.mkdir(parents=True, exist_ok=True)
                    with (folder / filename).open("wb") as f:
                        for chunk in r.iter_content(256 * 1024):
                            if chunk:
                                f.write(chunk)
                saved += 1

            if saved:
                self.set_status(f"Selesai. {saved} media tersimpan di Download/IGSaver.")
            else:
                self.set_status("Tidak ada media yang berhasil disimpan.", True)
        except Exception as exc:
            self.set_status(f"Gagal menyimpan media: {exc}", True)
        finally:
            self.busy = False
            Clock.schedule_once(lambda _dt: setattr(self.save_media_btn, "disabled", not bool(self.media_items)))

    def save_caption(self, *_):
        if not self.caption.strip():
            self.set_status("Tidak ada caption.", True)
            return
        try:
            filename = f"IGSaver_{self._safe_stamp()}_caption.txt"
            data = self.caption.encode("utf-8")
            if platform == "android":
                self._save_bytes_android(data, filename, "text/plain")
            else:
                folder = Path.home() / "Downloads" / "IGSaver"
                folder.mkdir(parents=True, exist_ok=True)
                (folder / filename).write_bytes(data)
            self.set_status("Caption tersimpan di Download/IGSaver.")
        except Exception as exc:
            self.set_status(f"Gagal menyimpan caption: {exc}", True)

    def _save_response_android(self, response, filename: str, mime_type: str):
        api_level = self._android_api_level()
        if api_level >= 29:
            resolver, uri, output = self._open_mediastore_output(filename, mime_type)
            try:
                for chunk in response.iter_content(256 * 1024):
                    if chunk:
                        output.write(chunk)
                output.flush()
            finally:
                output.close()
            self._finish_mediastore(resolver, uri)
            return

        folder = Path("/storage/emulated/0/Download/IGSaver")
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / filename).open("wb") as f:
            for chunk in response.iter_content(256 * 1024):
                if chunk:
                    f.write(chunk)

    def _save_bytes_android(self, data: bytes, filename: str, mime_type: str):
        api_level = self._android_api_level()
        if api_level >= 29:
            resolver, uri, output = self._open_mediastore_output(filename, mime_type)
            try:
                output.write(data)
                output.flush()
            finally:
                output.close()
            self._finish_mediastore(resolver, uri)
            return

        folder = Path("/storage/emulated/0/Download/IGSaver")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_bytes(data)

    @staticmethod
    def _android_api_level() -> int:
        if platform != "android":
            return 0
        try:
            from jnius import autoclass
            return int(autoclass("android.os.Build$VERSION").SDK_INT)
        except Exception:
            return 29

    @staticmethod
    def _open_mediastore_output(filename: str, mime_type: str):
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ContentValues = autoclass("android.content.ContentValues")
        MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
        MediaStoreMediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        Environment = autoclass("android.os.Environment")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        values = ContentValues()
        values.put(MediaStoreMediaColumns.DISPLAY_NAME, filename)
        values.put(MediaStoreMediaColumns.MIME_TYPE, mime_type)
        values.put(
            MediaStoreMediaColumns.RELATIVE_PATH,
            Environment.DIRECTORY_DOWNLOADS + "/IGSaver",
        )
        values.put(MediaStoreMediaColumns.IS_PENDING, 1)

        uri = resolver.insert(MediaStoreDownloads.EXTERNAL_CONTENT_URI, values)
        if uri is None:
            raise RuntimeError("Android MediaStore gagal membuat file.")
        output = resolver.openOutputStream(uri)
        if output is None:
            resolver.delete(uri, None, None)
            raise RuntimeError("Android tidak dapat membuka file tujuan.")
        return resolver, uri, output

    @staticmethod
    def _finish_mediastore(resolver, uri):
        from jnius import autoclass

        ContentValues = autoclass("android.content.ContentValues")
        MediaStoreMediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        values = ContentValues()
        values.put(MediaStoreMediaColumns.IS_PENDING, 0)
        resolver.update(uri, values, None, None)

    @staticmethod
    def _request_legacy_storage_if_needed():
        try:
            from jnius import autoclass
            if int(autoclass("android.os.Build$VERSION").SDK_INT) >= 29:
                return
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        except Exception:
            pass

    @staticmethod
    def _choose_extension(item: dict, content_type: str) -> str:
        guessed = mimetypes.guess_extension(content_type) if content_type else None
        if guessed == ".jpe":
            guessed = ".jpg"
        if guessed and guessed in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".m4v"}:
            return guessed

        ext = str(item.get("ext") or "").lower().lstrip(".")
        if ext in {"jpg", "jpeg", "png", "webp", "mp4", "m4v"}:
            return "." + ext
        return ".mp4" if item.get("type") == "video" else ".jpg"

    @staticmethod
    def _mime_for_ext(ext: str) -> str:
        return mimetypes.types_map.get(ext.lower(), "application/octet-stream")

    @staticmethod
    def _safe_stamp():
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    IGSaverApp().run()
