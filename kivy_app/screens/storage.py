"""
AEGIS AI - Storage Telemetry & 30-Day Automated Retention Purge Screen
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, StatCard, CyberButton, COLORS
from services.storage_service import storage_service
from services.retention_service import retention_service
from models import Event, Notification

class StorageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(16), padding=dp(16))

        # Title
        top = BoxLayout(size_hint_y=None, height=dp(38))
        lbl = Label(text="[b]FORENSIC STORAGE TELEMETRY & 30-DAY RETENTION ENGINE[/b]", markup=True, font_size="16sp", color=COLORS["text_main"], halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        top.add_widget(lbl)
        root.add_widget(top)

        # Stat cards
        stats_grid = GridLayout(cols=4, spacing=dp(14), size_hint_y=None, height=dp(86))
        self.card_snapshots = StatCard(title="Captured Snapshots", value="0", accent_color=COLORS["info"])
        self.card_size = StatCard(title="Storage Used (MB)", value="0.0", accent_color=COLORS["warning"])
        self.card_retention = StatCard(title="Retention Lifespan", value="30 Days", accent_color=COLORS["primary"])
        self.card_oldest = StatCard(title="Oldest Snapshot", value="None", accent_color=COLORS["text_muted"])

        stats_grid.add_widget(self.card_snapshots)
        stats_grid.add_widget(self.card_size)
        stats_grid.add_widget(self.card_retention)
        stats_grid.add_widget(self.card_oldest)
        root.add_widget(stats_grid)

        # Action Card
        action_card = CyberCard(orientation="vertical", padding=[dp(18), dp(16)], spacing=dp(12), size_hint_y=None, height=dp(130), radius=8)
        act_title = Label(
            text="[b]AUTOMATED DATA RETENTION POLICY[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(20),
            halign="left"
        )
        act_title.bind(size=act_title.setter("text_size"))
        action_card.add_widget(act_title)

        desc = Label(
            text="Records and high-definition snapshots older than the configured 30-day retention window are purged to maintain optimal disk space and database performance.",
            font_size="12sp",
            color=COLORS["text_muted"],
            size_hint_y=None,
            height=dp(28),
            halign="left"
        )
        desc.bind(size=desc.setter("text_size"))
        action_card.add_widget(desc)

        btn_cleanup = CyberButton(
            text="TRIGGER 30-DAY RETENTION CLEANUP NOW",
            btn_type="danger",
            size_hint_y=None,
            height=dp(42),
            on_release=self.trigger_purge
        )
        action_card.add_widget(btn_cleanup)
        root.add_widget(action_card)

        # Audit Output Log
        log_card = CyberCard(orientation="vertical", padding=[dp(18), dp(14)], spacing=dp(10), size_hint_y=1, radius=8)
        log_title = Label(
            text="[b]RETENTION PURGE AUDIT LOG[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(20),
            halign="left"
        )
        log_title.bind(size=log_title.setter("text_size"))
        log_card.add_widget(log_title)

        scroll = ScrollView(size_hint=(1, 1))
        self.lbl_log = Label(
            text="No cleanup runs triggered yet in this session.",
            font_size="12sp",
            color=COLORS["text_muted"],
            size_hint_y=None,
            halign="left",
            valign="top"
        )
        self.lbl_log.bind(width=lambda *x: self.lbl_log.setter('text_size')(self.lbl_log, (self.lbl_log.width, None)),
                          texture_size=lambda *x: self.lbl_log.setter('height')(self.lbl_log, self.lbl_log.texture_size[1]))
        scroll.add_widget(self.lbl_log)
        log_card.add_widget(scroll)

        root.add_widget(log_card)
        self.add_widget(root)

    def on_enter(self):
        self.load_storage_stats()

    def load_storage_stats(self):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                stats = storage_service.get_storage_statistics()
                days = retention_service.get_retention_days()

                self.card_snapshots.update_value(stats["total_snapshots"])
                self.card_size.update_value(f"{stats['total_size_mb']:.1f}")
                self.card_retention.update_value(f"{days} Days")
                self.card_oldest.update_value(stats.get("oldest_snapshot", "None") or "None")
        except Exception as e:
            print(f"[StorageScreen] Error loading stats: {e}")

    def trigger_purge(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                report = retention_service.run_cleanup()
                msg = (
                    f"[{report.get('status', 'SUCCESS').upper()}] Purge finished at {report.get('timestamp')}\n"
                    f" - Cutoff Date: {report.get('cutoff_date')}\n"
                    f" - Snapshots Deleted from Disk: {report.get('snapshots_deleted', 0)}\n"
                    f" - Empty Directories Removed: {report.get('empty_dirs_deleted', 0)}\n"
                    f" - Database Event Records Purged: {report.get('events_purged', 0)}\n"
                    f" - Storage Cleaned: {report.get('cleaned_mb', 0):.2f} MB\n"
                )
                self.lbl_log.text = msg
                self.lbl_log.color = COLORS["primary"]
                self.load_storage_stats()
        except Exception as e:
            self.lbl_log.text = f"Error executing retention purge: {e}"
            self.lbl_log.color = COLORS["danger"]
