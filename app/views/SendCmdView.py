from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal


class SendCmdView(QWidget):
    """Сквозной адаптивный виджет ручной отправки и выбора шаблонов команд (PyQt6 View)."""
    send_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    payload_requested = pyqtSignal()
    edit_payload_requested = pyqtSignal()

    mode_changed = pyqtSignal(bool)  # True - сохраненная, False - новая
    pattern_selected = pyqtSignal(str)  # Передает выбранное название шаблона

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # 1. ИСПРАВЛЕНО: Упаковываем ряд радиокнопок в QWidget-контейнер для динамического скрытия
        self.radio_container = QWidget()
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

        # По умолчанию скрываем контейнер с радиокнопками с экрана
        self.radio_container.setVisible(False)
        main_layout.addWidget(self.radio_container)

        # 2. РЯД УПРАВЛЕНИЯ И ОТПРАВКИ КОМАНД
        self.send_cmd_layout = QHBoxLayout()
        self.send_cmd_layout.setSpacing(8)

        self.cmd_label = QLabel("Команда (HEX):")

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("1A")
        self.cmd_input.setFixedWidth(65)
        self.cmd_input.setMaxLength(5)

        self.pattern_combobox = QComboBox()
        self.pattern_combobox.setMinimumWidth(180)
        self.pattern_combobox.currentTextChanged.connect(self.pattern_selected.emit)

        self.send_button = QPushButton("Отправить")
        self.send_button.setFixedWidth(85)
        self.send_button.clicked.connect(self.send_clicked.emit)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedWidth(85)
        self.save_button.clicked.connect(self.save_clicked.emit)

        self.send_cmd_layout.addWidget(self.cmd_label)
        self.send_cmd_layout.addWidget(self.cmd_input)
        self.send_cmd_layout.addWidget(self.pattern_combobox)
        self.send_cmd_layout.addWidget(self.send_button)
        self.send_cmd_layout.addWidget(self.save_button)
        self.send_cmd_layout.addStretch()
        main_layout.addLayout(self.send_cmd_layout)

        # 3. РЯД ПОЛЕЗНОЙ НАГРУЗКИ PAYLOAD И ИНФОРМАЦИОННЫХ СТАТУСОВ
        self.payload_layout = QHBoxLayout()
        self.payload_layout.setSpacing(8)

        self.payload_button = QPushButton("Добавить данные к команде")
        self.payload_button.setFixedWidth(180)
        self.payload_button.clicked.connect(self.payload_requested.emit)
        self.payload_layout.addWidget(self.payload_button)

        self.info_cmd_label = QLabel("")
        self.info_cmd_label.setStyleSheet("color: #0056b3; font-weight: bold; font-size: 11px;")
        self.payload_layout.addWidget(self.info_cmd_label)

        self.payload_status_label = QLabel("Данные отсутствуют (0 байт)")
        self.payload_status_label.setStyleSheet("color: #777777; font-style: italic; font-size: 11px;")
        self.payload_layout.addWidget(self.payload_status_label)

        self.payload_edit_button = QPushButton("[?]")
        self.payload_edit_button.setFixedWidth(30)
        self.payload_edit_button.setStyleSheet(
            "font-weight: bold; color: #0056b3; background: transparent; border: none; font-size: 12px;"
        )
        self.payload_edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.payload_edit_button.clicked.connect(self.edit_payload_requested.emit)
        self.payload_edit_button.setVisible(False)
        self.payload_layout.addWidget(self.payload_edit_button)

        self.payload_layout.addStretch()
        main_layout.addLayout(self.payload_layout)

        # Стартовая принудительная инициализация интерфейса в режим "Новая"
        self.radio_new.setChecked(True)
        self.set_view_mode(False)

    # --- Публичное API динамического изменения интерфейса под выбранный режим ---
    def set_radio_layout_visible(self, visible: bool):
        """ИСПРАВЛЕНО: Публичный метод для скрытия/показа всего ряда радиокнопок."""
        self.radio_container.setVisible(visible)

    def set_view_mode(self, is_saved_mode: bool):
        """Гарантирует взаимное исключение видимости текстового поля и выпадающего списка."""
        if is_saved_mode:
            self.cmd_input.setVisible(False)
            self.pattern_combobox.setVisible(True)
            self.save_button.setVisible(False)
            self.payload_button.setVisible(False)
            self.info_cmd_label.setVisible(True)
        else:
            self.cmd_input.setVisible(True)
            self.pattern_combobox.setVisible(False)
            self.save_button.setVisible(True)
            self.payload_button.setVisible(True)
            self.info_cmd_label.setVisible(False)
            self.info_cmd_label.setText("")

    def populate_patterns(self, pattern_names: list[str]):
        """Заполняет комбобокс названиями шаблонов команд."""
        self.pattern_combobox.clear()
        self.pattern_combobox.addItems(pattern_names)

    def set_info_cmd_text(self, cmd_hex: str):
        """Выводит номер команды на нижнюю панель в режиме работы с шаблонами."""
        self.info_cmd_label.setText(f"Команда: 0x{cmd_hex.upper()} |")

    def show_save_button(self, visible: bool):
        """Форсированно включает видимость кнопки Сохранить при редактировании шаблона."""
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