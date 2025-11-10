from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle, Line
from plyer import notification
import datetime, winsound, json, os
from kivy.utils import platform
import json

class MedicineApp(App):
    def build(self):
        self.title = "💊 Medicine Reminder"

        root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # ---------- FORM AREA ----------
        form_layout = GridLayout(cols=2, spacing=10, row_default_height=40, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))

        self.name_input = TextInput(multiline=False)
        self.shape_spinner = Spinner(text="Round", values=["Round", "Oval", "Capsule", "Square", "Rounded Rectangle"])
        self.size_spinner = Spinner(text="Medium", values=["Small", "Medium", "Large"])
        self.color1_input = TextInput(text="red", multiline=False)
        self.color2_input = TextInput(text="white", multiline=False)
        self.time_input = TextInput(text="09:00", multiline=False)

        form_layout.add_widget(Label(text="Medicine Name:"))
        form_layout.add_widget(self.name_input)
        form_layout.add_widget(Label(text="Shape:"))
        form_layout.add_widget(self.shape_spinner)
        form_layout.add_widget(Label(text="Size:"))
        form_layout.add_widget(self.size_spinner)
        form_layout.add_widget(Label(text="Color 1:"))
        form_layout.add_widget(self.color1_input)
        form_layout.add_widget(Label(text="Color 2 (Capsule):"))
        form_layout.add_widget(self.color2_input)
        form_layout.add_widget(Label(text="Time (HH:MM):"))
        form_layout.add_widget(self.time_input)
        root.add_widget(form_layout)

        # ---------- PREVIEW SECTION ----------
        preview_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=160, spacing=10)
        self.preview_canvas = RelativeLayout(size_hint=(0.7, 1))
        preview_button = Button(text="Preview 💊", size_hint=(0.3, 1))
        preview_button.bind(on_press=self.preview_medicine)
        preview_layout.add_widget(self.preview_canvas)
        preview_layout.add_widget(preview_button)
        root.add_widget(preview_layout)

        # ---------- ADD BUTTON ----------
        add_button = Button(text="Add Medicine", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_medicine)
        root.add_widget(add_button)

        # ---------- LIST SCROLL AREA ----------
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=5, padding=5)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        root.add_widget(scroll)

        # Load existing medicines
        self.medicines = self.load_medicines()
        for m in self.medicines:
            self.list_layout.add_widget(Label(text=f"{m['name']} ⏰ {m['time']}"))

        self.last_notified = set()
        Clock.schedule_interval(self.check_reminders, 10)  # every 10 sec
        self.start_service()
        return root

    # ---------- DRAW PILL ----------
    def draw_pill(self, canvas, shape, size, color1, color2):
        canvas.canvas.clear()
        sizes = {"Small": (80, 40), "Medium": (120, 60), "Large": (160, 80)}
        w, h = sizes.get(size, (120, 60))
        cx, cy = canvas.width / 2, canvas.height / 2
        x, y = cx - w / 2, cy - h / 2

        def get_color(c):
            colors = {
                "red": (1, 0, 0, 1), "blue": (0, 0, 1, 1), "green": (0, 1, 0, 1),
                "yellow": (1, 1, 0, 1), "white": (1, 1, 1, 1), "pink": (1, 0.6, 0.7, 1),
                "orange": (1, 0.5, 0, 1), "gray": (0.7, 0.7, 0.7, 1),
                "purple": (0.6, 0, 0.8, 1)
            }
            return colors.get(c.lower(), (0.6, 0.6, 0.6, 1))

        c1, c2 = get_color(color1), get_color(color2)

        with canvas.canvas:
            if shape == "Capsule":
                r = h / 2
                Color(*c1)
                RoundedRectangle(pos=(x, y), size=(w / 2, h),
                                 radius=[(r, r), (0, 0), (0, 0), (r, r)])
                Color(*c2)
                RoundedRectangle(pos=(x + w / 2, y), size=(w / 2, h),
                                 radius=[(0, 0), (r, r), (r, r), (0, 0)])
                Color(0, 0, 0)
                Line(rounded_rectangle=(x, y, w, h, r), width=1.2)

            elif shape == "Rounded Rectangle":
                r = h / 2
                Color(*c1)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[(r, r), (r, r), (r, r), (r, r)])
                Color(0, 0, 0)
                Line(rounded_rectangle=(x, y, w, h, r), width=1.2)

            elif shape == "Round":
                Color(*c1)
                Ellipse(pos=(x, y), size=(h, h))
                Color(0, 0, 0)
                Line(ellipse=(x, y, h, h), width=1.2)

            elif shape == "Oval":
                Color(*c1)
                Ellipse(pos=(x, y), size=(w, h))
                Color(0, 0, 0)
                Line(ellipse=(x, y, w, h), width=1.2)

            elif shape == "Square":
                Color(*c1)
                Rectangle(pos=(x, y), size=(h, h))
                Color(0, 0, 0)
                Line(rectangle=(x, y, h, h), width=1.2)

    # ---------- PREVIEW ----------
    def preview_medicine(self, instance):
        self.draw_pill(
            self.preview_canvas,
            self.shape_spinner.text,
            self.size_spinner.text,
            self.color1_input.text,
            self.color2_input.text
        )

    # ---------- SAVE / LOAD ----------
    def save_medicines(self):
        with open("medicines.json", "w") as f:
            json.dump(self.medicines, f)

    def load_medicines(self):
        if os.path.exists("medicines.json"):
            with open("medicines.json", "r") as f:
                return json.load(f)
        return []

    # ---------- ADD ----------
    def add_medicine(self, instance):
        name = self.name_input.text.strip()
        time_text = self.time_input.text.strip()
        if not name or not time_text:
            return
        item = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
        item.add_widget(Label(text=f"{name} ⏰ {time_text}", halign="left"))
        self.list_layout.add_widget(item)
        med = {
            "name": name,
            "shape": self.shape_spinner.text,
            "size": self.size_spinner.text,
            "color1": self.color1_input.text,
            "color2": self.color2_input.text,
            "time": time_text
        }
        self.medicines.append(med)
        self.save_medicines()

    def start_service(self):
    # Only try to use Android features when actually running on Android
        if platform == "android":
            try:
                from jnius import autoclass
                from android import start_service
                PythonService = autoclass('org.kivy.android.PythonService')
                service = PythonService.mService
                if not service:
                    print("Starting background service…")
                    start_service('service', 'main.py')
            except Exception as e:
                print("⚠️ Could not start Android background service:", e)
        else:
            print("💻 Running on desktop — background services not supported here.")

    # ---------- POPUP ----------
    def show_reminder_popup(self, med):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text=f"⏰ Time to take: [b]{med['name']}[/b]", markup=True, font_size=18))
        pill_canvas = RelativeLayout(size_hint=(1, 1), height=120)
        layout.add_widget(pill_canvas)
        Clock.schedule_once(lambda dt: self.draw_pill(pill_canvas, med["shape"], med["size"], med["color1"], med["color2"]), 0.1)
        close_btn = Button(text="OK", size_hint_y=None, height=40)
        layout.add_widget(close_btn)
        popup = Popup(title="💊 Medicine Reminder", content=layout, size_hint=(0.6, 0.6), auto_dismiss=False)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- REMINDER CHECK ----------
    def check_reminders(self, dt):
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")

        for med in self.medicines:
            if med["time"] == current_time and med["time"] not in self.last_notified:
                self.last_notified.add(med["time"])
                self.show_reminder_popup(med)
                notification.notify(title="💊 Medicine Reminder", message=f"Time to take {med['name']}", timeout=10)
                try:
                    winsound.Beep(1000, 500)
                except:
                    pass


if __name__ == "__main__":
    MedicineApp().run()
