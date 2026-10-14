from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QScrollArea, QPushButton, \
    QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class IdsPanelView(QWidget):
    """
    Специализированная панель управления прибором IDS (PyQt6 View).
    Инкапсулирует таблицу чекбоксов параметров КНБК, поля ответов и статус-бар сессии.
    """
    query_requested = pyqtSignal()
    save_pattern_requested = pyqtSignal()
    param_toggled = pyqtSignal(int, bool)

    def __init__(self, identifiers_map: dict, parent=None):
        super().__init__(parent)

        self.ids_checkboxes = {}  # {param_id: QCheckBox}
        self.ids_value_labels = {}  # {param_name: QLabel}

        # Корневой слой всей панели — строго вертикальный
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Промышленная строго зафиксированная рамка-контейнер
        self.border_frame = QFrame()

        # Настраиваем базовые стили и поведение при наведении (hover)
        self.border_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: #FAFAFA;
            }
            QLabel, QScrollArea, QPushButton {
                background-color: transparent;
            }
            QCheckBox {
                background-color: transparent;
                color: #000000;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #777777;
                border-radius: 0px;
                background-color: #FFFFFF;
                padding: 1px; /* Резервируем пиксель под будущую толстую рамку */
            }
            QCheckBox::indicator:hover {
                border: 2px solid #1D6477;
                padding: 0px; /* Сохраняем общий размер неизменным */
            }
        """)

        # Внутренний слой для размещения забойной таблицы параметров
        inner_layout = QVBoxLayout(self.border_frame)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(10)

        self.main_layout.addWidget(self.border_frame)

        # 1. Область прокрутки параметров
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        container_widget = QWidget()
        self.grid = QGridLayout(container_widget)

        # Расстояние между строками параметров 4px и отступы 2px
        self.grid.setSpacing(4)
        self.grid.setContentsMargins(2, 2, 2, 2)

        # Главный управляющий чекбокс шапки со светлой синей заливкой при активации
        self.select_all_checkbox = QCheckBox("Выделить все")
        self.select_all_checkbox.setStyleSheet("""
            QCheckBox { color: #333333; font-weight: bold; }
            QCheckBox::indicator:checked {
                border: 2px solid #1D6477;
                background-color: #E6F2F7; /* Спокойный пастельно-синий фон */
                padding: 0px;
            }
        """)
        self.select_all_checkbox.clicked.connect(self._handle_select_all_clicked)
        self.grid.addWidget(self.select_all_checkbox, 0, 0)

        label_resp = QLabel("Ответ")
        label_resp.setStyleSheet("font-weight: bold; color: #333333;")
        self.grid.addWidget(label_resp, 0, 1)

        # Строим строки параметров КНБК
        self._build_rows(identifiers_map)

        self.scroll_area.setWidget(container_widget)
        inner_layout.addWidget(self.scroll_area, stretch=1)
        # 2. Текстовый статус-бар сессии опроса
        self.status_bar_label = QLabel("Система готова к опросу")
        self.status_bar_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_bar_label.setStyleSheet("color: #555555; font-style: italic; font-size: 11px; padding-left: 2px;")
        inner_layout.addWidget(self.status_bar_label)

        # 3. Горизонтальный ряд кнопок управления
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.save_pattern_button = QPushButton("Сохранить запрос")
        self.save_pattern_button.setFixedHeight(30)
        self.save_pattern_button.setStyleSheet(
            "font-weight: bold; background-color: #28A745; color: white; border: 1px solid #218838; border-radius: 3px;")
        self.save_pattern_button.clicked.connect(self.save_pattern_requested.emit)
        buttons_layout.addWidget(self.save_pattern_button, stretch=1)

        self.query_button = QPushButton("Послать запрос")
        self.query_button.setFixedHeight(30)
        self.query_button.setStyleSheet(
            "font-weight: bold; background-color: #0056b3; color: white; border: 1px solid #004085; border-radius: 3px;")
        self.query_button.clicked.connect(self.query_requested.emit)
        buttons_layout.addWidget(self.query_button, stretch=1)

        inner_layout.addLayout(buttons_layout)

    def _build_rows(self, identifiers_map: dict):
        row = 1
        for param_id, meta in identifiers_map.items():
            param_name = meta["name"] if isinstance(meta, dict) else str(meta)

            cb = QCheckBox(f"{param_name} (0x{param_id:02X})")

            # ИСПРАВЛЕНО: Для отмеченных чекбоксов установлена жирная рамка #1D6477 внутрь элемента
            # и добавлена мягкая синяя заливка #E6F2F7, полностью гармонирующая с верхним пультом
            cb.setStyleSheet("""
                QCheckBox { color: #000000; font-weight: normal; padding-top: 1px; padding-bottom: 1px; }
                QCheckBox::indicator:checked {
                    border: 2px solid #1D6477;
                    background-color: #E6F2F7;
                    padding: 0px;
                }
            """)
            cb.clicked.connect(lambda checked, p_id=param_id: self.param_toggled.emit(p_id, checked))
            self.grid.addWidget(cb, row, 0)
            self.ids_checkboxes[param_id] = cb

            val_label = QLabel("—")
            val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_label.setFixedWidth(90)
            val_label.setFixedHeight(18)
            val_label.setStyleSheet(
                "background-color: #FFFFFF; border: 1px solid #CCCCCC; "
                "border-radius: 3px; color: #000000; font-family: monospace; font-size: 11px;"
            )
            self.grid.addWidget(val_label, row, 1)
            self.ids_value_labels[param_name] = val_label
            row += 1

        self.grid.setRowStretch(row, 1)

    def _handle_select_all_clicked(self, is_checked: bool):
        for param_id, cb in self.ids_checkboxes.items():
            if cb.isEnabled() and cb.isChecked() != is_checked:
                cb.setChecked(is_checked)
                self.param_toggled.emit(param_id, is_checked)

    def set_interactive_state(self, enabled: bool):
        self.query_button.setEnabled(enabled)
        self.save_pattern_button.setEnabled(enabled)
        self.select_all_checkbox.setEnabled(enabled)
        for cb in self.ids_checkboxes.values():
            cb.setEnabled(enabled)

        if enabled:
            self.query_button.setStyleSheet(
                "font-weight: bold; background-color: #0056b3; color: white; border: 1px solid #004085; border-radius: 3px;")
            self.save_pattern_button.setStyleSheet(
                "font-weight: bold; background-color: #28A745; color: white; border: 1px solid #218838; border-radius: 3px;")
        else:
            self.query_button.setStyleSheet(
                "font-weight: bold; background-color: #A0A0A0; color: #E0E0E0; border: 1px solid #808080; border-radius: 3px;")
            self.save_pattern_button.setStyleSheet(
                "font-weight: bold; background-color: #A0A0A0; color: #E0E0E0; border: 1px solid #808080; border-radius: 3px;")

    def set_session_status(self, text: str, color_hex: str = "#555555", font_bold: bool = False):
        self.status_bar_label.setText(text)
        weight = "bold" if font_bold else "normal"
        self.status_bar_label.setStyleSheet(
            f"color: {color_hex}; font-weight: {weight}; font-size: 11px; padding-left: 2px;")

    def update_value(self, param_name: str, value: str):
        if param_name in self.ids_value_labels:
            label = self.ids_value_labels[param_name]
            label.setText(value)
            label.setStyleSheet("""
                background-color: #FFFFFF; 
                border: 1px solid #CCCCCC; 
                border-radius: 3px; 
                color: #000000; 
                font-family: monospace;
                font-size: 11px;
                font-weight: normal;
            """)

    def update_value_with_border(self, param_name: str, value: str, border_color_hex: str):
        if param_name in self.ids_value_labels:
            label = self.ids_value_labels[param_name]
            label.setText(value)
            label.setStyleSheet(f"""
                background-color: #F4FAF4; 
                border: 2px solid {border_color_hex}; 
                border-radius: 3px; 
                color: #000000; 
                font-family: monospace;
                font-size: 11px;
                font-weight: bold;
            """)

    def get_selected_param_ids(self) -> list[int]:
        return [param_id for param_id, cb in self.ids_checkboxes.items() if cb.isChecked()]
