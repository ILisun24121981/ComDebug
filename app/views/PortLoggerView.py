from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame, QFileDialog, QMessageBox
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt
from app.models.LogManager import LogManager


class PortLoggerView(QWidget):
    """
    Виджет монитора забойного трафика (PyQt6 View).
    Обеспечивает вывод кодограмм с временными метками, очистку экрана и сохранение логов.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Инкапсулируем независимую модель менеджера логов на уровне представления
        self.log_manager = LogManager()

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
            QPushButton {
                border: 1px solid #999999;
                border-radius: 2px;
                background-color: #EAEAEA;
                color: #222222;
                font-size: 11px;
            }
            QPushButton:hover {
                border-color: #666666;
                background-color: #DFDFDF;
            }
            QPushButton:pressed {
                border-color: #444444;
                background-color: #D5D5D5;
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

        # Горизонтальный ряд кнопок управления логом
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Кнопка «Очистить»
        self.clear_button = QPushButton("Очистить")
        self.clear_button.setFixedSize(85, 22)
        self.clear_button.clicked.connect(self.clear_log)
        buttons_layout.addWidget(self.clear_button)

        # Кнопка «Сохранить»
        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedSize(85, 22)
        self.save_button.clicked.connect(self.save_log_to_file)
        buttons_layout.addWidget(self.save_button)

        # Поджимаем кнопки к левому краю
        buttons_layout.addStretch()
        inner_layout.addLayout(buttons_layout)

    def append_log(self, timestamp: str, direction: str, hex_data: str):
        """
        Добавляет строку трафика с индивидуальным цветом направления.
        Применяется посимвольное дополнение пробелами и подмена на &nbsp;
        для идеального вертикального выравнивания данных в моноширинном шрифте.
        """
        color_map = {
            "out": "#0000FF",  # Синий для исходящих запросов оператора
            "in": "#008000",  # Зеленый для ответов
            "err": "#FF0000",  # Красный для ошибок контрольных сумм CRC, таймаутов и сбоев
            "sys": "#808080"  # Серый для системных переключений и статусов
        }
        color = color_map.get(direction, "#000000")

        dir_upper = direction.upper()
        dir_tag = f"[{dir_upper}]"

        # Задаем фиксированную длину в 5 моноширинных символов для всех тегов направления
        aligned_dir_tag = dir_tag.ljust(5)

        # Защищаем пробелы от сжатия HTML-движком Qt
        html_dir = aligned_dir_tag.replace(" ", "&nbsp;")

        html_msg = f"<span style='color: {color};'>[{timestamp}] {html_dir} {hex_data}</span>"
        self.log_textedit.append(html_msg)

        # Автоматическая прокрутка каретки вниз до упора
        self.log_textedit.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        """Полностью очищает экран монитора забойного трафика."""
        self.log_textedit.clear()

    def save_log_to_file(self):
        """Извлекает чистый текстовый лог и делегирует сохранение в LogManager."""
        log_text = self.log_textedit.toPlainText().strip()

        if not log_text:
            QMessageBox.warning(self, "Предупреждение", "Невозможно сохранить пустой журнал трафика.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить журнал трафика",
            "PortTrafficLog.txt",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )

        if file_path:
            try:
                if self.log_manager.write_log_to_file(file_path, log_text):
                    QMessageBox.information(self, "Успех", f"Журнал трафика успешно экспортирован в файл:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка записи", f"Не удалось сохранить лог на диск.\nДетали: {e}")
