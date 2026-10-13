from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QScrollArea, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class IdsPanelView(QWidget):
    """
    Специализированная панель управления прибором IDS (PyQt6 View).
    Объединяет HEX-адресацию шины, чекбоксы запросов и поля результатов ответов.
    """
    query_requested = pyqtSignal()
    param_toggled = pyqtSignal(int, bool)

    def __init__(self, identifiers_map: dict, parent=None):
        super().__init__(parent)

        self.ids_checkboxes = {}  # {param_id: QCheckBox}
        self.ids_value_labels = {}  # {param_name: QLabel}

        # Корневой вертикальный слой панели IDS
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 1. Панель адресации (addresses_layout)
        self.addresses_layout = QHBoxLayout()
        self.addresses_layout.setSpacing(8)

        self.dst_label = QLabel("Адрес Получателя (HEX):")
        self.dst_input = QLineEdit()
        self.dst_input.setPlaceholderText("Например: 29")
        self.dst_input.setFixedWidth(60)
        self.dst_input.setText("29")

        self.src_label = QLabel("Адрес Отправителя (HEX):")
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Например: 00")
        self.src_input.setFixedWidth(60)
        self.src_input.setText("00")

        self.addresses_layout.addWidget(self.dst_label)
        self.addresses_layout.addWidget(self.dst_input)
        self.addresses_layout.addWidget(self.src_label)
        self.addresses_layout.addWidget(self.src_input)
        self.addresses_layout.addStretch()
        main_layout.addLayout(self.addresses_layout)

        # 2. Область прокрутки параметров
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        container_widget = QWidget()
        self.grid = QGridLayout(container_widget)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(5, 5, 5, 5)

        # Шапка таблицы
        label_req = QLabel("Запрос (Параметр КНБК)")
        label_req.setStyleSheet("font-weight: bold; color: #333333;")
        label_resp = QLabel("Ответ")
        label_resp.setStyleSheet("font-weight: bold; color: #333333;")

        self.grid.addWidget(label_req, 0, 0)
        self.grid.addWidget(label_resp, 0, 1)

        # Строим строки параметров
        self._build_rows(identifiers_map)

        self.scroll_area.setWidget(container_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 3. Кнопка «Запрос данных»
        self.query_button = QPushButton("Запрос данных")
        self.query_button.setFixedHeight(30)
        self.query_button.setStyleSheet("font-weight: bold; background-color: #0056b3; color: white;")
        self.query_button.clicked.connect(self.query_requested.emit)
        main_layout.addWidget(self.query_button)

    def _build_rows(self, identifiers_map: dict):
        row = 1
        for param_id, param_name in identifiers_map.items():
            cb = QCheckBox(f"{param_name} (0x{param_id:02X})")
            cb.setStyleSheet("""
                QCheckBox { color: #000000; font-weight: normal; }
                QCheckBox::indicator { border: 1px solid #666666; width: 13px; height: 13px; }
                QCheckBox::indicator:checked { background-color: #0056b3; border-color: #0056b3; }
            """)
            cb.clicked.connect(lambda checked, p_id=param_id: self.param_toggled.emit(p_id, checked))
            self.grid.addWidget(cb, row, 0)
            self.ids_checkboxes[param_id] = cb

            val_label = QLabel("—")
            val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_label.setFixedWidth(90)
            val_label.setFixedHeight(22)
            val_label.setStyleSheet(
                "background-color: #FFFFFF; border: 1px solid #CCCCCC; "
                "border-radius: 3px; color: #000000; font-family: monospace;"
            )
            self.grid.addWidget(val_label, row, 1)
            self.ids_value_labels[param_name] = val_label
            row += 1

        self.grid.setRowStretch(row, 1)

    def update_value(self, param_name: str, value: str):
        if param_name in self.ids_value_labels:
            self.ids_value_labels[param_name].setText(value)

    def get_selected_param_ids(self) -> list[int]:
        return [param_id for param_id, cb in self.ids_checkboxes.items() if cb.isChecked()]

    def get_addresses(self) -> dict:
        return {
            "dst": self.dst_input.text().strip(),
            "src": self.src_input.text().strip()
        }


from PyQt6.QtWidgets import QLineEdit  # Импорт для полей ввода