from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt


class HexPayloadDialog(QDialog):
    """
    Модальное окно для ввода полезной нагрузки кодограммы в формате HEX.
    Обеспечивает изоляцию диалогового интерфейса.
    """

    def __init__(self, initial_hex: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Полезная нагрузка пакета (Payload HEX)")
        self.resize(350, 120)
        self.setModal(True)  # Делает окно строго модальным

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Введите байты тела команды (HEX через пробел или слитно):"))

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("Например: 01 02 A5 FF")
        self.hex_input.setText(initial_hex)
        layout.addWidget(self.hex_input)

        # Кнопки действия
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.ok_button = QPushButton("ОК")
        self.ok_button.clicked.connect(self.accept)  # Закрывает с кодом QDialog.DialogCode.Accepted

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)  # Закрывает с кодом QDialog.DialogCode.Rejected

        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def get_hex_string(self) -> str:
        """Возвращает очищенную от лишних пробелов строку ввода."""
        return self.hex_input.text().strip()