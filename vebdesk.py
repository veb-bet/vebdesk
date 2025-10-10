import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QLineEdit, QLabel, QFileDialog, QListWidget, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

# === База данных ===
conn = sqlite3.connect("vebdesk.db")
c = conn.cursor()

# Пользователи
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, email TEXT UNIQUE, phone TEXT UNIQUE, password TEXT)''')
# Заметки
c.execute('''CREATE TABLE IF NOT EXISTS notes
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT)''')
# Сообщения
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT, timestamp TEXT)''')
# Файлы
c.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY, user_id INTEGER, filepath TEXT)''')
conn.commit()

# === Темы ===
LIGHT_THEME = """
QMainWindow {
    background-color: #FFF0F5;
}
QTabWidget::pane { border: 0; }
QLabel { color: #800080; font-weight: bold; }
QPushButton {
    background-color: #FFB6C1;
    border-radius: 8px;
    padding: 5px;
}
QPushButton:hover {
    background-color: #FF69B4;
}
QTextEdit, QLineEdit, QListWidget {
    background-color: #FFE4E1;
    border: 1px solid #FFB6C1;
    border-radius: 5px;
}
"""

DARK_THEME = """
QMainWindow {
    background-color: #2C003E;
}
QLabel { color: #FFB6C1; font-weight: bold; }
QPushButton {
    background-color: #800080;
    color: white;
    border-radius: 8px;
    padding: 5px;
}
QPushButton:hover {
    background-color: #DA70D6;
}
QTextEdit, QLineEdit, QListWidget {
    background-color: #4B0082;
    color: white;
    border: 1px solid #DA70D6;
    border-radius: 5px;
}
"""

# === Главное окно ===
class VebDesk(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("💖 VebDesk 💖")
        self.setGeometry(100, 100, 900, 600)
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

    # === Вкладки ===
    def init_notes_tab(self):
        self.notes_tab = QWidget()
        layout = QVBoxLayout()
        self.note_editor = QTextEdit()
        save_btn = QPushButton("💾 Сохранить заметку")
        save_btn.clicked.connect(self.save_note)
        layout.addWidget(QLabel("Ваши милые заметки:"))
        layout.addWidget(self.note_editor)
        layout.addWidget(save_btn)
        self.notes_tab.setLayout(layout)
        self.tabs.addTab(self.notes_tab, "📝 Заметки")

    def save_note(self):
        content = self.note_editor.toPlainText()
        c.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", 
                  (self.user_id, "Без названия", content))
        conn.commit()
        QMessageBox.information(self, "Ура!", "Заметка сохранена 💕")
        self.note_editor.clear()

    def init_calendar_tab(self):
        self.calendar_tab = QWidget()
        layout = QVBoxLayout()
        self.date_label = QLabel(f"Сегодня: {QDate.currentDate().toString()}")
        layout.addWidget(self.date_label)
        self.calendar_tab.setLayout(layout)
        self.tabs.addTab(self.calendar_tab, "📅 Календарь")

    def init_calculator_tab(self):
        self.calc_tab = QWidget()
        layout = QVBoxLayout()
        self.calc_input = QLineEdit()
        self.calc_result = QLabel("Результат:")
        calc_btn = QPushButton("➗ Вычислить")
        calc_btn.clicked.connect(self.calculate)
        layout.addWidget(QLabel("Введите выражение:"))
        layout.addWidget(self.calc_input)
        layout.addWidget(calc_btn)
        layout.addWidget(self.calc_result)
        self.calc_tab.setLayout(layout)
        self.tabs.addTab(self.calc_tab, "🧮 Калькулятор")

    def calculate(self):
        expr = self.calc_input.text()
        try:
            result = eval(expr)
            self.calc_result.setText(f"Результат: {result}")
        except Exception as e:
            self.calc_result.setText(f"Ошибка: {e}")

    def init_messages_tab(self):
        self.messages_tab = QWidget()
        layout = QVBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_list = QListWidget()
        send_btn = QPushButton("📨 Отправить")
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(QLabel("Чат:"))
        layout.addWidget(self.msg_list)
        layout.addWidget(self.msg_input)
        layout.addWidget(send_btn)
        self.messages_tab.setLayout(layout)
        self.tabs.addTab(self.messages_tab, "💌 Сообщения")

    def send_message(self):
        text = self.msg_input.text()
        if text:
            c.execute("INSERT INTO messages (user_id, text, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
                      (self.user_id, text))
            conn.commit()
            self.msg_list.addItem(f"Вы: {text}")
            self.msg_input.clear()

    def init_storage_tab(self):
        self.storage_tab = QWidget()
        layout = QVBoxLayout()
        self.file_list = QListWidget()
        add_file_btn = QPushButton("📂 Добавить файл")
        add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("Файлы в работе:"))
        layout.addWidget(self.file_list)
        layout.addWidget(add_file_btn)
        self.storage_tab.setLayout(layout)
        self.tabs.addTab(self.storage_tab, "🗂️ Хранилище")

    def add_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if fname:
            c.execute("INSERT INTO files (user_id, filepath) VALUES (?, ?)", (self.user_id, fname))
            conn.commit()
            self.file_list.addItem(fname)

    def init_theme_switch(self):
        theme_btn = QPushButton("🌙 Переключить тему")
        theme_btn.clicked.connect(self.switch_theme)
        self.tabs.setCornerWidget(theme_btn, Qt.Corner.TopRightCorner)

    def switch_theme(self):
        if self.dark_mode:
            self.setStyleSheet(LIGHT_THEME)
            self.dark_mode = False
        else:
            self.setStyleSheet(DARK_THEME)
            self.dark_mode = True


# === Окно входа и регистрации ===
class LoginRegister(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💖 VebDesk: Вход / Регистрация 💖")
        self.setGeometry(300, 200, 400, 300)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_login_page()
        self.init_register_page()

    def init_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Пароль")
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Войти 💖")
        login_btn.clicked.connect(self.login)
        switch_btn = QPushButton("Нет аккаунта? Зарегистрироваться")
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(QLabel("Вход"))
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
        self.reg_email.setPlaceholderText("Email")
        self.reg_phone = QLineEdit()
        self.reg_phone.setPlaceholderText("Телефон")
        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Пароль")
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_btn = QPushButton("Зарегистрироваться 💖")
        reg_btn.clicked.connect(self.register)
        switch_btn = QPushButton("Уже есть аккаунт? Войти")
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(QLabel("Регистрация"))
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
            QMessageBox.warning(self, "Ошибка", "Неверный email или пароль 💔")

    def register(self):
        email = self.reg_email.text()
        phone = self.reg_phone.text()
        password = self.reg_pass.text()
        try:
            c.execute("INSERT INTO users (email, phone, password) VALUES (?, ?, ?)", (email, phone, password))
            conn.commit()
            QMessageBox.information(self, "Ура!", "Регистрация успешна 💖")
            self.stack.setCurrentIndex(0)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Такой email или телефон уже существует 💔")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Comic Sans MS", 10))
    window = LoginRegister()
    window.show()
    sys.exit(app.exec())
