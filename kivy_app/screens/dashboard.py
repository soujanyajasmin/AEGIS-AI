"""
AEGIS AI - Dashboard Telemetry & Overview Screen
"""
from datetime import datetime, date
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, StatCard, CyberButton, StatusBadge, COLORS
from models import db, Event, Camera
from services.camera_service import camera_service
from services.storage_service import storage_service

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(16), padding=dp(16))

        # Top Bar: Title & Refresh Button
        top_bar = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(12))
        lbl_dash = Label(
            text="[b]PREMISES TELEMETRY DASHBOARD[/b]",
            markup=True,
            font_size="16sp",
            color=COLORS["text_main"],
            halign="left"
        )
        lbl_dash.bind(size=lbl_dash.setter("text_size"))
        btn_refresh = CyberButton(text="REFRESH METRICS", btn_type="secondary", size_hint=(None, 1), width=dp(150), on_release=self.load_data)
        top_bar.add_widget(lbl_dash)
        top_bar.add_widget(btn_refresh)
        root.add_widget(top_bar)

        # 1. Row of Stat Metric Cards
        self.stats_grid = GridLayout(cols=6, spacing=dp(12), size_hint_y=None, height=dp(86))
        self.card_events = StatCard(title="Today's Events", value="0", accent_color=COLORS["info"])
        self.card_people = StatCard(title="People Detected", value="0", accent_color=COLORS["primary"])
        self.card_known = StatCard(title="Known Subjects", value="0", accent_color=COLORS["primary"])
        self.card_unknown = StatCard(title="Unknown / Alerts", value="0", accent_color=COLORS["danger"])
        self.card_vehicles = StatCard(title="Vehicles", value="0", accent_color=COLORS["info"])
        self.card_storage = StatCard(title="Storage (MB)", value="0", accent_color=COLORS["warning"])

        self.stats_grid.add_widget(self.card_events)
        self.stats_grid.add_widget(self.card_people)
        self.stats_grid.add_widget(self.card_known)
        self.stats_grid.add_widget(self.card_unknown)
        self.stats_grid.add_widget(self.card_vehicles)
        self.stats_grid.add_widget(self.card_storage)
        root.add_widget(self.stats_grid)

        # 2. Main Content Split: Recent Events (70%) + Quick Controls (30%)
        content_box = BoxLayout(orientation="horizontal", spacing=dp(16), size_hint_y=1)

        # Recent Events Card
        events_card = CyberCard(orientation="vertical", padding=[dp(16), dp(14)], spacing=dp(10), size_hint_x=0.72)
        ev_title = Label(
            text="[b]RECENT SECURITY EVENTS & DETECTION AUDIT[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(22),
            halign="left"
        )
        ev_title.bind(size=ev_title.setter("text_size"))
        events_card.add_widget(ev_title)

        # Table Header
        tbl_hdr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        for col_name, col_w in [("TIME", 0.18), ("ENTITY", 0.26), ("STATUS", 0.20), ("DIRECTION", 0.18), ("CONFIDENCE", 0.18)]:
            hdr = Label(text=f"[b]{col_name}[/b]", markup=True, font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=col_w)
            hdr.bind(size=hdr.setter("text_size"))
            tbl_hdr.add_widget(hdr)
        events_card.add_widget(tbl_hdr)

        # Scrollable rows
        scroll = ScrollView(size_hint=(1, 1))
        self.events_layout = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.events_layout.bind(minimum_height=self.events_layout.setter("height"))
        scroll.add_widget(self.events_layout)
        events_card.add_widget(scroll)

        content_box.add_widget(events_card)

        # Right Actions & System Status Card
        side_card = CyberCard(orientation="vertical", padding=[dp(16), dp(14)], spacing=dp(12), size_hint_x=0.28)
        side_title = Label(
            text="[b]SYSTEM ACTIONS[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(22),
            halign="left"
        )
        side_title.bind(size=side_title.setter("text_size"))
        side_card.add_widget(side_title)

        btn_go_monitor = CyberButton(text="OPEN LIVE MONITOR", btn_type="primary", size_hint_y=None, height=dp(42), on_release=self.nav_to_monitor)
        btn_go_events = CyberButton(text="EXPLORE ALL EVENTS", btn_type="info", size_hint_y=None, height=dp(42), on_release=self.nav_to_events)
        btn_go_enroll = CyberButton(text="ENROLL NEW FACE", btn_type="secondary", size_hint_y=None, height=dp(42), on_release=self.nav_to_enrollment)
        btn_go_purge = CyberButton(text="MANAGE RETENTION", btn_type="warning", size_hint_y=None, height=dp(42), on_release=self.nav_to_storage)

        side_card.add_widget(btn_go_monitor)
        side_card.add_widget(btn_go_events)
        side_card.add_widget(btn_go_enroll)
        side_card.add_widget(btn_go_purge)

        # Spacer
        side_card.add_widget(Label(size_hint_y=1))

        content_box.add_widget(side_card)
        root.add_widget(content_box)

        self.add_widget(root)

    def on_enter(self):
        self.load_data()

    def nav_to_monitor(self, *args):
        from kivy.app import App
        App.get_running_app().navigate_to("monitor")

    def nav_to_events(self, *args):
        from kivy.app import App
        App.get_running_app().navigate_to("events")

    def nav_to_enrollment(self, *args):
        from kivy.app import App
        App.get_running_app().navigate_to("enrollment")

    def nav_to_storage(self, *args):
        from kivy.app import App
        App.get_running_app().navigate_to("storage")

    def load_data(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                today_start = datetime.combine(date.today(), datetime.min.time())
                
                tot_events = Event.query.filter(Event.timestamp >= today_start).count()
                people = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON").count()
                known = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "KNOWN").count()
                unknown = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "UNKNOWN").count()
                vehicles = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "VEHICLE").count()
                
                storage_stats = storage_service.get_storage_statistics()

                self.card_events.update_value(tot_events)
                self.card_people.update_value(people)
                self.card_known.update_value(known)
                self.card_unknown.update_value(unknown)
                self.card_vehicles.update_value(vehicles)
                self.card_storage.update_value(f"{storage_stats['total_size_mb']:.1f}")

                # Load Recent Events
                recent = Event.query.order_by(Event.timestamp.desc()).limit(15).all()
                self.events_layout.clear_widgets()

                if not recent:
                    lbl = Label(text="No security events recorded yet today.", font_size="12sp", color=COLORS["text_muted"], size_hint_y=None, height=dp(36))
                    self.events_layout.add_widget(lbl)
                else:
                    for ev in recent:
                        row = CyberCard(
                            orientation="horizontal",
                            size_hint_y=None,
                            height=dp(34),
                            padding=[dp(8), dp(4)],
                            spacing=dp(6),
                            bg_color=COLORS["card_hover"],
                            radius=4
                        )

                        t_str = ev.timestamp.strftime("%H:%M:%S")
                        l_time = Label(text=t_str, font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=0.18)
                        l_time.bind(size=l_time.setter("text_size"))
                        row.add_widget(l_time)

                        name = ev.entity_name or ev.entity_type
                        l_entity = Label(text=f"[b]{name}[/b]", markup=True, font_size="11sp", color=COLORS["text_main"], halign="left", size_hint_x=0.26)
                        l_entity.bind(size=l_entity.setter("text_size"))
                        row.add_widget(l_entity)

                        b_status = StatusBadge(text=ev.recognition_status, size_hint_x=0.20)
                        row.add_widget(b_status)

                        b_dir = StatusBadge(text=ev.direction if ev.direction != "NONE" else "STATIONARY", size_hint_x=0.18)
                        row.add_widget(b_dir)

                        l_conf = Label(text=f"{int(ev.confidence * 100)}%", font_size="11sp", color=COLORS["info"], halign="left", size_hint_x=0.18)
                        l_conf.bind(size=l_conf.setter("text_size"))
                        row.add_widget(l_conf)

                        self.events_layout.add_widget(row)

        except Exception as e:
            print(f"[DashboardScreen] Error fetching dashboard data: {e}")
