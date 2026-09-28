"""
AEGIS AI - Forensic Events Explorer & Snapshot Modal
"""
from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, StatusBadge, COLORS
from models import Event, db
from config import Config

class SnapshotViewerPopup(Popup):
    """Modal displaying high-resolution snapshot and event metadata"""
    def __init__(self, event_data, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Forensic Event #{event_data['id']} - {event_data['entity_name']}"
        self.title_color = COLORS["primary"]
        self.size_hint = (0.85, 0.88)
        self.auto_dismiss = True

        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(12))

        # Snapshot Image
        img_container = CyberCard(orientation="vertical", padding=dp(4), size_hint_y=0.78)
        snapshot_rel = event_data.get("snapshot_path", "")
        img_widget = Image(fit_mode="contain")

        if snapshot_rel:
            full_path = (Path(Config.STORAGE_DIR) / snapshot_rel).resolve()
            if full_path.exists():
                img_widget.source = str(full_path)
            else:
                img_widget.source = ""
        img_container.add_widget(img_widget)
        content.add_widget(img_container)

        # Meta detail row
        meta_box = CyberCard(
            orientation="horizontal",
            padding=[dp(12), dp(8)],
            spacing=dp(10),
            size_hint_y=None,
            height=dp(44),
            radius=6
        )
        meta_box.add_widget(Label(text=f"Time: {event_data.get('timestamp')}", font_size="12sp", color=COLORS["text_main"]))
        meta_box.add_widget(Label(text=f"Camera: {event_data.get('camera_name', 'Main Entrance')}", font_size="12sp", color=COLORS["text_muted"]))
        meta_box.add_widget(StatusBadge(text=event_data.get("recognition_status", "UNKNOWN")))
        meta_box.add_widget(Label(text=f"Confidence: {int(event_data.get('confidence', 0)*100)}%", font_size="12sp", color=COLORS["info"]))
        content.add_widget(meta_box)

        # Close button
        btn_close = CyberButton(text="CLOSE VIEWER", btn_type="secondary", size_hint_y=None, height=dp(38), on_release=self.dismiss)
        content.add_widget(btn_close)

        self.content = content


class EventsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))

        # Title & Filter Bar
        filter_card = CyberCard(
            orientation="horizontal",
            spacing=dp(10),
            padding=[dp(14), dp(10)],
            size_hint_y=None,
            height=dp(56),
            radius=8
        )

        lbl = Label(text="[b]EVENTS LOG[/b]", markup=True, font_size="15sp", color=COLORS["primary"], size_hint_x=0.20, halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        filter_card.add_widget(lbl)

        # Entity Spinner
        self.spin_entity = Spinner(
            text="ALL ENTITIES",
            values=["ALL ENTITIES", "PERSON", "VEHICLE", "ANIMAL", "OTHER"],
            size_hint_x=0.20,
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        filter_card.add_widget(self.spin_entity)

        # Recognition Spinner
        self.spin_rec = Spinner(
            text="ALL STATUSES",
            values=["ALL STATUSES", "KNOWN", "UNKNOWN", "NOT_APPLICABLE"],
            size_hint_x=0.20,
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        filter_card.add_widget(self.spin_rec)

        # Direction Spinner
        self.spin_dir = Spinner(
            text="ALL MOVEMENTS",
            values=["ALL MOVEMENTS", "ENTRY", "EXIT", "NONE"],
            size_hint_x=0.20,
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        filter_card.add_widget(self.spin_dir)

        btn_filter = CyberButton(text="APPLY FILTERS", btn_type="primary", size_hint_x=0.20, on_release=self.load_events)
        filter_card.add_widget(btn_filter)

        root.add_widget(filter_card)

        # Table Card Container
        table_card = CyberCard(orientation="vertical", padding=[dp(14), dp(12)], spacing=dp(8), size_hint_y=1, radius=8)

        # Table Header
        tbl_hdr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        cols = [("#ID", 0.08), ("TIMESTAMP", 0.20), ("ENTITY NAME", 0.24), ("RECOGNITION", 0.16), ("DIRECTION", 0.14), ("CONF", 0.10), ("ACTION", 0.14)]
        for name, w in cols:
            h_lbl = Label(text=f"[b]{name}[/b]", markup=True, font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=w)
            h_lbl.bind(size=h_lbl.setter("text_size"))
            tbl_hdr.add_widget(h_lbl)
        table_card.add_widget(tbl_hdr)

        # Scrollable events rows
        scroll = ScrollView(size_hint=(1, 1))
        self.events_layout = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.events_layout.bind(minimum_height=self.events_layout.setter("height"))
        scroll.add_widget(self.events_layout)
        table_card.add_widget(scroll)

        root.add_widget(table_card)
        self.add_widget(root)

    def on_enter(self):
        self.load_events()

    def load_events(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                query = Event.query

                ent = self.spin_entity.text
                if ent != "ALL ENTITIES":
                    query = query.filter(Event.entity_type == ent)

                rec = self.spin_rec.text
                if rec != "ALL STATUSES":
                    query = query.filter(Event.recognition_status == rec)

                dir_ = self.spin_dir.text
                if dir_ != "ALL MOVEMENTS":
                    query = query.filter(Event.direction == dir_)

                events = query.order_by(Event.timestamp.desc()).limit(50).all()
                self.events_layout.clear_widgets()

                if not events:
                    empty = Label(text="No matching security events found.", font_size="13sp", color=COLORS["text_muted"], size_hint_y=None, height=dp(40))
                    self.events_layout.add_widget(empty)
                    return

                for ev in events:
                    ev_dict = ev.to_dict()
                    row = CyberCard(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=dp(38),
                        padding=[dp(8), dp(4)],
                        spacing=dp(6),
                        bg_color=COLORS["card_hover"],
                        radius=4
                    )

                    l_id = Label(text=f"#{ev.id}", font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=0.08)
                    l_id.bind(size=l_id.setter("text_size"))
                    row.add_widget(l_id)

                    l_time = Label(text=ev.timestamp.strftime("%Y-%m-%d %H:%M:%S"), font_size="11sp", color=COLORS["text_main"], halign="left", size_hint_x=0.20)
                    l_time.bind(size=l_time.setter("text_size"))
                    row.add_widget(l_time)

                    l_name = Label(text=f"[b]{ev.entity_name}[/b]", markup=True, font_size="11sp", color=COLORS["text_main"], halign="left", size_hint_x=0.24)
                    l_name.bind(size=l_name.setter("text_size"))
                    row.add_widget(l_name)

                    b_rec = StatusBadge(text=ev.recognition_status, size_hint_x=0.16)
                    row.add_widget(b_rec)

                    b_dir = StatusBadge(text=ev.direction if ev.direction != "NONE" else "STATIONARY", size_hint_x=0.14)
                    row.add_widget(b_dir)

                    l_conf = Label(text=f"{int(ev.confidence * 100)}%", font_size="11sp", color=COLORS["info"], halign="left", size_hint_x=0.10)
                    l_conf.bind(size=l_conf.setter("text_size"))
                    row.add_widget(l_conf)

                    btn_snap = CyberButton(
                        text="VIEW",
                        btn_type="info",
                        size_hint_x=0.14,
                        on_release=lambda instance, data=ev_dict: self.open_snapshot_modal(data)
                    )
                    row.add_widget(btn_snap)

                    self.events_layout.add_widget(row)

        except Exception as e:
            print(f"[EventsScreen] Error loading events: {e}")

    def open_snapshot_modal(self, event_data):
        popup = SnapshotViewerPopup(event_data=event_data)
        popup.open()
