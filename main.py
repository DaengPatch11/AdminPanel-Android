import requests
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# --- KONFIGURASI URL API ---
BASE_URL = "http://203.194.112.67/admin"
API_GET = f"{BASE_URL}/get_users.php"
API_SAVE = f"{BASE_URL}/add_user_api.php"
API_DELETE = f"{BASE_URL}/delete_user.php"

class UserCard(BoxLayout):
    """Widget untuk menampilkan satu baris data user sebagai kartu"""
    def __init__(self, user_data, refresh_callback, edit_callback, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=200, padding=10, **kwargs)
        self.user_data = user_data
        self.refresh_callback = refresh_callback
        
        # Info Text
        uid = user_data.get('user_id', '-')
        status = user_data.get('status', 'Offline')
        expire = user_data.get('expire_date', '-')
        hwid = user_data.get('hwid', '-')
        
        info_label = Label(
            text=f"[b]ID:[/b] {uid} | [b]Status:[/b] {status}\n[b]HWID:[/b] {hwid}\n[b]Expire:[/b] {expire}",
            markup=True, halign='left', valign='middle'
        )
        info_label.bind(size=info_label.setter('text_size'))
        self.add_widget(info_label)

        # Tombol Aksi (Edit & Hapus)
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        btn_edit = Button(text="EDIT", background_color=(1, 0.6, 0, 1))
        btn_edit.bind(on_press=lambda x: edit_callback(self.user_data))
        
        btn_del = Button(text="HAPUS", background_color=(1, 0, 0, 1))
        btn_del.bind(on_press=self.confirm_delete)
        
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        self.add_widget(btn_layout)

    def confirm_delete(self, instance):
        uid = self.user_data.get('user_id')
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f"Hapus user {uid}?"))
        
        btns = BoxLayout(spacing=10, size_hint_y=None, height=40)
        yes_btn = Button(text="Ya")
        no_btn = Button(text="Batal")
        btns.addWidget(yes_btn)
        btns.addWidget(no_btn)
        content.add_widget(btns)

        popup = Popup(title="Konfirmasi", content=content, size_hint=(0.8, 0.4))
        no_btn.bind(on_press=popup.dismiss)
        yes_btn.bind(on_press=lambda x: self.do_delete(uid, popup))
        popup.open()

    def do_delete(self, uid, popup):
        try:
            requests.post(API_DELETE, json={"user_id": uid}, timeout=10)
            popup.dismiss()
            self.refresh_callback()
        except Exception as e:
            print(e)

class AdminPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.padding = 10
        self.spacing = 10

        # Header
        header = BoxLayout(size_hint_y=None, height=60, spacing=10)
        header.add_widget(Label(text="ADMIN DATABASE", font_size='20sp', color=(0, 1, 0.5, 1)))
        
        btn_add = Button(text="+ USER", size_hint_x=None, width=100, background_color=(0, 0.8, 0.4, 1))
        btn_add.bind(on_press=lambda x: self.open_form())
        header.add_widget(btn_add)
        self.add_widget(header)

        # Body (List User)
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=15, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.add_widget(self.scroll)

        # Footer Refresh
        btn_ref = Button(text="REFRESH DATABASE", size_hint_y=None, height=50)
        btn_ref.bind(on_press=lambda x: self.load_data())
        self.add_widget(btn_ref)

        Clock.schedule_once(lambda dt: self.load_data())

    def load_data(self):
        self.grid.clear_widgets()
        try:
            res = requests.get(API_GET, timeout=10)
            users = res.json()
            for u in users:
                self.grid.add_widget(UserCard(u, self.load_data, self.open_form))
        except Exception as e:
            self.grid.add_widget(Label(text=f"Error: {e}"))

    def open_form(self, data=None):
        is_edit = True if data else False
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        uid_input = TextInput(text=str(data.get('user_id','')) if is_edit else '', multiline=False, hint_text="User ID", readonly=is_edit)
        hwid_input = TextInput(text=str(data.get('hwid','')) if is_edit else '', multiline=False, hint_text="HWID")
        exp_input = TextInput(text=str(data.get('expire_date','')) if is_edit else '2025-01-01', multiline=False, hint_text="YYYY-MM-DD")
        msg_input = TextInput(text=str(data.get('footer_message','')) if is_edit else 'Welcome', multiline=False, hint_text="Message")

        for w in [uid_input, hwid_input, exp_input, msg_input]: content.add_widget(w)

        btn_save = Button(text="SIMPAN", size_hint_y=None, height=50, background_color=(0, 0.7, 1, 1))
        content.add_widget(btn_save)

        popup = Popup(title="User Form", content=content, size_hint=(0.9, 0.8))
        
        def save_action(instance):
            payload = {
                "user_id": uid_input.text,
                "hwid": hwid_input.text,
                "expire_date": exp_input.text,
                "footer_message": msg_input.text
            }
            try:
                requests.post(API_SAVE, json=payload, timeout=10)
                popup.dismiss()
                self.load_data()
            except Exception as e:
                print(e)

        btn_save.bind(on_press=save_action)
        popup.open()

class AdminApp(App):
    def build(self):
        return AdminPanel()

if __name__ == '__main__':
    AdminApp().run()