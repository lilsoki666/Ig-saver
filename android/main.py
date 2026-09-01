import os
import threading
import requests
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


# GANTI setelah backend selesai dibuat
API_URL = "https://YOUR-BACKEND-URL"

class IGSaverLayout(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10),
            **kwargs
        )

        title = Label(
            text="[b]IGSaver - Simpan Posting[/b]",
            markup=True,
            font_size=dp(25),
            size_hint_y=None,
            height=dp(50)
        )
        self.add_widget(title)

        self.url_input = TextInput(
            hint_text="Tempel URL Instagram di sini",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )
        self.add_widget(self.url_input)

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(10)
        )

        clear_btn = Button(text="Bersihkan")
        fetch_btn = Button(text="Ambil Posting")

        clear_btn.bind(on_release=self.clear)
        fetch_btn.bind(on_release=self.fetch)

        buttons.add_widget(clear_btn)
        buttons.add_widget(fetch_btn)

        self.add_widget(buttons)

        self.status = Label(
            text="Siap.",
            size_hint_y=None,
            height=dp(45),
            halign="left",
            valign="middle"
        )

        self.status.bind(
            size=lambda obj, value:
            setattr(obj, "text_size", value)
        )

        self.add_widget(self.status)

        self.preview = AsyncImage(
            source="",
            size_hint_y=0.50,
            allow_stretch=True,
            keep_ratio=True
        )

        self.add_widget(self.preview)

        self.caption = TextInput(
            hint_text="Caption akan tampil di sini...",
            readonly=True,
            multiline=True,
            size_hint_y=0.30
        )

        self.add_widget(self.caption)

        save_btn = Button(
            text="Simpan ke HP",
            size_hint_y=None,
            height=dp(52),
            disabled=True
        )

        save_btn.bind(on_release=self.save_media)

        self.save_button = save_btn
        self.add_widget(save_btn)

        self.post_data = None

    def set_status(self, text):

        Clock.schedule_once(
            lambda dt:
            setattr(self.status, "text", text)
        )

    def clear(self, *args):

        self.url_input.text = ""
        self.preview.source = ""
        self.caption.text = ""
        self.status.text = "Siap."

        self.post_data = None
        self.save_button.disabled = True

    def fetch(self, *args):

        url = self.url_input.text.strip()

        if "instagram.com/" not in url:

            self.set_status(
                "Masukkan URL Instagram yang benar."
            )

            return

        self.save_button.disabled = True

        self.set_status(
            "Mengambil posting..."
        )

        threading.Thread(
            target=self.fetch_thread,
            args=(url,),
            daemon=True
        ).start()

    def fetch_thread(self, url):

        try:

            response = requests.post(
                API_URL.rstrip("/") + "/api/fetch",
                json={"url": url},
                timeout=90
            )

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):

                raise Exception(
                    data.get(
                        "error",
                        "Posting tidak dapat diproses."
                    )
                )

            Clock.schedule_once(
                lambda dt:
                self.show_result(data)
            )

        except Exception as e:

            self.set_status(
                "Gagal: " + str(e)
            )

    def show_result(self, data):

        self.post_data = data

        caption = data.get(
            "caption",
            ""
        )

        self.caption.text = (
            caption
            if caption
            else "Tidak ada caption."
        )

        media = data.get(
            "media",
            []
        )

        if media:

            self.preview.source = media[0]["url"]

            self.save_button.disabled = False

            self.set_status(
                "Posting berhasil ditemukan."
            )

        else:

            self.set_status(
                "Posting ditemukan tetapi media tidak tersedia."
            )

    def save_media(self, *args):

        if not self.post_data:
            return

        threading.Thread(
            target=self.save_thread,
            daemon=True
        ).start()

    def save_thread(self):

        media = self.post_data.get(
            "media",
            []
        )

        caption = self.post_data.get(
            "caption",
            ""
        )

        if not media:

            self.set_status(
                "Tidak ada media."
            )

            return

        folder = os.path.join(
            os.path.expanduser("~"),
            "Download",
            "IGSaver"
        )

        os.makedirs(
            folder,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        saved = 0

        for index, item in enumerate(media, 1):

            try:

                url = item.get("url")

                response = requests.get(
                    url,
                    stream=True,
                    timeout=90,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    }
                )

                response.raise_for_status()

                content_type = (
                    response.headers
                    .get("Content-Type", "")
                    .lower()
                )

                extension = (
                    ".mp4"
                    if "video" in content_type
                    else ".jpg"
                )

                filename = (
                    f"instagram_{timestamp}_{index}"
                    f"{extension}"
                )

                path = os.path.join(
                    folder,
                    filename
                )

                with open(
                    path,
                    "wb"
                ) as file:

                    for chunk in response.iter_content(
                        262144
                    ):

                        if chunk:
                            file.write(chunk)

                saved += 1

            except Exception:
                continue

        if caption:

            caption_path = os.path.join(
                folder,
                f"instagram_{timestamp}_caption.txt"
            )

            with open(
                caption_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(caption)

        self.set_status(
            f"{saved} media berhasil disimpan."
        )


class IGSaverApp(App):

    title = "IGSaver"

    def build(self):

        return IGSaverLayout()


if __name__ == "__main__":
    IGSaverApp().run()
