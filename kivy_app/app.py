"""
AEGIS AI - Main Kivy Desktop Application Framework
Coordinates ScreenManager, Navigation Sidebar, Top Header, and Flask Service Lifecycle
"""
import os
import sys
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp

# Configure Desktop Window
Window.size = (1280, 800)
Window.minimum_width = 1024
Window.minimum_height = 700
Window.clearcolor = (0.043, 0.059, 0.098, 1.0) # Theme dark background

from kivy_app.ui_components import CyberCard, CyberButton, StatusBadge, COLORS
from kivy_app.screens.login import LoginScreen
from kivy_app.screens.dashboard import DashboardScreen
from kivy_app.screens.monitor import MonitorScreen
from kivy_app.screens.events import EventsScreen
from kivy_app.screens.people import PeopleScreen
from kivy_app.screens.enrollment import EnrollmentScreen
from kivy_app.screens.cameras import CamerasScreen
from kivy_app.screens.storage import StorageScreen
from kivy_app.screens.settings import SettingsScreen

from app import create_app
from services.camera_service import camera_service
from services.notification_service import notification_service
from models import Notification

class NotificationDrawerPopup(Popup):
    """Slide-in / Pop-out drawer for security alerts"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Security Alert Center"
        self.title_color = COLORS["primary"]
        self.size_hint = (0.5, 0.7)
        self.build_ui()

    def build_ui(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))

        # Action bar
        top = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        btn_mark_all = CyberButton(text="MARK ALL READ", btn_type="primary", on_release=self.mark_all_read)
        top.add_widget(btn_mark_all)
        content.add_widget(top)

        # Scrollable list
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        scroll.add_widget(self.list_layout)
        content.add_widget(scroll)

        self.content = content
        self.load_notifs()

    def load_notifs(self):
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                notifs = Notification.query.order_by(Notification.created_at.desc()).limit(30).all()
                self.list_layout.clear_widgets()

                if not notifs:
                    self.list_layout.add_widget(Label(text="No security alerts on record.", color=COLORS["text_muted"], size_hint_y=None, height=dp(36)))
                    return

                for n in notifs:
                    row = CyberCard(
                        orientation="vertical",
                        size_hint_y=None,
                        height=dp(52),
                        padding=[dp(10), dp(6)],
                        spacing=dp(2),
                        bg_color=COLORS["card_hover"] if not n.read_status else COLORS["card_bg"],
                        radius=4
                    )
                    top_line = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
                    lbl_title = Label(text=f"[b]{n.title}[/b]", markup=True, font_size="11sp", color=COLORS["text_main"], halign="left", size_hint_x=0.8)
                    lbl_title.bind(size=lbl_title.setter("text_size"))
                    top_line.add_widget(lbl_title)
                    b_sev = StatusBadge(text=n.severity.upper(), size_hint_x=0.2)
                    top_line.add_widget(b_sev)
                    row.add_widget(top_line)

                    lbl_msg = Label(text=n.message, font_size="10sp", color=COLORS["text_muted"], halign="left", size_hint_y=None, height=dp(18))
                    lbl_msg.bind(size=lbl_msg.setter("text_size"))
                    row.add_widget(lbl_msg)

                    self.list_layout.add_widget(row)
        except Exception as e:
            print(f"[Notifications] Error: {e}")

    def mark_all_read(self, *args):
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                notification_service.mark_all_as_read()
                self.load_notifs()
                app.update_notification_badge()
        except Exception as e:
            print(f"[Notifications] Error marking read: {e}")


class MainAppShell(BoxLayout):
    """Main authenticated application UI containing Header, Nav Sidebar, and Viewport"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 0
        self.nav_buttons = {}

        # 1. Top Header Bar
        self.header = CyberCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            padding=[dp(16), dp(8)],
            spacing=dp(12),
            bg_color=COLORS["sidebar_bg"],
            radius=0
        )
        self.build_header()
        self.add_widget(self.header)

        # 2. Main Body: Sidebar (200dp) + Screen Area
        body = BoxLayout(orientation="horizontal", spacing=0)

        # Sidebar Navigation
        self.sidebar = CyberCard(
            orientation="vertical",
            size_hint_x=None,
            width=dp(210),
            padding=[dp(10), dp(14)],
            spacing=dp(6),
            bg_color=COLORS["sidebar_bg"],
            radius=0
        )
        self.build_sidebar()
        body.add_widget(self.sidebar)

        # Screen Viewport
        self.content_area = BoxLayout(orientation="vertical")
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))

        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(MonitorScreen(name="monitor"))
        self.sm.add_widget(EventsScreen(name="events"))
        self.sm.add_widget(PeopleScreen(name="people"))
        self.sm.add_widget(EnrollmentScreen(name="enrollment"))
        self.sm.add_widget(CamerasScreen(name="cameras"))
        self.sm.add_widget(StorageScreen(name="storage"))
        self.sm.add_widget(SettingsScreen(name="settings"))

        self.content_area.add_widget(self.sm)
        body.add_widget(self.content_area)

        self.add_widget(body)

    def build_header(self):
        # App Title & Branding
        brand_box = BoxLayout(orientation="horizontal", size_hint_x=0.35, spacing=dp(8))
        lbl_logo = Label(text="[b]AEGIS AI[/b]", markup=True, font_size="17sp", color=COLORS["primary"], size_hint_x=None, width=dp(90), halign="left")
        lbl_logo.bind(size=lbl_logo.setter("text_size"))
        lbl_sub = Label(text="| Intelligent Surveillance", font_size="12sp", color=COLORS["text_muted"], halign="left")
        lbl_sub.bind(size=lbl_sub.setter("text_size"))
        brand_box.add_widget(lbl_logo)
        brand_box.add_widget(lbl_sub)
        self.header.add_widget(brand_box)

        # Center Status Pill & FPS
        center_box = BoxLayout(orientation="horizontal", size_hint_x=0.35, spacing=dp(10))
        self.cam_badge = StatusBadge(text="LIVE", size_hint_x=None, width=dp(70))
        self.lbl_header_fps = Label(text="FPS: 0.0", font_size="12sp", color=COLORS["text_muted"], size_hint_x=None, width=dp(70))
        center_box.add_widget(self.cam_badge)
        center_box.add_widget(self.lbl_header_fps)
        self.header.add_widget(center_box)

        # Right User Info, Notifications, Logout
        right_box = BoxLayout(orientation="horizontal", size_hint_x=0.30, spacing=dp(8))
        self.btn_notif = CyberButton(text="ALERTS (0)", btn_type="warning", size_hint_x=None, width=dp(95), on_release=self.open_notifications)
        self.lbl_user = Label(text="Admin", font_size="12sp", color=COLORS["text_main"], size_hint_x=0.55, halign="right")
        self.lbl_user.bind(size=self.lbl_user.setter("text_size"))
        btn_logout = CyberButton(text="LOGOUT", btn_type="danger", size_hint_x=None, width=dp(80), on_release=self.do_logout)

        right_box.add_widget(self.btn_notif)
        right_box.add_widget(self.lbl_user)
        right_box.add_widget(btn_logout)
        self.header.add_widget(right_box)

    def build_sidebar(self):
        nav_items = [
            ("dashboard", "Telemetry Dashboard"),
            ("monitor", "Live Video Monitor"),
            ("events", "Security Events"),
            ("people", "Subject Directory"),
            ("enrollment", "Face Enrollment"),
            ("cameras", "Camera Hardware"),
            ("storage", "Storage & Retention"),
            ("settings", "System Settings")
        ]

        for screen_name, title in nav_items:
            btn = CyberButton(
                text=title,
                btn_type="secondary",
                size_hint_y=None,
                height=dp(38),
                radius=6,
                on_release=lambda instance, s=screen_name: self.switch_screen(s)
            )
            self.nav_buttons[screen_name] = btn
            self.sidebar.add_widget(btn)

        # Push to top
        self.sidebar.add_widget(Label(size_hint_y=1))

    def switch_screen(self, screen_name):
        self.sm.current = screen_name
        for name, btn in self.nav_buttons.items():
            if name == screen_name:
                btn.base_color = COLORS["primary"]
                btn.color = COLORS["text_main"]
            else:
                btn.base_color = COLORS["card_hover"]
                btn.color = COLORS["text_muted"]
            btn._redraw()

    def open_notifications(self, *args):
        drawer = NotificationDrawerPopup()
        drawer.open()

    def do_logout(self, *args):
        app = App.get_running_app()
        app.do_logout()


class AegisKivyApp(App):
    title = "AEGIS AI - Intelligent Premises Monitoring System"

    def build(self):
        self.current_user = None
        self.flask_app = create_app()

        # Root ScreenManager holding Login and Authenticated Main Shell
        self.root_sm = ScreenManager(transition=FadeTransition(duration=0.2))

        # 1. Login Screen
        self.login_screen = LoginScreen(name="login_screen")
        self.root_sm.add_widget(self.login_screen)

        # 2. Main Shell Screen (holds inner header + sidebar + screens)
        self.shell_screen = Screen(name="shell_screen")
        self.shell_widget = MainAppShell()
        self.shell_screen.add_widget(self.shell_widget)
        self.root_sm.add_widget(self.shell_screen)

        # Start on Login
        self.root_sm.current = "login_screen"

        # Scheduled update of header badges and alert counts
        Clock.schedule_interval(self.periodic_sync, 2.0)

        return self.root_sm

    def on_login_success(self):
        user_info = self.current_user or {}
        uname = user_info.get("full_name") or user_info.get("username", "Admin")
        role = user_info.get("role", "admin").upper()
        self.shell_widget.lbl_user.text = f"{uname} ({role})"
        self.shell_widget.switch_screen("dashboard")
        self.root_sm.current = "shell_screen"
        self.update_notification_badge()

    def do_logout(self):
        self.current_user = None
        self.root_sm.current = "login_screen"

    def navigate_to(self, screen_name):
        self.shell_widget.switch_screen(screen_name)

    def update_notification_badge(self):
        try:
            with self.flask_app.app_context():
                unread = notification_service.get_unread_count()
                self.shell_widget.btn_notif.text = f"ALERTS ({unread})"
        except Exception:
            pass

    def periodic_sync(self, dt):
        if self.current_user is None:
            return

        # 1. Update camera status in top header
        st = camera_service.get_status()
        status_text = st.get("status", "OFFLINE")
        fps = st.get("fps", 0.0)

        self.shell_widget.cam_badge.text = f" {status_text} "
        if status_text == "LIVE":
            self.shell_widget.cam_badge.bg_color = (0.063, 0.725, 0.506, 0.85)
        elif status_text == "PAUSED":
            self.shell_widget.cam_badge.bg_color = (0.961, 0.620, 0.043, 0.85)
        else:
            self.shell_widget.cam_badge.bg_color = (0.937, 0.267, 0.267, 0.85)
        self.shell_widget.cam_badge._draw()

        self.shell_widget.lbl_header_fps.text = f"FPS: {fps:.1f}"

        # 2. Update notification badge
        self.update_notification_badge()

    def on_stop(self):
        """Cleanup camera threads and background workers on application exit"""
        print("[AegisKivyApp] Shutting down monitoring services...")
        try:
            camera_service.stop_monitoring()
        except Exception as e:
            print(f"[AegisKivyApp] Error stopping camera: {e}")

def main():
    AegisKivyApp().run()

if __name__ == "__main__":
    main()
