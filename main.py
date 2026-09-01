import json
import re
import threading
from html import unescape
from html.parser import HTMLParser
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


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.images = []
        self.links = []
        self.in_title = False
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "meta":
            key = attrs.get("property") or attrs.get("name")
            value = attrs.get("content")
            if key and value:
                self.meta[key.lower()] = unescape(value)
        elif tag.lower() == "img":
            src = attrs.get("src")
            if src:
                self.images.append(unescape(src))
        elif tag.lower() == "a":
            href = attrs.get("href")
            if href:
                self.links.append(unescape(href))
        elif tag.lower() == "title":
            self.in_title = True

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    @property
    def title(self):
        return " ".join(self.title_parts).strip()


def extract_instagram_url(raw_url):
    raw_url = raw_url.strip()
    if not re.match(r"^https?://", raw_url, re.I):
        raw_url = "https://" + raw_url
    match = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", raw_url, re.I)
    if not match:
        return None, None, None
    shortcode = match.group(1)
    kind_match = re.search(r"instagram\.com/(p|reel|tv)/", raw_url, re.I)
    kind = kind_match.group(1).lower() if kind_match else "p"
    normalized = f"https://www.instagram.com/{kind}/{shortcode}/"
    return normalized, shortcode, kind


def clean_caption(value):
    if not value:
        return ""
    value = unescape(value)
    value = value.replace("\\n", "\n").replace("\\r", "\r").replace('\\"', '"')
    value = re.sub(r"^.*?\s+on Instagram:\s*", "", value, flags=re.I | re.S)
    value = value.strip().strip('"').strip("'")
    return value.strip()


def parse_html_data(html):
    parser = MetaParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    meta = parser.meta
    image_url = meta.get("og:image", "")
    video_url = meta.get("og:video", "")
    caption = clean_caption(meta.get("og:description", ""))

    # JSON-LD is often available even when the normal OG description is not.
    for match in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        try:
            data = json.loads(unescape(match))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not image_url and isinstance(item.get("image"), str):
                    image_url = item["image"]
                if not caption and isinstance(item.get("description"), str):
                    caption = clean_caption(item["description"])
        except Exception:
            continue

    # Instagram's embedded JSON has changed names several times. Look for
    # common caption/media fields without assuming one exact page structure.
    if not caption:
        patterns = [
            r'"edge_media_to_caption"\s*:\s*\{.*?"text"\s*:\s*"((?:\\.|[^"\\])*)"',
            r'"caption"\s*:\s*\{.*?"text"\s*:\s*"((?:\\.|[^"\\])*)"',
            r'"caption"\s*:\s*"((?:\\.|[^"\\])*)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.I | re.S)
            if m:
                try:
                    caption = clean_caption(json.loads('"' + m.group(1) + '"'))
                except Exception:
                    caption = clean_caption(m.group(1))
                if caption:
                    break

    if not image_url:
        for src in parser.images:
            low = src.lower()
            if ("cdninstagram" in low or "fbcdn.net" in low) and re.search(r"\.(?:jpg|jpeg|png|webp)(?:[?&]|$)", low):
                image_url = src
                break

    return image_url, video_url, caption, parser.title


class IGSaverApp(App):
    def build(self):
        self.title = "IGSaver - Simpan Posting"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": APP_UA,
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )

        main_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)
        header = Label(text="IGSaver - Simpan Posting", font_size="20sp", bold=True,
                       size_hint_y=None, height=40)
        main_layout.add_widget(header)

        self.link_input = TextInput(
            hint_text="Tempel link postingan Instagram di sini...",
            multiline=False, size_hint_y=None, height=45,
        )
        main_layout.add_widget(self.link_input)

        btn_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=45)
        clear_btn = Button(text="Bersihkan", on_press=self.clear_fields)
        self.download_btn = Button(text="Ambil Posting", on_press=self.start_fetch_thread)
        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(self.download_btn)
        main_layout.add_widget(btn_layout)

        self.status_label = Label(text="Tempel link posting publik untuk memulai.", size_hint_y=None, height=45)
        main_layout.add_widget(self.status_label)

        self.image_preview = Image(source="", allow_stretch=True, keep_ratio=True)
        main_layout.add_widget(self.image_preview)

        self.caption_input = TextInput(hint_text="Caption akan tampil di sini...", multiline=True, readonly=True)
        main_layout.add_widget(self.caption_input)
        return main_layout

    def clear_fields(self, instance):
        self.link_input.text = ""
        self.caption_input.text = ""
        self.status_label.text = "Bersih."
        self.image_preview.texture = None

    def update_ui_success(self, media_data, caption_text, media_type="image"):
        def _update(dt):
            self.download_btn.disabled = False
            self.status_label.text = "Berhasil mengambil posting publik."
            self.caption_input.text = caption_text or "Tidak ada caption yang dapat dibaca."
            self.image_preview.texture = None
            if media_data:
                try:
                    self.image_preview.texture = CoreImage(BytesIO(media_data), ext="jpg").texture
                except Exception as exc:
                    self.status_label.text = f"Media ditemukan, preview gagal: {exc}"
            elif media_type == "video":
                self.status_label.text = "Posting video ditemukan. Thumbnail tidak dapat ditampilkan."
            else:
                self.status_label.text = "Posting ditemukan, tetapi gambar tidak tersedia dari sumber publik."
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
        threading.Thread(target=self.fetch_instagram_data,
                         args=(normalized, shortcode, kind), daemon=True).start()

    def fetch_instagram_data(self, normalized_url, shortcode, kind):
        try:
            # 1) Official oEmbed: gives a public thumbnail and title/caption
            # without asking the user for a Session ID.
            oembed_url = "https://api.instagram.com/oembed/"
            oembed_params = {"url": normalized_url, "omitscript": "true", "maxwidth": "1080"}
            try:
                r = self.session.get(oembed_url, params=oembed_params, timeout=20,
                                     verify=certifi.where(), allow_redirects=True)
                if r.status_code == 200:
                    data = r.json()
                    thumb = data.get("thumbnail_url", "")
                    title = clean_caption(data.get("title", ""))
                    if thumb:
                        media = self.session.get(
                            thumb, headers={"Referer": normalized_url, "User-Agent": APP_UA},
                            timeout=30, verify=certifi.where(), allow_redirects=True,
                        )
                        if media.status_code == 200 and media.content:
                            self.update_ui_success(media.content, title, "video" if kind == "reel" else "image")
                            return
                    if title:
                        self.update_ui_success(None, title, "video" if kind == "reel" else "image")
                        return
            except (requests.RequestException, ValueError):
                pass

            # 2) Public embed pages. Try captioned first because it tends to
            # contain both media metadata and visible caption information.
            urls = [
                f"https://www.instagram.com/{kind}/{shortcode}/embed/captioned/",
                f"https://www.instagram.com/{kind}/{shortcode}/embed/",
                normalized_url,
            ]
            last_status = None
            for url in urls:
                try:
                    response = self.session.get(
                        url,
                        headers={"Referer": "https://www.instagram.com/", "User-Agent": APP_UA},
                        timeout=25, verify=certifi.where(), allow_redirects=True,
                    )
                    last_status = response.status_code
                    if response.status_code != 200 or not response.text:
                        continue

                    html = response.text
                    image_url, video_url, caption, page_title = parse_html_data(html)
                    caption = caption or page_title
                    if not image_url and not caption and not video_url:
                        # A 200 response can still be a login/challenge page.
                        continue

                    if image_url:
                        media_response = self.session.get(
                            image_url,
                            headers={"Referer": normalized_url, "User-Agent": APP_UA},
                            timeout=30, verify=certifi.where(), allow_redirects=True,
                        )
                        if media_response.status_code == 200 and media_response.content:
                            self.update_ui_success(media_response.content, caption, "video" if video_url else "image")
                            return

                    self.update_ui_success(None, caption, "video" if video_url else "image")
                    return
                except requests.RequestException:
                    continue

            if last_status == 403:
                self.update_ui_error("Instagram menolak akses publik (HTTP 403). Coba link posting publik lain.")
            elif last_status == 404:
                self.update_ui_error("Posting tidak ditemukan (HTTP 404).")
            else:
                self.update_ui_error("Data posting tidak berhasil ditemukan. Instagram mungkin mengubah halaman publiknya atau membatasi akses.")
        except requests.RequestException as exc:
            self.update_ui_error(f"Gagal koneksi: {exc}")
        except Exception as exc:
            self.update_ui_error(f"Terjadi kesalahan: {exc}")


if __name__ == "__main__":
    IGSaverApp().run()
