import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QLineEdit, QLabel, QFileDialog, QListWidget, QStackedWidget,
    QMessageBox, QHBoxLayout, QInputDialog, QCalendarWidget, QListWidgetItem,
    QToolTip
)
from PyQt6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QIcon, QPalette, QBrush, QLinearGradient

# === База данных ===
conn = sqlite3.connect("vebdesk.db")
c = conn.cursor()

# Таблицы (если не созданы)
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, email TEXT UNIQUE, phone TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, tags TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY, user_id INTEGER, filepath TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, date TEXT, color TEXT)''')
conn.commit()

# === Темы с градиентами ===
LIGHT_THEME = """
QMainWindow { 
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #FFF0F5, stop:1 #FFE4E1);
}
QLabel { color: #800080; font-weight: bold; }
QPushButton { background-color: #FFB6C1; border-radius: 12px; padding: 8px; }
QPushButton:hover { background-color: #FF69B4; }
QTextEdit, QLineEdit, QListWidget, QCalendarWidget { 
    background-color: #FFF0F5; border: 1px solid #FFB6C1; border-radius: 8px; 
}
QTabBar::tab:selected { background-color: #FFB6C1; border-radius: 10px; }
"""

DARK_THEME = """
QMainWindow { 
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #2C003E, stop:1 #4B0082);
}
QLabel { color: #FFB6C1; font-weight: bold; }
QPushButton { background-color: #800080; color: white; border-radius: 12px; padding: 8px; }
QPushButton:hover { background-color: #DA70D6; }
QTextEdit, QLineEdit, QListWidget, QCalendarWidget { 
    background-color: #4B0082; color: white; border: 1px solid #DA70D6; border-radius: 8px; 
}
QTabBar::tab:selected { background-color: #800080; border-radius: 10px; }
"""

# === Главное окно ===
class VebDesk(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("💖 VebDesk Ultimate 💖")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(LIGHT_THEME)
        self.dark_mode = False

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_notes_tab()
        self.init_calendar_tab()
        self.init_calculator_tab()
        self.init_messages_tab()
        self.init_storage_tab()
        self.init_theme_switch()

        # Анимация появления
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.start()

    # === Заметки с тегами и cute emoji ===
    def init_notes_tab(self):
        self.notes_tab = QWidget()
        layout = QVBoxLayout()
        self.note_editor = QTextEdit()
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Название заметки 📝")
        self.note_tags = QLineEdit()
        self.note_tags.setPlaceholderText("Теги через запятую 🌸")
        save_btn = QPushButton("💾 Сохранить заметку")
        save_btn.setToolTip("Сохраняет заметку с тегами и эмодзи")
        save_btn.clicked.connect(self.save_note)
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.load_note)
        layout.addWidget(QLabel("Ваши милые заметки 💕:"))
        layout.addWidget(self.note_title)
        layout.addWidget(self.note_tags)
        layout.addWidget(self.note_editor)
        layout.addWidget(save_btn)
        layout.addWidget(QLabel("Сохранённые заметки 🗂️:"))
        layout.addWidget(self.notes_list)
        self.notes_tab.setLayout(layout)
        self.tabs.addTab(self.notes_tab, "📝 Заметки")
        self.refresh_notes()

    def save_note(self):
        title = self.note_title.text() or "Без названия 🐱"
        content = self.note_editor.toPlainText()
        tags = self.note_tags.text()
        c.execute("INSERT INTO notes (user_id, title, content, tags) VALUES (?, ?, ?, ?)",
                  (self.user_id, title, content, tags))
        conn.commit()
        QMessageBox.information(self, "Ура!", "Заметка сохранена 💖")
        self.note_editor.clear()
        self.note_title.clear()
        self.note_tags.clear()
        self.refresh_notes()

    def refresh_notes(self):
        self.notes_list.clear()
        c.execute("SELECT id, title, tags FROM notes WHERE user_id=?", (self.user_id,))
        for note_id, title, tags in c.fetchall():
            item = QListWidgetItem(f"{title} [{tags}] ✨")
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.notes_list.addItem(item)

    def load_note(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        c.execute("SELECT title, content, tags FROM notes WHERE id=?", (note_id,))
        res = c.fetchone()
        if res:
            title, content, tags = res
            self.note_title.setText(title)
            self.note_editor.setText(content)
            self.note_tags.setText(tags)

    # === Календарь с cute emoji и цветами ===
    def init_calendar_tab(self):
        self.calendar_tab = QWidget()
        layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.show_events)
        self.events_list = QListWidget()
        add_event_btn = QPushButton("➕ Добавить событие 🎀")
        add_event_btn.setToolTip("Добавляет новое событие в выбранный день")
        add_event_btn.clicked.connect(self.add_event)
        layout.addWidget(QLabel("Календарь 📅:"))
        layout.addWidget(self.calendar)
        layout.addWidget(QLabel("События на выбранный день ✨:"))
        layout.addWidget(self.events_list)
        layout.addWidget(add_event_btn)
        self.calendar_tab.setLayout(layout)
        self.tabs.addTab(self.calendar_tab, "📅 Календарь")
        self.show_events()

    def add_event(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        title, ok = QInputDialog.getText(self, "Новое событие 🎉", "Название события:")
        if ok and title:
            color = "#FF69B4"
            c.execute("INSERT INTO events (user_id, title, date, color) VALUES (?, ?, ?, ?)",
                      (self.user_id, title, date, color))
            conn.commit()
            self.show_events()

    def show_events(self):
        self.events_list.clear()
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        c.execute("SELECT title, color FROM events WHERE user_id=? AND date=?", (self.user_id, date))
        for title, color in c.fetchall():
            item = QListWidgetItem(f"{title} ✨")
            item.setBackground(QColor(color))
            self.events_list.addItem(item)

    # === Калькулятор с cute emoji ===
    def init_calculator_tab(self):
        self.calc_tab = QWidget()
        layout = QVBoxLayout()
        self.calc_input = QLineEdit()
        self.calc_input.setPlaceholderText("Введите выражение ➗")
        self.calc_result = QLabel("Результат: 🤔")
        calc_btn = QPushButton("➗ Вычислить 🐱")
        calc_btn.clicked.connect(self.calculate)
        layout.addWidget(self.calc_input)
        layout.addWidget(calc_btn)
        layout.addWidget(self.calc_result)
        self.calc_tab.setLayout(layout)
        self.tabs.addTab(self.calc_tab, "🧮 Калькулятор")

    def calculate(self):
        expr = self.calc_input.text()
        try:
            result = eval(expr)
            self.calc_result.setText(f"Результат: {result} ✨")
        except Exception as e:
            self.calc_result.setText(f"Ошибка: {e} ❌")

    # === Сообщения с cute emoji ===
    def init_messages_tab(self):
        self.messages_tab = QWidget()
        layout = QVBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Напишите сообщение 💌")
        self.msg_list = QListWidget()
        send_btn = QPushButton("📨 Отправить 💖")
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.msg_list)
        layout.addWidget(self.msg_input)
        layout.addWidget(send_btn)
        self.messages_tab.setLayout(layout)
        self.tabs.addTab(self.messages_tab, "💌 Сообщения")
        self.refresh_messages()

    def send_message(self):
        text = self.msg_input.text()
        if text:
            c.execute("INSERT INTO messages (user_id, text, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
                      (self.user_id, text))
            conn.commit()
            self.msg_list.addItem(f"Вы: {text} 💖")
            self.msg_input.clear()

    def refresh_messages(self):
        self.msg_list.clear()
        c.execute("SELECT text FROM messages WHERE user_id=?", (self.user_id,))
        for (text,) in c.fetchall():
            self.msg_list.addItem(f"Вы: {text} 💌")

    # === Хранилище файлов с cute emoji ===
    def init_storage_tab(self):
        self.storage_tab = QWidget()
        layout = QVBoxLayout()
        self.file_list = QListWidget()
        add_file_btn = QPushButton("📂 Добавить файл 💖")
        add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("Файлы в работе 🗂️:"))
        layout.addWidget(self.file_list)
        layout.addWidget(add_file_btn)
        self.storage_tab.setLayout(layout)
        self.tabs.addTab(self.storage_tab, "🗂️ Хранилище")
        self.refresh_files()

    def add_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if fname:
            c.execute("INSERT INTO files (user_id, filepath) VALUES (?, ?)", (self.user_id, fname))
            conn.commit()
            self.file_list.addItem(f"{fname} ✨")

    def refresh_files(self):
        self.file_list.clear()
        c.execute("SELECT filepath FROM files WHERE user_id=?", (self.user_id,))
        for (filepath,) in c.fetchall():
            self.file_list.addItem(f"{filepath} ✨")

    # === Переключение темы ===
    def init_theme_switch(self):
        theme_btn = QPushButton("🌙 Переключить тему")
        theme_btn.setToolTip("Переключение между светлой и тёмной темой")
        theme_btn.clicked.connect(self.switch_theme)
        self.tabs.setCornerWidget(theme_btn, Qt.Corner.TopRightCorner)

    def switch_theme(self):
        if self.dark_mode:
            self.setStyleSheet(LIGHT_THEME)
            self.dark_mode = False
        else:
            self.setStyleSheet(DARK_THEME)
            self.dark_mode = True


# === Вход и регистрация ===
class LoginRegister(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💖 VebDesk Ultimate: Вход / Регистрация 💖")
        self.setGeometry(300, 200, 450, 350)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_login_page()
        self.init_register_page()

    def init_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email 💌")
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Пароль 🔒")
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Войти 💖")
        login_btn.clicked.connect(self.login)
        switch_btn = QPushButton("Нет аккаунта? Зарегистрироваться 🌸")
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(QLabel("Вход 💌"))
        layout.addWidget(self.login_email)
        layout.addWidget(self.login_pass)
        layout.addWidget(login_btn)
        layout.addWidget(switch_btn)
        page.setLayout(layout)
        self.stack.addWidget(page)

    def init_register_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email 💌")
        self.reg_phone = QLineEdit()
        self.reg_phone.setPlaceholderText("Телефон 📞")
        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Пароль 🔒")
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_btn = QPushButton("Зарегистрироваться 💖")
        reg_btn.clicked.connect(self.register)
        switch_btn = QPushButton("Уже есть аккаунт? Войти 🌸")
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(QLabel("Регистрация 🌸"))
        layout.addWidget(self.reg_email)
        layout.addWidget(self.reg_phone)
        layout.addWidget(self.reg_pass)
        layout.addWidget(reg_btn)
        layout.addWidget(switch_btn)
        page.setLayout(layout)
        self.stack.addWidget(page)

    def login(self):
        email = self.login_email.text()
        password = self.login_pass.text()
        c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
        res = c.fetchone()
        if res:
            self.main_window = VebDesk(res[0])
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка 💔", "Неверный email или пароль")

    def register(self):
        email = self.reg_email.text()
        phone = self.reg_phone.text()
        password = self.reg_pass.text()
        try:
            c.execute("INSERT INTO users (email, phone, password) VALUES (?, ?, ?)", (email, phone, password))
            conn.commit()
            QMessageBox.information(self, "Ура! 💖", "Регистрация успешна")
            self.stack.setCurrentIndex(0)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка 💔", "Такой email или телефон уже существует")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Comic Sans MS", 11))
    QToolTip.setFont(QFont("Comic Sans MS", 10))
    window = LoginRegister()
    window.show()
    sys.exit(app.exec())
