import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.resources import resource_add_path
from plyer import filechooser

# Daftarkan direktori 'assets' agar file gambar selalu terdeteksi di Android
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
resource_add_path(os.path.join(BASE_DIR, 'assets'))

class MainWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # Preview area starts empty; no external icon asset is required.
        self.img_display = Image(allow_stretch=True)
        self.add_widget(self.img_display)

        # Tombol untuk memilih foto
        self.btn_select = Button(
            text='Pilih Foto dari Galeri',
            size_hint=(1, 0.15)
        )
        self.btn_select.bind(on_press=self.open_gallery)
        self.add_widget(self.btn_select)

        # Minta izin media Android saat tampilan utama dibuat
        self.request_permissions()

    def request_permissions(self):
        """Meminta izin akses penyimpanan dan media secara runtime di Android"""
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES
            ])

    def open_gallery(self, instance):
        """Membuka galeri/file picker"""
        filechooser.open_file(
            on_selection=self.on_file_selected,
            filters=['*.png', '*.jpg', '*.jpeg']
        )

    def on_file_selected(self, selection):
        """Callback ketika pengguna memilih gambar dari galeri"""
        if selection and len(selection) > 0:
            selected_path = selection[0]
            if os.path.exists(selected_path):
                self.img_display.source = selected_path
                self.img_display.reload()

class IGSaverApp(App):
    def build(self):
        return MainWidget()

if __name__ == '__main__':
    IGSaverApp().run()
