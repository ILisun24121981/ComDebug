from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt


class PortLoggerView(QWidget):
    """
    Виджет монитора забойного трафика (PyQt6 View).
    Обеспечивает вывод кодограмм с временными меток.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Корневой слой всей панели — строго вертикальный
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Промышленная строго зафиксированная рамка-контейнер
        self.border_frame = QFrame()
        self.border_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: #FAFAFA;
            }
            QLabel, QTextEdit {
                background-color: transparent;
            }
        """)

        # Внутренний рабочий слой
        inner_layout = QVBoxLayout(self.border_frame)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(6)

        self.main_layout.addWidget(self.border_frame)

        # Заголовок панели монитора трафика шины
        self.title_label = QLabel("Монитор забойного трафика (HEX):")
        self.title_label.setStyleSheet("font-weight: bold; color: #333333;")
        inner_layout.addWidget(self.title_label)

        # Текстовое поле терминала (Белый экран View)
        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setFont(QFont("Courier New", 10))
        self.log_textedit.setStyleSheet("background-color: #FFFFFF; color: #000000; border: 1px solid #D1D1D1;")
        inner_layout.addWidget(self.log_textedit)

    def append_log(self, timestamp: str, direction: str, hex_data: str):
        color_map = {
            "out": "#0000FF",
            "in": "#008000",
            "err": "#FF0000",
            "sys": "#808080"
        }
        color = color_map.get(direction, "#000000")

        html_msg = f"<span style='color: {color};'>[{timestamp}] [{direction.upper()}] {hex_data}</span>"
        self.log_textedit.append(html_msg)
        self.log_textedit.moveCursor(QTextCursor.MoveOperation.End)
