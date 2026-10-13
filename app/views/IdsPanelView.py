from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QScrollArea, QPushButton, \
    QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal


class IdsPanelView(QWidget):
    """
    Специализированная панель управления прибором IDS (PyQt6 View).
    Инкапсулирует таблицу чекбоксов параметров КНБК, поля ответов и статус-бар сессии.
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

        # 1. Область прокрутки параметров
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        container_widget = QWidget()
        self.grid = QGridLayout(container_widget)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(5, 5, 5, 5)

        # Шапка таблицы параметров КНБК
        label_req = QLabel("Запрос (Параметр КНБК)")
        label_req.setStyleSheet("font-weight: bold; color: #333333;")
        label_resp = QLabel("Ответ")
        label_resp.setStyleSheet("font-weight: bold; color: #333333;")

        self.grid.addWidget(label_req, 0, 0)
        self.grid.addWidget(label_resp, 0, 1)

        # Строим строки параметров КНБК
        self._build_rows(identifiers_map)

        self.scroll_area.setWidget(container_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 2. Новая строка: Текстовый статус-бар сессии опроса
        self.status_bar_label = QLabel("Система готова к опросу")
        self.status_bar_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_bar_label.setStyleSheet("color: #555555; font-style: italic; font-size: 11px; padding-left: 2px;")
        main_layout.addWidget(self.status_bar_label)

        # 3. Кнопка «Запрос данных»
        self.query_button = QPushButton("Запрос данных")
        self.query_button.setFixedHeight(30)
        self.query_button.setStyleSheet("font-weight: bold; background-color: #0056b3; color: white;")
        self.query_button.clicked.connect(self.query_requested.emit)
        main_layout.addWidget(self.query_button)

    def _build_rows(self, identifiers_map: dict):
        row = 1
        for param_id, meta in identifiers_map.items():
            # ИСПРАВЛЕНО: Безопасно вытягиваем строку имени из вложенного словаря метаданных
            param_name = meta["name"] if isinstance(meta, dict) else str(meta)

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

    # --- Публичные методы API для управления интерфейсом из Контроллера ---
    def set_interactive_state(self, enabled: bool):
        """Блокирует или разблокирует чекбоксы и кнопку опроса для защиты транзакции."""
        self.query_button.setEnabled(enabled)
        for cb in self.ids_checkboxes.values():
            cb.setEnabled(enabled)

        if enabled:
            self.query_button.setStyleSheet("font-weight: bold; background-color: #0056b3; color: white;")
        else:
            self.query_button.setStyleSheet("font-weight: bold; background-color: #A0A0A0; color: #E0E0E0;")

    def set_session_status(self, text: str, color_hex: str = "#555555", font_bold: bool = False):
        """Обновляет text и цвет статус-бара панели."""
        self.status_bar_label.setText(text)
        weight = "bold" if font_bold else "normal"
        self.status_bar_label.setStyleSheet(
            f"color: {color_hex}; font-weight: {weight}; font-size: 11px; padding-left: 2px;")

    def update_value(self, param_name: str, value: str):
        if param_name in self.ids_value_labels:
            self.ids_value_labels[param_name].setText(value)

    def get_selected_param_ids(self) -> list[int]:
        return [param_id for param_id, cb in self.ids_checkboxes.items() if cb.isChecked()]