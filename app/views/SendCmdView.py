from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QComboBox, QStackedWidget, QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class SendCmdView(QWidget):
    """
    Сквозной адаптивный виджет ручной отправки и выбора шаблонов команд (PyQt6 View).
    Содержит строки ввода кодограмм, настраиваемой HEX-адресации шины КНБК и payload данных.
    Использует QStackedWidget для предотвращения прыжков интерфейса по высоте.
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
        """)

        # Внутренний рабочий слой для элементов управления
        self.inner_layout = QVBoxLayout(self.border_frame)
        self.inner_layout.setContentsMargins(10, 10, 10, 10)
        self.inner_layout.setSpacing(6)

        self.main_layout.addWidget(self.border_frame)

        # Базовая высота с учетом добавленной промышленной рамки и внутренних отступов
        self.setFixedHeight(74)

        # 1. КОНТЕЙНЕР РАДИОКНОПОК (По умолчанию скрыт)
        self.radio_container = QWidget()
        self.radio_container.setFixedHeight(18)
        radio_inner_layout = QHBoxLayout(self.radio_container)
        radio_inner_layout.setContentsMargins(0, 0, 0, 0)
        radio_inner_layout.setSpacing(12)

        radio_inner_layout.addWidget(QLabel("Режим команды:"))
        self.radio_saved = QRadioButton("Сохраненная")
        self.radio_new = QRadioButton("Новая")

        self.radio_saved.toggled.connect(lambda checked: self.mode_changed.emit(True) if checked else None)
        self.radio_new.toggled.connect(lambda checked: self.mode_changed.emit(False) if checked else None)

        radio_inner_layout.addWidget(self.radio_saved)
        radio_inner_layout.addWidget(self.radio_new)
        radio_inner_layout.addStretch()

        self.radio_container.setVisible(False)
        self.inner_layout.addWidget(self.radio_container)

        # 2. РЯД УПРАВЛЕНИЯ И ОТПРАВКИ КОМАНД (Виден всегда)
        self.send_cmd_layout = QHBoxLayout()
        self.send_cmd_layout.setSpacing(8)
        self.send_cmd_layout.addWidget(QLabel("Команда (HEX):"))

        self.cmd_stack = QStackedWidget()
        self.cmd_stack.setFixedSize(180, 24)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("1A")
        self.cmd_input.setMaxLength(5)
        self.cmd_stack.addWidget(self.cmd_input)

        self.pattern_combobox = QComboBox()
        self.pattern_combobox.currentTextChanged.connect(self.pattern_selected.emit)
        self.cmd_stack.addWidget(self.pattern_combobox)
        self.send_cmd_layout.addWidget(self.cmd_stack)

        self.send_button = QPushButton("Отправить")
        self.send_button.setFixedSize(85, 24)
        self.send_button.clicked.connect(self.send_clicked.emit)
        self.send_cmd_layout.addWidget(self.send_button)

        # ИСПРАВЛЕНО: Кнопка «Редактировать» зафиксирована на длине 105 пикселей
        self.edit_patterns_button = QPushButton("Редактировать")
        self.edit_patterns_button.setFixedSize(105, 24)
        self.edit_patterns_button.clicked.connect(self.edit_patterns_clicked.emit)
        self.send_cmd_layout.addWidget(self.edit_patterns_button)

        # ИСПРАВЛЕНО: Кнопка «Сохранить» приведена к той же длине 105 пикселей для исключения прыжков геометрии
        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedSize(105, 24)
        self.save_button.clicked.connect(self.save_clicked.emit)
        self.send_cmd_layout.addWidget(self.save_button)

        self.send_cmd_layout.addStretch()
        self.inner_layout.addLayout(self.send_cmd_layout)

        # 3. КОНТЕЙНЕР АДРЕСАЦИИ ШИНЫ (Динамически перестраиваемый под протоколы IDS/Gels)
        self.addresses_container = QWidget()
        self.addresses_container.setFixedHeight(24)
        addresses_inner_layout = QHBoxLayout(self.addresses_container)
        addresses_inner_layout.setContentsMargins(0, 0, 0, 0)
        addresses_inner_layout.setSpacing(8)

        self.dst_label = QLabel("Адрес Получателя (HEX):")
        self.dst_input = QLineEdit()
        self.dst_input.setFixedWidth(60)

        self.src_label = QLabel("Адрес Отправителя (HEX):")
        self.src_input = QLineEdit()
        self.src_input.setFixedWidth(60)

        addresses_inner_layout.addWidget(self.dst_label)
        addresses_inner_layout.addWidget(self.dst_input)
        addresses_inner_layout.addWidget(self.src_label)
        addresses_inner_layout.addWidget(self.src_input)
        addresses_inner_layout.addStretch()

        self.addresses_container.setVisible(False)
        self.inner_layout.addWidget(self.addresses_container)

        # 4. РЯД ПОЛЕЗНОЙ НАГРУЗКИ PAYLOAD (Виден всегда)
        self.payload_layout = QHBoxLayout()
        self.payload_layout.setSpacing(8)

        self.bottom_left_stack = QStackedWidget()
        self.bottom_left_stack.setFixedSize(180, 24)

        self.payload_button = QPushButton("Добавить данные к команде")
        self.payload_button.clicked.connect(self.payload_requested.emit)
        self.bottom_left_stack.addWidget(self.payload_button)

        self.info_cmd_label = QLabel("")
        self.info_cmd_label.setStyleSheet("color: #0056b3; font-weight: bold; font-size: 11px;")
        self.info_cmd_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.bottom_left_stack.addWidget(self.info_cmd_label)
        self.payload_layout.addWidget(self.bottom_left_stack)

        self.payload_status_label = QLabel("Данные отсутствуют (0 байт)")
        self.payload_status_label.setStyleSheet("color: #777777; font-style: italic; font-size: 11px;")
        self.payload_layout.addWidget(self.payload_status_label)

        self.payload_edit_button = QPushButton("[?]")
        self.payload_edit_button.setFixedSize(30, 20)
        self.payload_edit_button.setStyleSheet(
            "font-weight: bold; color: #0056b3; background: transparent; border: none; font-size: 12px;"
        )
        self.payload_edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.payload_edit_button.clicked.connect(self.edit_payload_requested.emit)
        self.payload_edit_button.setVisible(False)
        self.payload_layout.addWidget(self.payload_edit_button)

        self.payload_layout.addStretch()
        self.inner_layout.addLayout(self.payload_layout)

        # Вертикальный поджим к верху рамки
        self.inner_layout.addStretch()

        # Принудительный стартовый сброс
        self.radio_new.setChecked(True)
        self.set_view_mode(False)

    def update_addresses_labels(self, protocol_name: str):
        if protocol_name == "Gels":
            self.dst_label.setText("Адрес Устройства (HEX):")
            self.dst_input.setText("01")
            self.src_label.setText("Адрес Модуля (HEX):")
            self.src_input.setText("10")
        else:
            self.dst_label.setText("Адрес Получателя (HEX):")
            self.dst_input.setText("29")
            self.src_label.setText("Адрес Отправителя (HEX):")
            self.src_input.setText("00")

    def set_addresses_container_visible(self, visible: bool):
        self.addresses_container.setVisible(visible)
        self._recalculate_total_height()

    def set_radio_layout_visible(self, visible: bool):
        self.radio_container.setVisible(visible)
        self._recalculate_total_height()

    def _recalculate_total_height(self):
        """Внутренний метод: динамически пересчитывает жесткую высоту панели."""
        base_h = 74
        if self.radio_container.isVisible():
            base_h += 24
        if self.addresses_container.isVisible():
            base_h += 30
        self.setFixedHeight(base_h)

    def set_view_mode(self, is_saved_mode: bool):
        if is_saved_mode:
            self.cmd_stack.setCurrentIndex(1)
            self.bottom_left_stack.setCurrentIndex(1)
            self.save_button.setVisible(False)
            self.edit_patterns_button.setVisible(True)
        else:
            self.cmd_stack.setCurrentIndex(0)
            self.bottom_left_stack.setCurrentIndex(0)
            self.save_button.setVisible(True)
            self.edit_patterns_button.setVisible(False)
            self.info_cmd_label.setText("")

    def populate_patterns(self, pattern_names: list[str]):
        self.pattern_combobox.blockSignals(True)
        self.pattern_combobox.clear()
        self.pattern_combobox.addItems(pattern_names)
        self.pattern_combobox.blockSignals(False)

    def set_info_cmd_text(self, cmd_hex: str):
        self.info_cmd_label.setText(f"Команда: 0x{cmd_hex.upper()} |")

    def show_save_button(self, visible: bool):
        self.save_button.setVisible(visible)

    def update_payload_status(self, bytes_count: int):
        if bytes_count > 0:
            self.payload_status_label.setText(f"Прикреплено: {bytes_count} байт")
            self.payload_status_label.setStyleSheet("color: #008000; font-weight: bold; font-size: 11px;")
            self.payload_edit_button.setVisible(True)
        else:
            self.payload_status_label.setText("Данные отсутствуют (0 байт)")
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
