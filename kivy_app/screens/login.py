"""
AEGIS AI - Login Screen
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy_app.ui_components import CyberCard, CyberButton, CyberInput, COLORS
from models import db, User

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = AnchorLayout(anchor_x="center", anchor_y="center")
        
        # Center Login Card
        card = CyberCard(
            orientation="vertical",
            padding=[dp(32), dp(36)],
            spacing=dp(18),
            size_hint=(None, None),
            size=(dp(420), dp(480)),
            radius=12
        )

        # Header Title
        title_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(80), spacing=dp(4))
        title = Label(
            text="[b]AEGIS AI[/b]",
            markup=True,
            font_size="28sp",
            color=COLORS["primary"],
            halign="center"
        )
        subtitle = Label(
            text="Premises Monitoring & Security Suite",
            font_size="13sp",
            color=COLORS["text_muted"],
            halign="center"
        )
        title_box.add_widget(title)
        title_box.add_widget(subtitle)
        card.add_widget(title_box)

        # Error / Feedback label
        self.msg_label = Label(
            text="",
            font_size="12sp",
            color=COLORS["danger"],
            size_hint_y=None,
            height=dp(24),
            halign="center"
        )
        card.add_widget(self.msg_label)

        # Form Fields
        form_box = BoxLayout(orientation="vertical", spacing=dp(14))
        
        user_lbl = Label(text="Username", font_size="12sp", color=COLORS["text_muted"], halign="left", size_hint_y=None, height=dp(18))
        user_lbl.bind(size=user_lbl.setter("text_size"))
        self.username_input = CyberInput(multiline=False, size_hint_y=None, height=dp(42), text="admin")
        
        pass_lbl = Label(text="Password", font_size="12sp", color=COLORS["text_muted"], halign="left", size_hint_y=None, height=dp(18))
        pass_lbl.bind(size=pass_lbl.setter("text_size"))
        self.password_input = CyberInput(password=True, multiline=False, size_hint_y=None, height=dp(42), text="Admin@123")
        self.password_input.bind(on_text_validate=self.do_login)

        form_box.add_widget(user_lbl)
        form_box.add_widget(self.username_input)
        form_box.add_widget(pass_lbl)
        form_box.add_widget(self.password_input)
        card.add_widget(form_box)

        # Submit Button
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), padding=[0, dp(4)])
        self.login_btn = CyberButton(text="AUTHENTICATE & ENTER", btn_type="primary", on_release=self.do_login)
        btn_box.add_widget(self.login_btn)
        card.add_widget(btn_box)

        root.add_widget(card)
        self.add_widget(root)

    def do_login(self, *args):
        username = self.username_input.text.strip()
        password = self.password_input.text

        if not username or not password:
            self.msg_label.color = COLORS["danger"]
            self.msg_label.text = "Please enter both username and password."
            return

        from kivy.app import App
        app = App.get_running_app()

        try:
            with app.flask_app.app_context():
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    app.current_user = {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role,
                        "full_name": user.full_name or user.username,
                        "is_admin": user.is_admin
                    }
                    self.msg_label.text = ""
                    app.on_login_success()
                else:
                    self.msg_label.color = COLORS["danger"]
                    self.msg_label.text = "Invalid credentials. Please verify and retry."
        except Exception as e:
            self.msg_label.color = COLORS["danger"]
            self.msg_label.text = f"Authentication error: {e}"
