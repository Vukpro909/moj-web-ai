import json
import urllib.request
import threading
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"
KEY_FILE = "groq_key.txt"

class ChatApp(App):
    def build(self):
        self.title = "Google UI Chat"
        self.history = [{"role": "system", "content": "Odgovaraj kratko na srpskom."}]
        
        # Glavni kontejner (Taman režim)
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        Window.clearcolor = get_color_from_hex("#131314")
        
        # Naslov na vrhu
        header = Label(text="Google UI Assistant", font_size='20sp', size_hint_y=None, height=40, color=get_color_from_hex("#4285f4"), bold=True)
        main_layout.add_widget(header)
        
        # Deo za unos API Ključa (da kod ostane Open Source i bezbedan)
        self.key_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=5)
        self.key_input = TextInput(hint_text="Unesi svoj Groq API ključ ovde...", password=True, multiline=False, background_color=get_color_from_hex("#1e1f20"), foreground_color=get_color_from_hex("#e3e3e3"))
        
        # Provera da li ključ već postoji lokalno sačuvan
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "r") as f:
                self.key_input.text = f.read().strip()

        save_key_btn = Button(text="Sačuvaj", size_hint_x=None, width=90, background_color=get_color_from_hex("#34a853"), background_normal='')
        save_key_btn.bind(on_release=self.save_key)
        self.key_layout.add_widget(self.key_input)
        self.key_layout.add_widget(save_key_btn)
        main_layout.add_widget(self.key_layout)
        
        # Deo za poruke sa skrolovanjem
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_box = BoxLayout(orientation='vertical', spacing=12, size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        self.scroll.add_widget(self.chat_box)
        main_layout.add_widget(self.scroll)
        
        # Donji deo za unos i slanje poruka
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.txt_input = TextInput(hint_text="Pitaj me nešto...", multiline=False, background_color=get_color_from_hex("#1e1f20"), foreground_color=get_color_from_hex("#e3e3e3"), cursor_color=get_color_from_hex("#4285f4"))
        self.txt_input.bind(on_text_validate=self.send_message)
        
        send_btn = Button(text="Pošalji", size_hint_x=None, width=100, background_color=get_color_from_hex("#4285f4"), background_normal='', font_size='16sp')
        send_btn.bind(on_release=self.send_message)
        
        input_layout.add_widget(self.txt_input)
        input_layout.add_widget(send_btn)
        main_layout.add_widget(input_layout)
        
        self.add_msg("🤖 Ćao! Unesi ključ na vrhu (ako već nisi) i pitaj me bilo šta!", "#1e1f20")
        return main_layout

    def save_key(self, instance):
        key = self.key_input.text.strip()
        if key:
            with open(KEY_FILE, "w") as f:
                f.write(key)
            self.add_msg("System: API ključ uspešno sačuvan na uređaju!", "#1e1f20")

    def add_msg(self, text, bg_color):
        msg_label = Label(text=text, size_hint_x=1, size_hint_y=None, text_size=(Window.width - 40, None), padding=[15, 10], color=get_color_from_hex("#e3e3e3"), halign='left', valign='top')
        msg_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.chat_box.add_widget(msg_label)
        self.scroll.scroll_to(msg_label)

    def send_message(self, instance):
        text = self.txt_input.text.strip()
        if not text:
            return
        
        self.add_msg(f"Ti: {text}", "#2b2a33")
        self.txt_input.text = ""
        self.history.append({"role": "user", "content": text})
        threading.Thread(target=self.get_ai_response).start()

    def get_ai_response(self):
        api_key = self.key_input.text.strip()
        if not api_key:
            self.add_msg("System: Greška! Prvo moraš uneti i sačuvati Groq API ključ na vrhu ekrana.", "#1e1f20")
            return

        data = json.dumps({"model": MODEL, "messages": self.history}).encode("utf-8")
        req = urllib.request.Request(URL, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                reply = res_data["choices"][0]["message"]["content"]
                self.history.append({"role": "assistant", "content": reply})
                self.add_msg(f"AI: {reply}", "#1e1f20")
        except Exception as e:
            self.add_msg("Greška pri povezivanju. Proveri ključ i internet.", "#1e1f20")

if __name__ == '__main__':
    ChatApp().run()

