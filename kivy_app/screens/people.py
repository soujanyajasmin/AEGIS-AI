"""
AEGIS AI - Enrolled Subjects & People Directory Screen
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, CyberInput, StatusBadge, COLORS
from models import db, Person, FaceEmbedding
from services.face_recognition_service import face_recognition_service
from services.storage_service import storage_service

class AddPersonPopup(Popup):
    """Modal dialog to register a new person"""
    def __init__(self, on_success_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Register New Subject"
        self.title_color = COLORS["primary"]
        self.size_hint = (0.55, 0.65)
        self.on_success_callback = on_success_callback

        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))

        self.lbl_msg = Label(text="", font_size="12sp", color=COLORS["danger"], size_hint_y=None, height=dp(20))
        content.add_widget(self.lbl_msg)

        f_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.75)
        
        f_grid.add_widget(Label(text="Full Name *", font_size="12sp", color=COLORS["text_muted"], halign="left"))
        self.in_name = CyberInput(multiline=False)
        f_grid.add_widget(self.in_name)

        f_grid.add_widget(Label(text="Badge / ID Code", font_size="12sp", color=COLORS["text_muted"], halign="left"))
        self.in_code = CyberInput(multiline=False)
        f_grid.add_widget(self.in_code)

        f_grid.add_widget(Label(text="Email Address", font_size="12sp", color=COLORS["text_muted"], halign="left"))
        self.in_email = CyberInput(multiline=False)
        f_grid.add_widget(self.in_email)

        f_grid.add_widget(Label(text="Notes / Dept", font_size="12sp", color=COLORS["text_muted"], halign="left"))
        self.in_notes = CyberInput(multiline=False)
        f_grid.add_widget(self.in_notes)

        content.add_widget(f_grid)

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(42))
        btn_cancel = CyberButton(text="CANCEL", btn_type="secondary", on_release=self.dismiss)
        btn_save = CyberButton(text="SAVE SUBJECT", btn_type="primary", on_release=self.save_person)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_save)
        content.add_widget(btn_box)

        self.content = content

    def save_person(self, *args):
        name = self.in_name.text.strip()
        code = self.in_code.text.strip() or None
        email = self.in_email.text.strip() or None
        notes = self.in_notes.text.strip() or None

        if not name:
            self.lbl_msg.text = "Name is required."
            return

        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                if code:
                    exists = Person.query.filter_by(person_code=code).first()
                    if exists:
                        self.lbl_msg.text = f"Code '{code}' already in use."
                        return

                p = Person(name=name, person_code=code, email=email, notes=notes, status="active")
                db.session.add(p)
                db.session.commit()
                self.dismiss()
                if self.on_success_callback:
                    self.on_success_callback()
        except Exception as e:
            self.lbl_msg.text = str(e)


class PeopleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))

        # Header Bar
        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(12))
        lbl = Label(text="[b]SUBJECT DIRECTORY & BIOMETRICS[/b]", markup=True, font_size="16sp", color=COLORS["text_main"], halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        header.add_widget(lbl)

        btn_add = CyberButton(text="+ REGISTER PERSON", btn_type="primary", size_hint=(None, 1), width=dp(170), on_release=self.open_add_dialog)
        btn_refresh = CyberButton(text="REFRESH", btn_type="secondary", size_hint=(None, 1), width=dp(110), on_release=self.load_people)
        header.add_widget(btn_add)
        header.add_widget(btn_refresh)
        root.add_widget(header)

        # Directory Card
        card = CyberCard(orientation="vertical", padding=[dp(14), dp(12)], spacing=dp(8), size_hint_y=1, radius=8)

        # Table Header
        tbl_hdr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        cols = [("ID", 0.08), ("NAME", 0.24), ("CODE", 0.16), ("STATUS", 0.14), ("SAMPLES", 0.12), ("LAST SEEN", 0.14), ("ACTIONS", 0.12)]
        for name, w in cols:
            h_lbl = Label(text=f"[b]{name}[/b]", markup=True, font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=w)
            h_lbl.bind(size=h_lbl.setter("text_size"))
            tbl_hdr.add_widget(h_lbl)
        card.add_widget(tbl_hdr)

        # Scrollable rows
        scroll = ScrollView(size_hint=(1, 1))
        self.people_layout = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.people_layout.bind(minimum_height=self.people_layout.setter("height"))
        scroll.add_widget(self.people_layout)
        card.add_widget(scroll)

        root.add_widget(card)
        self.add_widget(root)

    def on_enter(self):
        self.load_people()

    def open_add_dialog(self, *args):
        popup = AddPersonPopup(on_success_callback=self.load_people)
        popup.open()

    def load_people(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                people = Person.query.order_by(Person.created_at.desc()).all()
                self.people_layout.clear_widgets()

                if not people:
                    empty = Label(text="No subjects enrolled yet. Click '+ REGISTER PERSON' to add one.", font_size="13sp", color=COLORS["text_muted"], size_hint_y=None, height=dp(40))
                    self.people_layout.add_widget(empty)
                    return

                for p in people:
                    p_id = p.id
                    p_name = p.name
                    p_status = p.status
                    p_samples = p.sample_count
                    p_code = p.person_code or "N/A"
                    last_ev = p.events.order_by(Event.timestamp.desc()).first()
                    p_last_seen = last_ev.timestamp.strftime("%Y-%m-%d %H:%M") if last_ev else "Never"

                    row = CyberCard(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=dp(40),
                        padding=[dp(8), dp(4)],
                        spacing=dp(6),
                        bg_color=COLORS["card_hover"],
                        radius=4
                    )

                    l_id = Label(text=f"#{p_id}", font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=0.08)
                    l_id.bind(size=l_id.setter("text_size"))
                    row.add_widget(l_id)

                    l_name = Label(text=f"[b]{p_name}[/b]", markup=True, font_size="12sp", color=COLORS["text_main"], halign="left", size_hint_x=0.24)
                    l_name.bind(size=l_name.setter("text_size"))
                    row.add_widget(l_name)

                    l_code = Label(text=p_code, font_size="11sp", color=COLORS["info"], halign="left", size_hint_x=0.16)
                    l_code.bind(size=l_code.setter("text_size"))
                    row.add_widget(l_code)

                    b_status = StatusBadge(text=p_status, size_hint_x=0.14)
                    row.add_widget(b_status)

                    l_samples = Label(text=f"{p_samples} samples", font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=0.12)
                    l_samples.bind(size=l_samples.setter("text_size"))
                    row.add_widget(l_samples)

                    l_seen = Label(text=p_last_seen, font_size="11sp", color=COLORS["text_muted"], halign="left", size_hint_x=0.14)
                    l_seen.bind(size=l_seen.setter("text_size"))
                    row.add_widget(l_seen)

                    # Action button (Delete)
                    btn_del = CyberButton(
                        text="DELETE",
                        btn_type="danger",
                        size_hint_x=0.12,
                        on_release=lambda instance, pid=p_id: self.delete_person(pid)
                    )
                    row.add_widget(btn_del)

                    self.people_layout.add_widget(row)

        except Exception as e:
            print(f"[PeopleScreen] Error loading people: {e}")

    def delete_person(self, person_id):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                person = Person.query.get(person_id)
                if person:
                    for emb in person.embeddings:
                        if emb.sample_image_path:
                            storage_service.delete_file(emb.sample_image_path)
                    db.session.delete(person)
                    db.session.commit()
                    face_recognition_service.train_database()
                    self.load_people()
        except Exception as e:
            print(f"[PeopleScreen] Error deleting person {person_id}: {e}")
