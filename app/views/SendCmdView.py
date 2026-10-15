from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, \
    QRadioButton, QComboBox, QStackedWidget, QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class SendCmdView(QWidget):
    """
    Сквозной адаптивный виджет ручной отправки и выбора шаблонов команд (PyQt6 View).
    Содержит строки ввода кодограмм, настраиваемой HEX-адресации шины КНБК и payload данных.
    Использует QGridLayout для обеспечения безупречной соосности левой и правой колонок элементов.
    """
    send_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    edit_patterns_clicked = pyqtSignal()
    payload_requested = pyqtSignal()
    edit_payload_requested = pyqtSignal()

    mode_changed = pyqtSignal(bool)  # True - сохраненная, False - новая
    pattern_selected = pyqtSignal(str)  # Передает выбранное название шаблона

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
            QLabel {
                border: none;
                background-color: transparent;
                color: #333333;
            }
            QLineEdit, QComboBox {
                border: 1px solid #B0B0B0;
                border-radius: 2px;
                background-color: #FFFFFF;
                color: #000000;
                padding-left: 3px;
            }
            QPushButton {
                border: 1px solid #999999;
                border-radius: 2px;
                background-color: #EAEAEA;
                color: #222222;
            }
            QPushButton:hover {
                border-color: #666666;
                background-color: #DFDFDF;
            }
            QPushButton:pressed {
                border-color: #444444;
                background-color: #D5D5D5;
            }
            QRadioButton {
                background-color: transparent;
                color: #000000;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #777777;
                border-radius: 7px;
                background-color: #FFFFFF;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #1D6477;
                background-color: #E6F2F7;
                image: url("");
                width: 8px;
                height: 8px;
                padding: 2px;
                border-radius: 7px;
            }
        """)

        # Внутренний рабочий слой на жесткой сетке QGridLayout
        self.grid_layout = QGridLayout(self.border_frame)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(6)

        self.main_layout.addWidget(self.border_frame)

        # Геометрическая изоляция виджета от внешнего окружения
        self.setFixedWidth(350)
        self.setFixedHeight(114)

        # --- РЯД 0: ОБЪЕДИНЕННЫЙ КОМПАКТНЫЙ СЛОЙ ЛЕЙБЛА И РАДИОКНОПОК ---
        radio_inner_layout = QHBoxLayout()
        radio_inner_layout.setContentsMargins(0, 0, 0, 0)
        radio_inner_layout.setSpacing(12)

        self.lbl_title = QLabel("Команда (HEX):")
        radio_inner_layout.addWidget(self.lbl_title)

        self.radio_saved = QRadioButton("Сохраненная")
        self.radio_new = QRadioButton("Новая")
        self.radio_saved.toggled.connect(lambda checked: self.mode_changed.emit(True) if checked else None)
        self.radio_new.toggled.connect(lambda checked: self.mode_changed.emit(False) if checked else None)

        radio_inner_layout.addWidget(self.radio_saved)
        radio_inner_layout.addWidget(self.radio_new)
        radio_inner_layout.addStretch()

        self.grid_layout.addLayout(radio_inner_layout, 0, 0, 1, 2,
                                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # --- РЯД 1: ПОЛЕ ВВОДА КОМАНДЫ (КОЛ. 0) И КНОПКА ОТПРАВИТЬ (КОЛ. 1) ---
        self.cmd_stack = QStackedWidget()
        self.cmd_stack.setFixedSize(175, 24)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("1A")
        self.cmd_input.setMaxLength(5)
        self.cmd_stack.addWidget(self.cmd_input)

        self.pattern_combobox = QComboBox()
        self.pattern_combobox.currentTextChanged.connect(self.pattern_selected.emit)
        self.cmd_stack.addWidget(self.pattern_combobox)
        self.grid_layout.addWidget(self.cmd_stack, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.send_button = QPushButton("Отправить")
        self.send_button.setFixedSize(145, 24)
        self.send_button.clicked.connect(self.send_clicked.emit)
        self.grid_layout.addWidget(self.send_button, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # --- РЯД 2: КНОПКА ДОБАВИТЬ ДАННЫЕ И ИНФО-ЛЕЙБЛ РАЗМЕЩЕНЫ НАПРЯМУЮ В ЯЧЕЙКЕ ---
        self.payload_button = QPushButton("Добавить данные")
        self.payload_button.setFixedSize(175, 24)
        self.payload_button.clicked.connect(self.payload_requested.emit)
        self.grid_layout.addWidget(self.payload_button, 2, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.info_cmd_label = QLabel("")
        self.info_cmd_label.setStyleSheet("color: #0056b3; font-weight: bold; font-size: 11px;")
        self.info_cmd_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.info_cmd_label.setFixedSize(175, 24)
        self.grid_layout.addWidget(self.info_cmd_label, 2, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Правые управляющие кнопки ложатся в Колонку 1 (строго под кнопку Отправить)
        self.edit_patterns_button = QPushButton("Редактировать")
        self.edit_patterns_button.setFixedSize(145, 24)
        self.edit_patterns_button.clicked.connect(self.edit_patterns_clicked.emit)
        self.grid_layout.addWidget(self.edit_patterns_button, 2, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedSize(145, 24)
        self.save_button.clicked.connect(self.save_clicked.emit)
        self.grid_layout.addWidget(self.save_button, 2, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # --- РЯД 3: СТАТУС ВЫВОДА ПОЛЕЗНОЙ НАГРУЗКИ ---
        self.payload_status_widget = QWidget()
        self.payload_status_widget.setFixedHeight(18)  # ИСПРАВЛЕНО: Жестко закрепили высоту статус-бара
        payload_status_inner = QHBoxLayout(self.payload_status_widget)
        payload_status_inner.setContentsMargins(0, 0, 0, 0)
        payload_status_inner.setSpacing(6)

        self.payload_status_label = QLabel("Нет данных")
        self.payload_status_label.setStyleSheet("color: #777777; font-style: italic; font-size: 11px;")
        payload_status_inner.addWidget(self.payload_status_label)

        self.payload_edit_button = QPushButton("[?]")
        self.payload_edit_button.setFixedSize(30, 18)
        self.payload_edit_button.setStyleSheet(
            "font-weight: bold; color: #0056b3; background: transparent; border: none; font-size: 12px;"
        )
        self.payload_edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.payload_edit_button.clicked.connect(self.edit_payload_requested.emit)
        self.payload_edit_button.setVisible(False)
        payload_status_inner.addWidget(self.payload_edit_button)
        payload_status_inner.addStretch()
        self.grid_layout.addWidget(self.payload_status_widget, 3, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # --- РЯДЫ 4 И 5: АДРЕСАЦИЯ ПОЛУЧАТЕЛЯ И ОТПРАВИТЕЛЯ ---
        self.dst_label = QLabel("Адрес Получателя (HEX):")
        self.dst_label.setFixedWidth(175)
        self.dst_input = QLineEdit()
        self.dst_input.setFixedSize(145, 22)

        self.src_label = QLabel("Адрес Отправителя (HEX):")
        self.src_label.setFixedWidth(175)
        self.src_input = QLineEdit()
        self.src_input.setFixedSize(145, 22)

        self.grid_layout.addWidget(self.dst_label, 4, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.grid_layout.addWidget(self.dst_input, 4, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.grid_layout.addWidget(self.src_label, 5, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.grid_layout.addWidget(self.src_input, 5, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.grid_layout.setColumnStretch(2, 0)

        # Принудительный поджим контента сетки к верхнему краю
        self.main_layout.addStretch()

        self.set_addresses_visible_internal(False)
        self.radio_new.setChecked(True)
        self.set_view_mode(False)

    def update_addresses_labels(self, protocol_name: str):
        if protocol_name == "Gels":
            self.dst_label.setText("Адрес Устройства (HEX):")
            self.src_label.setText("Адрес Модуля (HEX):")
            self.dst_input.setText("01")
            self.src_input.setText("10")
        else:
            self.dst_label.setText("Адрес Получателя (HEX):")
            self.src_label.setText("Адрес Отправителя (HEX):")
            self.dst_input.setText("29")
            self.src_input.setText("00")

    def set_addresses_container_visible(self, visible: bool):
        self.set_addresses_visible_internal(visible)
        self._recalculate_total_height()

    def set_radio_layout_visible(self, visible: bool):
        self._recalculate_total_height()

    def set_addresses_visible_internal(self, visible: bool):
        self.dst_label.setVisible(visible)
        self.dst_input.setVisible(visible)
        self.src_label.setVisible(visible)
        self.src_input.setVisible(visible)

    # ИСПРАВЛЕНО: Линейная фиксация высот виджета (114px без адресов, 172px с адресами КНБК КНБК).
    # Никаких промежуточных плавающих расчетов — прыжки устранены полностью.
    def _recalculate_total_height(self):
        """Внутренний метод: динамически пересчитывает жесткую высоту панели."""
        if self.dst_label.isVisible():
            self.setFixedHeight(172)
        else:
            self.setFixedHeight(114)

    def set_view_mode(self, is_saved_mode: bool):
        if is_saved_mode:
            self.cmd_stack.setCurrentIndex(1)
            self.payload_button.setVisible(False)
            self.info_cmd_label.setVisible(True)
            self.save_button.setVisible(False)
            self.edit_patterns_button.setVisible(True)
        else:
            self.cmd_stack.setCurrentIndex(0)
            self.payload_button.setVisible(True)
            self.info_cmd_label.setVisible(False)
            self.save_button.setVisible(True)
            self.edit_patterns_button.setVisible(False)
            self.info_cmd_label.setText("")

    def populate_patterns(self, pattern_names: list[str]):
        self.pattern_combobox.blockSignals(True)
        self.pattern_combobox.clear()
        self.pattern_combobox.addItems(pattern_names)
        self.pattern_combobox.blockSignals(False)

    def set_info_cmd_text(self, cmd_hex: str):
        self.info_cmd_label.setText(f"Команда: 0x{cmd_hex.upper()}")

    def show_save_button(self, visible: bool):
        self.save_button.setVisible(visible)

    def update_payload_status(self, bytes_count: int):
        if bytes_count > 0:
            self.payload_status_label.setText(f"Данные: {bytes_count} байт")
            self.payload_status_label.setStyleSheet("color: #008000; font-weight: bold; font-size: 11px;")
            self.payload_edit_button.setVisible(True)
        else:
            self.payload_status_label.setText("Нет данных")
            self.payload_status_label.setStyleSheet("color: #777777; font-style: italic; font-size: 11px;")
            self.payload_edit_button.setVisible(False)

    def get_cmd_value(self) -> str:
        return self.cmd_input.text().strip()

    def get_addresses_values(self) -> dict:
        return {
            "dst": self.dst_input.text().strip(),
            "src": self.src_input.text().strip()
        }

    def set_addresses_values(self, dst_hex: str, src_hex: str):
        self.dst_input.setText(dst_hex.upper())
        self.src_input.setText(src_hex.upper())

    def show_error(self, title: str, message: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)
