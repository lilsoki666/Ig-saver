import re
import threading
from html import unescape
from io import BytesIO
from urllib.parse import urljoin

import certifi
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

APP_UA = (
    "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
)


def extract_instagram_url(raw_url):
    """Return a normalized Instagram post/reel URL and shortcode."""
    raw_url = raw_url.strip()
    if not re.match(r"^https?://", raw_url, re.I):
        raw_url = "https://" + raw_url

    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)",
        raw_url,
        re.I,
    )
    if not match:
        return None, None, None

    shortcode = match.group(1)
    kind_match = re.search(r"instagram\.com/(p|reel|tv)/", raw_url, re.I)
    kind = kind_match.group(1).lower() if kind_match else "p"
    normalized = f"https://www.instagram.com/{kind}/{shortcode}/"
    return normalized, shortcode, kind


def meta_content(html, property_name):
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{re.escape(property_name)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']*)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I)
        if match:
            return unescape(match.group(1)).replace("&quot;", '"')
    return ""


def extract_caption(html):
    # Open Graph description is the most stable public caption source.
    caption = meta_content(html, "og:description")
    if caption:
        # Instagram often formats this as: "... on Instagram: \"caption\""
        quoted = re.search(r'Instagram:\s*["\'](.+?)["\']\s*$', caption, re.S)
        if quoted:
            return quoted.group(1).strip()
        return caption.strip()

    # Fallback to common JSON fields embedded in the public page.
    for key in ("edge_media_to_caption", "caption"):
        match = re.search(
            rf'"{re.escape(key)}"\s*:\s*\{{.*?"text"\s*:\s*"((?:\\.|[^"\\])*)"',
            html,
            re.S,
        )
        if match:
            value = match.group(1)
            try:
                return bytes(value, "utf-8").decode("unicode_escape")
            except Exception:
                return value.replace("\\n", "\n").replace('\\"', '"')
    return ""


class IGSaverApp(App):
    def build(self):
        self.title = "IGSaver - Simpan Posting"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": APP_UA,
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Cache-Control": "no-cache",
            }
        )

        main_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)
        header = Label(
            text="IGSaver - Simpan Posting",
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=40,
        )
        main_layout.add_widget(header)

        self.link_input = TextInput(
            hint_text="Tempel link postingan Instagram di sini...",
            multiline=False,
            size_hint_y=None,
            height=45,
        )
        main_layout.add_widget(self.link_input)

        btn_layout = BoxLayout(
            orientation="horizontal", spacing=10, size_hint_y=None, height=45
        )
        clear_btn = Button(text="Bersihkan", on_press=self.clear_fields)
        self.download_btn = Button(text="Ambil Posting", on_press=self.start_fetch_thread)
        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(self.download_btn)
        main_layout.add_widget(btn_layout)

        self.status_label = Label(
            text="Tempel link posting publik untuk memulai.",
            size_hint_y=None,
            height=45,
        )
        main_layout.add_widget(self.status_label)

        self.image_preview = Image(source="", allow_stretch=True, keep_ratio=True)
        main_layout.add_widget(self.image_preview)

        self.caption_input = TextInput(
            hint_text="Caption akan tampil di sini...",
            multiline=True,
            readonly=True,
        )
        main_layout.add_widget(self.caption_input)
        return main_layout

    def clear_fields(self, instance):
        self.link_input.text = ""
        self.caption_input.text = ""
        self.status_label.text = "Bersih."
        self.image_preview.texture = None

    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", text))

    def update_ui_success(self, media_data, caption_text):
        def _update(dt):
            self.download_btn.disabled = False
            self.status_label.text = "Berhasil mengambil posting publik."
            self.caption_input.text = caption_text or "Tidak ada caption yang dapat dibaca."
            if media_data:
                try:
                    buf = BytesIO(media_data)
                    self.image_preview.texture = CoreImage(buf, ext="jpg").texture
                except Exception as exc:
                    self.status_label.text = f"Media berhasil diambil, preview gagal: {exc}"

        Clock.schedule_once(_update)

    def update_ui_error(self, error_msg):
        def _update(dt):
            self.download_btn.disabled = False
            self.status_label.text = f"Error: {error_msg}"

        Clock.schedule_once(_update)

    def start_fetch_thread(self, instance):
        url = self.link_input.text.strip()
        if not url:
            self.status_label.text = "Harap masukkan URL Instagram."
            return

        normalized, shortcode, kind = extract_instagram_url(url)
        if not normalized:
            self.status_label.text = "URL Instagram tidak valid."
            return

        self.download_btn.disabled = True
        self.status_label.text = "Membaca posting publik..."
        threading.Thread(
            target=self.fetch_instagram_data,
            args=(normalized, shortcode, kind),
            daemon=True,
        ).start()

    def fetch_instagram_data(self, normalized_url, shortcode, kind):
        try:
            # We intentionally do NOT require an Instagram session/cookie.
            # Public embed HTML is the least-privileged route available to a
            # standalone client. Instagram may still rate-limit or block it.
            embed_urls = [
                f"https://www.instagram.com/{kind}/{shortcode}/embed/captioned/",
                f"https://www.instagram.com/{kind}/{shortcode}/embed/",
                normalized_url,
            ]

            last_status = None
            html = ""
            for url in embed_urls:
                try:
                    response = self.session.get(
                        url,
                        timeout=25,
                        verify=certifi.where(),
                        allow_redirects=True,
                    )
                    last_status = response.status_code
                    if response.status_code == 200 and response.text:
                        html = response.text
                        break
                except requests.RequestException as exc:
                    last_status = str(exc)

            if not html:
                if last_status == 403:
                    self.update_ui_error(
                        "Instagram menolak akses publik (HTTP 403). "
                        "Posting mungkin privat, dibatasi umur/wilayah, atau sedang rate-limit. "
                        "Aplikasi tidak lagi meminta Session ID."
                    )
                elif last_status == 404:
                    self.update_ui_error("Posting tidak ditemukan (HTTP 404).")
                else:
                    self.update_ui_error(f"Gagal membaca posting. Respons: {last_status}")
                return

            image_url = meta_content(html, "og:image")
            video_url = meta_content(html, "og:video")
            caption = extract_caption(html)

            # Preview the video thumbnail when available. Actual video saving
            # can be added separately; do not pretend a video URL is an image.
            preview_url = image_url
            if not preview_url:
                self.update_ui_success(None, caption)
                return

            media_response = self.session.get(
                urljoin(normalized_url, preview_url),
                timeout=30,
                verify=certifi.where(),
            )
            if media_response.status_code != 200:
                self.update_ui_success(None, caption)
                return

            self.update_ui_success(media_response.content, caption)

        except requests.RequestException as exc:
            self.update_ui_error(f"Gagal koneksi: {exc}")
        except Exception as exc:
            self.update_ui_error(f"Terjadi kesalahan: {exc}")


if __name__ == "__main__":
    IGSaverApp().run()
