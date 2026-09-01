import threading
import requests
import json
import re
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from io import BytesIO

class IGSaverApp(App):
    def build(self):
        self.title = "IGSaver"
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Header
        header = Label(text="IGSaver - Simpan Posting", font_size='20sp', bold=True, size_hint_y=None, height=40)
        main_layout.add_widget(header)
        
        # Input Link
        self.link_input = TextInput(hint_text="Tempel link postingan Instagram di sini...", multiline=False, size_hint_y=None, height=45)
        main_layout.add_widget(self.link_input)
        
        # Tombol Aksi
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=45)
        self.download_btn = Button(text="Download", on_press=self.start_fetch_thread)
        clear_btn = Button(text="Bersihkan", on_press=self.clear_fields)
        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(self.download_btn)
        main_layout.add_widget(btn_layout)
        
        # Status Label
        self.status_label = Label(text="Masukkan link untuk memulai...", size_hint_y=None, height=30)
        main_layout.add_widget(self.status_label)
        
        # Area Preview Gambar
        self.image_preview = Image(source='', allow_stretch=True, keep_ratio=True)
        main_layout.add_widget(self.image_preview)
        
        # Caption Area
        self.caption_input = TextInput(hint_text="Caption akan tampil di sini...", multiline=True, readonly=True)
        main_layout.add_widget(self.caption_input)
        
        return main_layout

    def clear_fields(self, instance):
        self.link_input.text = ""
        self.caption_input.text = ""
        self.status_label.text = "Bersih."
        self.image_preview.texture = None

    def update_ui_success(self, image_data, caption_text):
        def _update(dt):
            self.download_btn.disabled = False
            self.status_label.text = "Berhasil mengambil data!"
            self.caption_input.text = caption_text if caption_text else "Tidak ada caption."
            
            if image_data:
                try:
                    buf = BytesIO(image_data)
                    cim = CoreImage(buf, ext='jpg')
                    self.image_preview.texture = cim.texture
                except Exception as e:
                    self.status_label.text = f"Gagal memuat gambar: {str(e)}"

        Clock.schedule_once(_update)

    def update_ui_error(self, error_msg):
        def _update(dt):
            self.download_btn.disabled = False
            self.status_label.text = f"Error: {error_msg}"
        Clock.schedule_once(_update)

    def start_fetch_thread(self, instance):
        url = self.link_input.text.strip()
        if not url:
            self.status_label.text = "Harap masukkan URL!"
            return
        
        self.download_btn.disabled = True
        self.status_label.text = "Mengambil data postingan..."
        
        threading.Thread(target=self.fetch_instagram_data, args=(url,), daemon=True).start()

    def fetch_instagram_data(self, url):
        try:
            match = re.search(r'/(?:p|reel)/([^/?#&]+)', url)
            if not match:
                self.update_ui_error("URL Instagram tidak valid.")
                return
            
            shortcode = match.group(1)
            
            # 1. Metodologi API Android resmi dengan App-ID
            api_url = f"https://i.instagram.com/api/v1/media/{shortcode}/info/"
            headers = {
                'User-Agent': 'Instagram 275.0.0.27.98 Android (30/11; 320dpi; 720x1280; Xiaomi; Redmi 9A; dandelion; mt6762; in_ID; 458229447)',
                'X-IG-App-ID': '936619743392459',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if items:
                    item = items[0]
                    img_url = None
                    if 'image_versions2' in item:
                        img_url = item['image_versions2']['candidates'][0]['url']
                    
                    caption = ""
                    if 'caption' in item and item['caption']:
                        caption = item['caption'].get('text', '')

                    if img_url:
                        img_resp = requests.get(img_url, timeout=10)
                        if img_resp.status_code == 200:
                            self.update_ui_success(img_resp.content, caption)
                            return

            # 2. Fallback jika API dibatasi (Parsing Meta OpenGraph)
            web_url = f"https://www.instagram.com/p/{shortcode}/"
            web_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            web_resp = requests.get(web_url, headers=web_headers, timeout=10)
            if web_resp.status_code == 200:
                img_match = re.search(r'<meta property="og:image" content="([^"]+)"', web_resp.text)
                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', web_resp.text)
                
                if img_match:
                    img_url = img_match.group(1).replace('&amp;', '&')
                    caption = desc_match.group(1) if desc_match else ""
                    
                    img_resp = requests.get(img_url, timeout=10)
                    if img_resp.status_code == 200:
                        self.update_ui_success(img_resp.content, caption)
                        return

            self.update_ui_error("Gagal mengambil data dari Instagram.")

        except Exception as e:
            self.update_ui_error(f"Gagal: {str(e)}")

if __name__ == '__main__':
    IGSaverApp().run()
