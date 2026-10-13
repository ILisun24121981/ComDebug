from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt


class PortLoggerView(QWidget):
    """
    Виджет монитора забойного трафика (PyQt6 View).
    Обеспечивает вывод кодограмм с временными метками.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Заголовок панели монитора трафика шины
        self.title_label = QLabel("Монитор забойного трафика (HEX):")
        self.title_label.setStyleSheet("font-weight: bold; color: #333333;")
        main_layout.addWidget(self.title_label)

        # Текстовое поле терминала (Белый экран View)
        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setFont(QFont("Courier New", 10))
        self.log_textedit.setStyleSheet("background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC;")
        main_layout.addWidget(self.log_textedit)

    def append_log(self, timestamp: str, direction: str, hex_data: str):
        """Добавляет строку трафика с индивидуальным цветом направления."""
        color_map = {
            "out": "#0000FF",  # Синий для исходящих запросов оператора
            "in": "#008000",  # Зеленый для ответов прибора КНБК
            "err": "#FF0000",  # Красный для ошибок контрольных сумм CRC
            "sys": "#808080"  # Серый для системных переключений и статусов
        }
        color = color_map.get(direction, "#000000")

        # HTML-форматирование строки для лог-экрана
        html_msg = f"<span style='color: {color};'>[{timestamp}] [{direction.upper()}] {hex_data}</span>"
        self.log_textedit.append(html_msg)

        # Автоматическая прокрутка каретки вниз до упора
        self.log_textedit.moveCursor(QTextCursor.MoveOperation.End)
