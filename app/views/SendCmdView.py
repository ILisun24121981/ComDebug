from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QComboBox, \
    QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal


class SendCmdView(QWidget):
    """
    Сквозной адаптивный виджет ручной отправки и выбора шаблонов команд (PyQt6 View).
    Содержит строки ввода кодограмм, настраиваемой HEX-адресации шины КНБК и payload данных.
    Использует QStackedWidget для предотвращения прыжков интерфейса по высоте.
    """
    send_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    payload_requested = pyqtSignal()
    edit_payload_requested = pyqtSignal()

    mode_changed = pyqtSignal(bool)  # True - сохраненная, False - новая
    pattern_selected = pyqtSignal(str)  # Передает выбранное название шаблона

    def __init__(self, parent=None):
        super().__init__(parent)

        # Корневой слой всей панели — строго вертикальный
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        # Базовая высота без строки радиокнопок и адресов (дефолтное состояние до подключения)
        self.setFixedHeight(54)

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
        self.main_layout.addWidget(self.radio_container)

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

        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedSize(85, 24)
        self.save_button.clicked.connect(self.save_clicked.emit)
        self.send_cmd_layout.addWidget(self.save_button)

        self.send_cmd_layout.addStretch()
        self.main_layout.addLayout(self.send_cmd_layout)

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
        self.main_layout.addWidget(self.addresses_container)

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
        self.main_layout.addLayout(self.payload_layout)

        # Принудительный стартовый сброс
        self.radio_new.setChecked(True)
        self.set_view_mode(False)

    # --- Публичное API динамического изменения интерфейса под выбранный протокол ---
    def update_addresses_labels(self, protocol_name: str):
        """Меняет текст текстовых меток и дефолты в зависимости от выбранного стандарта связи КНБК."""
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
        """Управляет отображением полей адресации получателя/отправителя КНБК."""
        self.addresses_container.setVisible(visible)
        self._recalculate_total_height()

    def set_radio_layout_visible(self, visible: bool):
        """Управляет отображением всего ряда радиокнопок."""
        self.radio_container.setVisible(visible)
        self._recalculate_total_height()

    def _recalculate_total_height(self):
        """Внутренний метод: динамически пересчитывает жесткую высоту панели для исключения прыжков."""
        base_h = 54
        if self.radio_container.isVisible():
            base_h += 24
        if self.addresses_container.isVisible():
            base_h += 30
        self.setFixedHeight(base_h)

    def set_view_mode(self, is_saved_mode: bool):
        """Бесшовно переключает слои через QStackedWidget без прыжков по высоте."""
        if is_saved_mode:
            self.cmd_stack.setCurrentIndex(1)  # Включаем QComboBox
            self.bottom_left_stack.setCurrentIndex(1)  # Включаем QLabel номера команды
            self.save_button.setVisible(False)
        else:
            self.cmd_stack.setCurrentIndex(0)  # Включаем QLineEdit
            self.bottom_left_stack.setCurrentIndex(0)  # Включаем QPushButton Payload
            self.save_button.setVisible(True)
            self.info_cmd_label.setText("")

    def populate_patterns(self, pattern_names: list[str]):
        """Заполняет комбобокс названиями шаблонов команд."""
        self.pattern_combobox.blockSignals(True)
        self.pattern_combobox.clear()
        self.pattern_combobox.addItems(pattern_names)
        self.pattern_combobox.blockSignals(False)

    def set_info_cmd_text(self, cmd_hex: str):
        """Выводит номер команды на нижнюю панель в режиме работы с шаблонами."""
        self.info_cmd_label.setText(f"Команда: 0x{cmd_hex.upper()} |")

    def show_save_button(self, visible: bool):
        """Включает видимость кнопки Сохранить при редактировании шаблона."""
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
        """ИСПРАВЛЕНО: Публичное API для принудительного заполнения полей адресации из контроллера."""
        self.dst_input.setText(dst_hex.upper())
        self.src_input.setText(src_hex.upper())

    def show_error(self, title: str, message: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)