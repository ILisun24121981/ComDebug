from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt


class SaveCmdPatternView(QDialog):
    """Модальное окно сохранения шаблона команды (PyQt6 View)."""

    def __init__(self, formatted_packet_hex: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сохранить шаблон команды")
        self.resize(450, 160)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Название шаблона (команды):"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Проверка связи или Запрос калибровки")
        layout.addWidget(self.name_input)

        # Информационная область отображения итогового кадра посылки
        layout.addWidget(QLabel("Сформированный код посылки (HEX):"))
        self.code_label = QLabel(formatted_packet_hex)
        self.code_label.setWordWrap(True)
        self.code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code_label.setStyleSheet(
            "background-color: #F4F4F4; border: 1px solid #CCCCCC; padding: 5px; "
            "font-family: monospace; font-size: 11px; color: #0056b3; font-weight: bold;"
        )
        layout.addWidget(self.code_label)

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def get_pattern_name(self) -> str:
        return self.name_input.text().strip()