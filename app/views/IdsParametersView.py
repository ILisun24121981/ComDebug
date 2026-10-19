from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QCheckBox, QScrollArea, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class IdsParametersView(QWidget):
    """
    Специализированный виджет для отображения списка параметров IDS (PyQt6 View).
    Абсолютно стабилен, так как чекбоксы работают без промежуточных Python-сигналов.
    """
    query_requested = pyqtSignal()

    def __init__(self, identifiers_map: dict, parent=None):
        super().__init__(parent)

        self.ids_checkboxes = {}  # {param_id: QCheckBox}
        self.ids_value_labels = {}  # {param_name: QLabel}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        container_widget = QWidget()
        self.grid = QGridLayout(container_widget)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(5, 5, 5, 5)

        label_req = QLabel("Запрашиваемый (Параметр)")
        label_req.setStyleSheet("font-weight: bold; color: #333333;")
        label_resp = QLabel("Ответ")
        label_resp.setStyleSheet("font-weight: bold; color: #333333;")

        self.grid.addWidget(label_req, 0, 0)
        self.grid.addWidget(label_resp, 0, 1)

        self._build_rows(identifiers_map)

        self.scroll_area.setWidget(container_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.query_button = QPushButton("Запрос данных")
        self.query_button.setFixedHeight(30)
        self.query_button.setStyleSheet("font-weight: bold; background-color: #0056b3; color: white;")

        self.query_button.clicked.connect(self.query_requested.emit)
        main_layout.addWidget(self.query_button)

    def _build_rows(self, identifiers_map: dict):
        """Внутренний метод для построчного заполнения таблицы."""
        row = 1
        for param_id, param_name in identifiers_map.items():
            cb = QCheckBox(f"{param_name} (0x{param_id:02X})")
            cb.setStyleSheet("""
                QCheckBox { color: #000000; font-weight: normal; }
                QCheckBox::indicator { border: 1px solid #666666; width: 13px; height: 13px; }
                QCheckBox::indicator:checked { background-color: #0056b3; border-color: #0056b3; }
            """)

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
        """Безопасный синхронный сбор состояний чекбоксов в момент клика по кнопке."""
        return [param_id for param_id, cb in self.ids_checkboxes.items() if cb.isChecked()]
