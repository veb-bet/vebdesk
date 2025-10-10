import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QLineEdit, QLabel, QListWidget, QListWidgetItem, QInputDialog, QCalendarWidget,
    QFileDialog, QMessageBox, QStackedWidget, QHBoxLayout, QGraphicsDropShadowEffect,
    QComboBox, QCheckBox, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFontDatabase, QFont, QColor

_notify_backend = None
try:
    from plyer import notification as plyer_notify
    _notify_backend = "plyer"
except Exception:
    try:
        import notify2
        notify2.init("VebDesk")
        _notify_backend = "notify2"
    except Exception:
        _notify_backend = None

def send_system_notification(title: str, message: str):
    if _notify_backend == "plyer":
        try:
            plyer_notify.notify(title=title, message=message, timeout=5)
            return
        except Exception:
            pass
    elif _notify_backend == "notify2":
        try:
            n = notify2.Notification(title, message)
            n.set_timeout(5000)
            n.show()
            return
        except Exception:
            pass
    QMessageBox.information(None, title, message)

DB_FILE = "vebdesk.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, email TEXT UNIQUE, phone TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, tags TEXT, color TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, date TEXT, color TEXT, reminder_time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY, user_id INTEGER, filepath TEXT, category TEXT, color TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS actions_log
             (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings
             (user_id INTEGER PRIMARY KEY,
              theme TEXT DEFAULT 'Neon Yellow',
              dark_mode INTEGER DEFAULT 0,
              font_choice TEXT DEFAULT 'Monospace',
              neon_anim INTEGER DEFAULT 1,
              default_reminder TEXT DEFAULT NULL)''')
conn.commit()

THEMES = {
    "Neon Yellow": {"background": "#071019", "accent": "#FFD500", "tab_selected_bg": "#FFD500", "tab_selected_fg": "#071019"},
    "Neon Green":  {"background": "#061914", "accent": "#00FF66", "tab_selected_bg": "#00FF66", "tab_selected_fg": "#061914"},
    "Neon Purple": {"background": "#10071A", "accent": "#CC00FF", "tab_selected_bg": "#CC00FF", "tab_selected_fg": "#10071A"},
}

def theme_to_stylesheet(theme, dark_mode=False):
    if not dark_mode:
        bg = theme["background"]
        input_bg = "#0b1418"
        text_color = "#E6E6E6"
        label_color = theme["accent"]
        tab_sel_bg = theme["tab_selected_bg"]
        tab_sel_fg = theme["tab_selected_fg"]
    else:
        bg = "#46484E"
        input_bg = "#9FA0A1"
        text_color = "#111111"
        label_color = theme["accent"]
        tab_sel_bg = theme["tab_selected_bg"]
        tab_sel_fg = "#605C61"

    ac = theme["accent"]; tbg = tab_sel_bg; tfg = tab_sel_fg
    return f"""
QMainWindow {{ background-color: {bg}; }}
QLabel {{ color: {label_color}; font-weight: bold; font-family: monospace; }}
QPushButton {{
    background-color: transparent;
    color: {ac};
    border: 2px solid {ac};
    border-radius: 3px;
    padding: 8px;
    font-family: monospace;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {ac}; color: {bg}; }}
QLineEdit, QTextEdit, QListWidget, QCalendarWidget {{
    background-color: {input_bg};
    color: {text_color};
    border: 1px solid #2a3034;
    border-left: 3px solid {ac};
    border-radius: 3px;
    padding: 6px;
    font-family: monospace;
}}
QTabBar::tab {{ padding: 8px 12px; color: #9aa7af; }}
QTabBar::tab:selected {{ color: {tfg}; background-color: {tbg}; border: 1px solid {ac}; border-radius: 3px; }}
"""

def apply_neon_pulse(widget, color_hex, radius_min=4, radius_max=18, duration=1200):
    effect = QGraphicsDropShadowEffect()
    color = QColor(color_hex); color.setAlpha(200)
    effect.setColor(color); effect.setOffset(0, 0); effect.setBlurRadius(radius_min)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"blurRadius")
    anim.setStartValue(radius_min); anim.setEndValue(radius_max)
    anim.setDuration(duration); anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.setLoopCount(-1); anim.start()
    if not hasattr(widget, "_neon_anim_refs"): widget._neon_anim_refs = []
    widget._neon_anim_refs.append((effect, anim))
    return effect, anim

def load_custom_font(font_choice=None):
    font_files = ["Orbitron-Regular.ttf", "VT323-Regular.ttf"]
    if font_choice == "Cyberpunk":
        for fname in font_files:
            if os.path.exists(fname):
                fid = QFontDatabase.addApplicationFont(fname)
                families = QFontDatabase.applicationFontFamilies(fid)
                if families: return QFont(families[0], 11)
        return QFont("Courier New", 11)
    else:
        if os.path.exists("VT323-Regular.ttf"):
            fid = QFontDatabase.addApplicationFont("VT323-Regular.ttf")
            families = QFontDatabase.applicationFontFamilies(fid)
            if families: return QFont(families[0], 11)
        return QFont("Courier New", 10)

class VebDesk(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("VebDesk Pro — Cyberpunk")
        self.setGeometry(80, 60, 1100, 750)

        self.current_theme = THEMES["Neon Yellow"]
        self.current_theme_name = "Neon Yellow"
        self.dark_mode = False
        self.font_choice = "Monospace"
        self.neon_animation_enabled = True
        self.default_reminder = None

        self.load_user_settings()

        self.setStyleSheet(theme_to_stylesheet(self.current_theme, self.dark_mode))
        self.setFont(load_custom_font(self.font_choice))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.init_tabs()
        self.init_theme_switch()
        self.init_reminder_checker()

    def init_tabs(self):
        self.init_notes_tab(); self.init_calendar_tab(); self.init_calculator_tab()
        self.init_messages_tab(); self.init_storage_tab(); self.init_timer_tab()
        self.init_search_tab(); self.init_profile_tab()

    def init_notes_tab(self):
        self.notes_tab = QWidget(); layout = QVBoxLayout()
        self.note_title = QLineEdit(); self.note_title.setPlaceholderText("TITLE")
        self.note_tags = QLineEdit(); self.note_tags.setPlaceholderText("TAGS (comma)")
        self.note_color = QLineEdit(); self.note_color.setPlaceholderText("COLOR (#HEX) optional")
        self.note_editor = QTextEdit()
        save_btn = QPushButton("SAVE"); save_btn.clicked.connect(self.save_note)
        if self.neon_animation_enabled:
            apply_neon_pulse(save_btn, self.current_theme["accent"])
        self.notes_list = QListWidget(); self.notes_list.itemClicked.connect(self.load_note)
        export_btn = QPushButton("EXPORT"); export_btn.clicked.connect(self.export_notes)
        import_btn = QPushButton("IMPORT"); import_btn.clicked.connect(self.import_notes)
        row = QHBoxLayout(); row.addWidget(save_btn); row.addWidget(export_btn); row.addWidget(import_btn)
        layout.addWidget(QLabel("NOTES"))
        layout.addWidget(self.note_title); layout.addWidget(self.note_tags); layout.addWidget(self.note_color)
        layout.addWidget(self.note_editor); layout.addLayout(row)
        layout.addWidget(QLabel("SAVED")); layout.addWidget(self.notes_list)
        self.notes_tab.setLayout(layout); self.tabs.addTab(self.notes_tab, "NOTES"); self.refresh_notes()

    def save_note(self):
        title = self.note_title.text() or "UNTITLED"; content = self.note_editor.toPlainText()
        tags = self.note_tags.text(); color = self.note_color.text() or self.current_theme["accent"]
        c.execute("INSERT INTO notes (user_id, title, content, tags, color) VALUES (?, ?, ?, ?, ?)",
                  (self.user_id, title, content, tags, color)); conn.commit()
        self.note_title.clear(); self.note_tags.clear(); self.note_color.clear(); self.note_editor.clear()
        self.refresh_notes(); self.log_action(f"NOTE CREATED: {title}"); send_system_notification("Note saved", title)

    def refresh_notes(self):
        self.notes_list.clear()
        c.execute("SELECT id, title, tags, color FROM notes WHERE user_id=?", (self.user_id,))
        for nid, title, tags, color in c.fetchall():
            text = f"{title} [{tags}]"; item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, nid)
            try: item.setBackground(QColor(color))
            except: pass
            self.notes_list.addItem(item)

    def load_note(self, item):
        nid = item.data(Qt.ItemDataRole.UserRole)
        c.execute("SELECT title, content, tags, color FROM notes WHERE id=?", (nid,))
        res = c.fetchone()
        if res: title, content, tags, color = res; self.note_title.setText(title); self.note_editor.setText(content)
        self.note_tags.setText(tags); self.note_color.setText(color or "")

    def export_notes(self):
        fname, _ = QFileDialog.getSaveFileName(self, "EXPORT NOTES", "", "Text Files (*.txt)")
        if fname:
            c.execute("SELECT title, content, tags, color FROM notes WHERE user_id=?", (self.user_id,))
            notes = c.fetchall()
            with open(fname, "w", encoding="utf-8") as f:
                for title, content, tags, color in notes:
                    f.write(f"=== {title} ===\nTAGS: {tags}\nCOLOR: {color}\n{content}\n\n")
            QMessageBox.information(self, "EXPORT", "Notes exported.")

    def import_notes(self):
        fname, _ = QFileDialog.getOpenFileName(self, "IMPORT NOTES", "", "Text Files (*.txt)")
        if fname:
            with open(fname, "r", encoding="utf-8") as f:
                content = f.read()
                sections = content.split("===")
                for sec in sections:
                    if sec.strip():
                        lines = sec.strip().splitlines()
                        title = lines[0].strip(); tags = "Imported"; color = self.current_theme["accent"]
                        note_content = "\n".join(lines[1:])
                        c.execute("INSERT INTO notes (user_id, title, content, tags, color) VALUES (?, ?, ?, ?, ?)",
                                  (self.user_id, title, note_content, tags, color))
                conn.commit(); self.refresh_notes(); QMessageBox.information(self, "IMPORT", "Notes imported.")

    def init_calendar_tab(self):
        self.calendar_tab = QWidget(); layout = QVBoxLayout()
        self.calendar = QCalendarWidget(); self.calendar.setGridVisible(True); self.calendar.clicked.connect(self.show_events)
        self.events_list = QListWidget()
        add_event_btn = QPushButton("ADD EVENT"); add_event_btn.clicked.connect(self.add_event)
        if self.neon_animation_enabled:
            apply_neon_pulse(add_event_btn, self.current_theme["accent"])
        layout.addWidget(QLabel("CALENDAR")); layout.addWidget(self.calendar)
        layout.addWidget(QLabel("EVENTS")); layout.addWidget(self.events_list)
        layout.addWidget(add_event_btn); self.calendar_tab.setLayout(layout)
        self.tabs.addTab(self.calendar_tab, "CALENDAR"); self.show_events()

    def add_event(self):
        title, ok = QInputDialog.getText(self, "New Event", "Event Title")
        if ok and title:
            date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            prefill = self.default_reminder if self.default_reminder else ""
            reminder, ok2 = QInputDialog.getText(self, "Reminder (HH:MM)", "Reminder time (optional)", text=prefill)
            color = self.current_theme["accent"]
            c.execute("INSERT INTO events (user_id, title, date, color, reminder_time) VALUES (?, ?, ?, ?, ?)",
                      (self.user_id, title, date, color, reminder if ok2 and reminder.strip() else None))
            conn.commit(); self.show_events(); send_system_notification("Event added", title)

    def show_events(self):
        self.events_list.clear(); date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        c.execute("SELECT id, title FROM events WHERE user_id=? AND date=?", (self.user_id, date))
        for eid, title in c.fetchall(): item = QListWidgetItem(title); self.events_list.addItem(item)

    def init_calculator_tab(self):
        self.calc_tab = QWidget(); layout = QVBoxLayout()
        self.calc_input = QLineEdit(); self.calc_input.setPlaceholderText("expression e.g. 2+2*3")
        self.calc_result = QLabel("RESULT:")
        calc_btn = QPushButton("EVAL"); calc_btn.clicked.connect(self.calculate)
        layout.addWidget(self.calc_input); layout.addWidget(calc_btn); layout.addWidget(self.calc_result)
        self.calc_tab.setLayout(layout); self.tabs.addTab(self.calc_tab, "CALCULATOR")

    def calculate(self):
        expr = self.calc_input.text()
        try: result = eval(expr, {}, {}); self.calc_result.setText(f"RESULT: {result}")
        except Exception as e: self.calc_result.setText(f"ERROR: {e}")

    def init_messages_tab(self):
        self.messages_tab = QWidget(); layout = QVBoxLayout()
        self.msg_list = QListWidget(); self.msg_input = QLineEdit(); self.msg_input.setPlaceholderText("WRITE MESSAGE")
        send_btn = QPushButton("SEND"); send_btn.clicked.connect(self.send_message)
        layout.addWidget(QLabel("MESSAGES")); layout.addWidget(self.msg_list)
        row = QHBoxLayout(); row.addWidget(self.msg_input); row.addWidget(send_btn); layout.addLayout(row)
        self.messages_tab.setLayout(layout); self.tabs.addTab(self.messages_tab, "MESSAGES"); self.refresh_messages()

    def send_message(self):
        text = self.msg_input.text(); self.msg_input.clear()
        if text:
            c.execute("INSERT INTO messages (user_id, text) VALUES (?, ?)", (self.user_id, text)); conn.commit()
            self.refresh_messages(); send_system_notification("Message sent", text)

    def refresh_messages(self):
        self.msg_list.clear(); c.execute("SELECT text, timestamp FROM messages WHERE user_id=?", (self.user_id,))
        for text, ts in c.fetchall(): self.msg_list.addItem(f"{ts}: {text}")

    def init_storage_tab(self):
        self.storage_tab = QWidget(); layout = QVBoxLayout()
        self.file_list = QListWidget(); add_file_btn = QPushButton("ADD FILE"); add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("FILES")); layout.addWidget(self.file_list); layout.addWidget(add_file_btn)
        self.storage_tab.setLayout(layout); self.tabs.addTab(self.storage_tab, "STORAGE"); self.refresh_files()

    def add_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select File")
        if fname:
            category, ok = QInputDialog.getText(self, "Category", "File category")
            c.execute("INSERT INTO files (user_id, filepath, category, color) VALUES (?, ?, ?, ?)",
                      (self.user_id, fname, category if ok else "None", self.current_theme["accent"])); conn.commit()
            self.refresh_files(); send_system_notification("File added", os.path.basename(fname))

    def refresh_files(self):
        self.file_list.clear(); c.execute("SELECT filepath, category FROM files WHERE user_id=?", (self.user_id,))
        for path, cat in c.fetchall(): self.file_list.addItem(f"{os.path.basename(path)} [{cat}]")

    def init_timer_tab(self):
        self.timer_tab = QWidget(); layout = QVBoxLayout()
        self.timer_input = QLineEdit(); self.timer_input.setPlaceholderText("minutes (e.g. 25)")
        self.timer_label = QLabel("TIMER: 00:00")
        start_btn = QPushButton("START"); stop_btn = QPushButton("STOP")
        start_btn.clicked.connect(self.start_timer); stop_btn.clicked.connect(self.stop_timer)
        layout.addWidget(self.timer_input); row = QHBoxLayout(); row.addWidget(start_btn); row.addWidget(stop_btn)
        layout.addLayout(row); layout.addWidget(self.timer_label); self.timer_tab.setLayout(layout); self.tabs.addTab(self.timer_tab, "TIMER")
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_timer); self.time_left = 0

    def start_timer(self):
        try: minutes = int(self.timer_input.text()); self.time_left = minutes*60; self.timer.start(1000)
        except: QMessageBox.warning(self, "ERROR", "Invalid number")

    def stop_timer(self):
        self.timer.stop(); self.timer_label.setText("TIMER: 00:00")

    def update_timer(self):
        if self.time_left>0: self.time_left -=1; m,s = divmod(self.time_left,60); self.timer_label.setText(f"TIMER: {m:02d}:{s:02d}")
        else: self.timer.stop(); send_system_notification("Timer finished", "Time is up!")

    def init_search_tab(self):
        self.search_tab = QWidget(); layout = QVBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("keyword")
        search_btn = QPushButton("SEARCH"); search_btn.clicked.connect(self.search_all)
        self.search_results = QListWidget()
        layout.addWidget(self.search_input); layout.addWidget(search_btn); layout.addWidget(QLabel("RESULTS")); layout.addWidget(self.search_results)
        self.search_tab.setLayout(layout); self.tabs.addTab(self.search_tab, "SEARCH")

    def search_all(self):
        keyword = self.search_input.text(); self.search_results.clear()
        tables = [("notes", "title || content"), ("messages", "text"), ("events", "title")]
        for table, col in tables:
            c.execute(f"SELECT * FROM {table} WHERE user_id=? AND {col} LIKE ?", (self.user_id, f"%{keyword}%"))
            for row in c.fetchall(): self.search_results.addItem(f"{table}: {row}")

    def init_profile_tab(self):
        self.profile_tab = QWidget(); layout = QVBoxLayout()
        layout.addWidget(QLabel("PROFILE & SETTINGS"))
        self.theme_combo = QComboBox(); self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setCurrentText(self.current_theme_name); self.theme_combo.currentTextChanged.connect(self.change_theme)
        layout.addWidget(QLabel("Select Theme:")); layout.addWidget(self.theme_combo)

        self.dark_checkbox = QCheckBox("Ligth Mode"); self.dark_checkbox.setChecked(self.dark_mode)
        self.dark_checkbox.stateChanged.connect(self.toggle_dark_from_ui)
        layout.addWidget(self.dark_checkbox)

        self.font_combo = QComboBox(); self.font_combo.addItems(["Monospace", "Cyberpunk"])
        self.font_combo.setCurrentText(self.font_choice); self.font_combo.currentTextChanged.connect(self.change_font)
        layout.addWidget(QLabel("Select Font:")); layout.addWidget(self.font_combo)

        self.neon_checkbox = QCheckBox("Enable Neon Animation"); self.neon_checkbox.setChecked(bool(self.neon_animation_enabled))
        self.neon_checkbox.stateChanged.connect(self.toggle_neon_animation)
        layout.addWidget(self.neon_checkbox)

        row = QHBoxLayout()
        self.reminder_time_edit = QTimeEdit(); self.reminder_time_edit.setDisplayFormat("HH:mm")
        if self.default_reminder:
            try:
                hh,mm = map(int, self.default_reminder.split(":"))
                from PyQt6.QtCore import QTime
                self.reminder_time_edit.setTime(QTime(hh,mm))
            except Exception:
                pass
        row.addWidget(QLabel("Default reminder:")); row.addWidget(self.reminder_time_edit)
        layout.addLayout(row)
        save_rem_btn = QPushButton("SAVE REMINDER"); save_rem_btn.clicked.connect(self.save_default_reminder)
        layout.addWidget(save_rem_btn)
        reset_btn = QPushButton("RESET SETTINGS TO DEFAULTS"); reset_btn.clicked.connect(self.reset_defaults)
        layout.addWidget(reset_btn)

        self.profile_tab.setLayout(layout); self.tabs.addTab(self.profile_tab, "PROFILE")

    def change_theme(self, text):
        if text in THEMES:
            self.current_theme_name = text
            self.current_theme = THEMES[text]
            self.apply_style_and_save()

    def toggle_dark_from_ui(self, state):
        self.dark_mode = bool(state)
        self.apply_style_and_save()

    def change_font(self, text):
        self.font_choice = text
        self.setFont(load_custom_font(self.font_choice))
        self.save_settings()

    def toggle_neon_animation(self, state):
        self.neon_animation_enabled = bool(state)
        self.save_settings()

    def save_default_reminder(self):
        t = self.reminder_time_edit.time().toString("HH:mm")
        self.default_reminder = t
        self.save_settings()
        QMessageBox.information(self, "OK", f"Default reminder set to {t}")

    def apply_style_and_save(self):
        self.setStyleSheet(theme_to_stylesheet(self.current_theme, self.dark_mode))
        self.save_settings()

    def reset_defaults(self):
        self.current_theme_name = "Neon Yellow"
        self.current_theme = THEMES[self.current_theme_name]
        self.dark_mode = False
        self.font_choice = "Monospace"
        self.neon_animation_enabled = True
        self.default_reminder = None
        self.theme_combo.setCurrentText(self.current_theme_name)
        self.dark_checkbox.setChecked(self.dark_mode)
        self.font_combo.setCurrentText(self.font_choice)
        self.neon_checkbox.setChecked(self.neon_animation_enabled)
        from PyQt6.QtCore import QTime
        self.reminder_time_edit.setTime(QTime(0,0))
        self.apply_style_and_save()
        self.setFont(load_custom_font(self.font_choice))
        QMessageBox.information(self, "RESET", "Settings reset to defaults.")

    def load_user_settings(self):
        c.execute("SELECT theme, dark_mode, font_choice, neon_anim, default_reminder FROM settings WHERE user_id=?", (self.user_id,))
        res = c.fetchone()
        if res:
            theme, dark_mode, font_choice, neon_anim, default_reminder = res
            if theme in THEMES:
                self.current_theme_name = theme
                self.current_theme = THEMES[theme]
            self.dark_mode = bool(dark_mode)
            self.font_choice = font_choice or "Monospace"
            self.neon_animation_enabled = bool(neon_anim)
            self.default_reminder = default_reminder
        else:
            c.execute("INSERT OR REPLACE INTO settings (user_id, theme, dark_mode, font_choice, neon_anim, default_reminder) VALUES (?, ?, ?, ?, ?, ?)",
                      (self.user_id, self.current_theme_name, int(self.dark_mode), self.font_choice, int(self.neon_animation_enabled), self.default_reminder))
            conn.commit()

    def save_settings(self):
        c.execute("INSERT OR REPLACE INTO settings (user_id, theme, dark_mode, font_choice, neon_anim, default_reminder) VALUES (?, ?, ?, ?, ?, ?)",
                  (self.user_id, self.current_theme_name, int(self.dark_mode), self.font_choice, int(self.neon_animation_enabled), self.default_reminder))
        conn.commit()

    def init_theme_switch(self):
        theme_btn = QPushButton("SWITCH THEME")
        theme_btn.setFixedHeight(28)
        theme_btn.clicked.connect(self.toggle_dark_corner)
        try:
            self.tabs.setCornerWidget(theme_btn, Qt.Corner.TopRightCorner)
        except Exception:
            pass

    def toggle_dark_corner(self):
        self.dark_mode = not self.dark_mode
        try:
            if hasattr(self, "dark_checkbox") and isinstance(self.dark_checkbox, QCheckBox):
                self.dark_checkbox.setChecked(self.dark_mode)
        except Exception:
            pass
        self.apply_style_and_save()

    def init_reminder_checker(self):
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.check_reminders()
        self.reminder_timer.start(60 * 1000)

    def check_reminders(self):
        today = QDate.currentDate().toString("yyyy-MM-dd")
        now = QTime.currentTime().toString("HH:mm")
        try:
            c.execute("SELECT title, reminder_time FROM events WHERE user_id=? AND date=? AND reminder_time IS NOT NULL", (self.user_id, today))
            for title, reminder in c.fetchall():
                if reminder and reminder.strip() == now:
                    send_system_notification("Reminder", f"{title} — {reminder}")
        except Exception:
            pass

    def log_action(self, text):
        try:
            c.execute("INSERT INTO actions_log (user_id, action) VALUES (?, ?)", (self.user_id, text))
            conn.commit()
        except Exception:
            pass

class LoginRegister(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VebDesk — LOGIN / REGISTER"); self.setGeometry(280,180,520,380)
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack); self.setFont(load_custom_font())
        self.init_login_page(); self.init_register_page()

    def init_login_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.login_email = QLineEdit(); self.login_email.setPlaceholderText("email")
        self.login_pass = QLineEdit(); self.login_pass.setPlaceholderText("password"); self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("LOGIN"); login_btn.clicked.connect(self.login)
        switch_btn = QPushButton("NO ACCOUNT? REGISTER"); switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(QLabel("LOGIN")); layout.addWidget(self.login_email); layout.addWidget(self.login_pass)
        layout.addWidget(login_btn); layout.addWidget(switch_btn); page.setLayout(layout); self.stack.addWidget(page)

    def init_register_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.reg_email = QLineEdit(); self.reg_email.setPlaceholderText("email")
        self.reg_phone = QLineEdit(); self.reg_phone.setPlaceholderText("phone (optional)")
        self.reg_pass = QLineEdit(); self.reg_pass.setPlaceholderText("password"); self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_btn = QPushButton("REGISTER"); reg_btn.clicked.connect(self.register)
        switch_btn = QPushButton("ALREADY HAVE ACCOUNT? LOGIN"); switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(QLabel("REGISTER")); layout.addWidget(self.reg_email); layout.addWidget(self.reg_phone)
        layout.addWidget(self.reg_pass); layout.addWidget(reg_btn); layout.addWidget(switch_btn); page.setLayout(layout); self.stack.addWidget(page)

    def login(self):
        email = self.login_email.text().strip(); password = self.login_pass.text().strip()
        if not (email and password): QMessageBox.warning(self, "ERROR", "Enter email and password"); return
        c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password)); res = c.fetchone()
        if res: self.main = VebDesk(res[0]); self.main.show(); self.close()
        else: QMessageBox.warning(self, "ERROR", "Invalid email or password")

    def register(self):
        email = self.reg_email.text().strip(); phone = self.reg_phone.text().strip(); password = self.reg_pass.text().strip()
        if not (email and password): QMessageBox.warning(self, "ERROR", "Enter email and password"); return
        try:
            c.execute("INSERT INTO users (email, phone, password) VALUES (?, ?, ?)", (email, phone, password)); conn.commit()
            user_id = c.lastrowid
            c.execute("INSERT OR REPLACE INTO settings (user_id, theme, dark_mode, font_choice, neon_anim, default_reminder) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, "Neon Yellow", 0, "Monospace", 1, None))
            conn.commit()
            QMessageBox.information(self, "OK", "Registered. You can log in."); self.stack.setCurrentIndex(0)
        except sqlite3.IntegrityError: QMessageBox.warning(self, "ERROR", "Email or phone already exists")


if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(load_custom_font())
    login = LoginRegister(); login.show(); sys.exit(app.exec())
