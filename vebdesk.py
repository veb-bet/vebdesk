import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit, 
    QPushButton, QLineEdit, QLabel, QFileDialog, QListWidget
)
from PyQt6.QtCore import QDate, QDateTime

class VebDesk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VebDesk")
        self.setGeometry(100, 100, 800, 600)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.init_notes_tab()
        self.init_calendar_tab()
        self.init_calculator_tab()
        self.init_messages_tab()
        self.init_storage_tab()
    
    def init_notes_tab(self):
        self.notes_tab = QWidget()
        layout = QVBoxLayout()
        self.note_editor = QTextEdit()
        layout.addWidget(QLabel("Ваши заметки:"))
        layout.addWidget(self.note_editor)
        self.notes_tab.setLayout(layout)
        self.tabs.addTab(self.notes_tab, "Заметки")

    def init_calendar_tab(self):
        self.calendar_tab = QWidget()
        layout = QVBoxLayout()
        self.date_label = QLabel(f"Сегодня: {QDate.currentDate().toString()}")
        layout.addWidget(self.date_label)
        self.calendar_tab.setLayout(layout)
        self.tabs.addTab(self.calendar_tab, "Календарь")
    
    def init_calculator_tab(self):
        self.calc_tab = QWidget()
        layout = QVBoxLayout()
        self.calc_input = QLineEdit()
        self.calc_result = QLabel("Результат:")
        calc_btn = QPushButton("Вычислить")
        calc_btn.clicked.connect(self.calculate)
        layout.addWidget(QLabel("Введите выражение:"))
        layout.addWidget(self.calc_input)
        layout.addWidget(calc_btn)
        layout.addWidget(self.calc_result)
        self.calc_tab.setLayout(layout)
        self.tabs.addTab(self.calc_tab, "Калькулятор")
    
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
        send_btn = QPushButton("Отправить")
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(QLabel("Чат:"))
        layout.addWidget(self.msg_list)
        layout.addWidget(self.msg_input)
        layout.addWidget(send_btn)
        self.messages_tab.setLayout(layout)
        self.tabs.addTab(self.messages_tab, "Сообщения")
    
    def send_message(self):
        text = self.msg_input.text()
        if text:
            self.msg_list.addItem(f"Вы: {text}")
            self.msg_input.clear()
    
    def init_storage_tab(self):
        self.storage_tab = QWidget()
        layout = QVBoxLayout()
        self.file_list = QListWidget()
        add_file_btn = QPushButton("Добавить файл")
        add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("Файлы в работе:"))
        layout.addWidget(self.file_list)
        layout.addWidget(add_file_btn)
        self.storage_tab.setLayout(layout)
        self.tabs.addTab(self.storage_tab, "Хранилище")
    
    def add_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if fname:
            self.file_list.addItem(fname)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VebDesk()
    window.show()
    sys.exit(app.exec())
