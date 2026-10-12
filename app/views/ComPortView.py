from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt


class ComPortView(QWidget):
    """
    Компактная по ширине форма выбора параметров связи (PyQt6 View).
    Все основные элементы управления выстроены в одну горизонтальную линию.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Колбэки для трансляции событий в Контроллер
        self.on_refresh_clicked = None
        self.on_connect_toggle_clicked = None
        self.on_protocol_changed_callback = None

        self._init_ui()

    def _init_ui(self):
        # Основной слой — строго вертикальный
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(6)

        # Горизонтальный контейнер для компактного размещения элементов в ряд
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # Выбор последовательного COM-порта
        controls_layout.addWidget(QLabel("Порт:"))
        self.port_combobox = QComboBox()
        self.port_combobox.setFixedWidth(90)  # Ограничиваем ширину для компактности
        controls_layout.addWidget(self.port_combobox)

        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setFixedWidth(75)
        self.refresh_button.clicked.connect(self._handle_refresh)
        controls_layout.addWidget(self.refresh_button)

        # Выбор промышленного протокола связи КНБК
        controls_layout.addWidget(QLabel("Протокол:"))
        self.protocol_combobox = QComboBox()
        self.protocol_combobox.addItems(["Gels", "Aps", "IDS"])
        self.protocol_combobox.setFixedWidth(75)
        self.protocol_combobox.currentTextChanged.connect(self._handle_protocol_change)
        controls_layout.addWidget(self.protocol_combobox)

        # Кнопка действия (Подключить/Отключить)
        self.connect_button = QPushButton("Подключить")
        self.connect_button.setFixedWidth(100)
        self.connect_button.clicked.connect(self._handle_connect)
        controls_layout.addWidget(self.connect_button)

        # Заполняем пустоту справа, чтобы элементы не растягивались на всё окно
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        # Строка с аппаратными характеристиками (под элементами управления)
        settings_container = QHBoxLayout()
        self.settings_label = QLabel("Параметры шины: —")
        self.settings_label.setStyleSheet("color: #0056b3; font-weight: bold; font-size: 11px;")
        settings_container.addWidget(self.settings_label)
        settings_container.addStretch()

        main_layout.addLayout(settings_container)

    # --- Внутренние трансляторы событий PyQt в архитектуру MVC ---
    def _handle_refresh(self):
        if self.on_refresh_clicked:
            self.on_refresh_clicked()

    def _handle_connect(self):
        if self.on_connect_toggle_clicked:
            self.on_connect_toggle_clicked(self.port_combobox.currentText())

    def _handle_protocol_change(self, text):
        if self.on_protocol_changed_callback:
            self.on_protocol_changed_callback(text)

    # --- Публичный интерфейс (API) для вызова из Контроллера ---
    def update_ports_list(self, ports: list[str]):
        """Обновляет выпадающий список обнаруженными портами ОС."""
        self.port_combobox.clear()
        self.port_combobox.addItems(ports if ports else ["Нет портов"])

    def set_connected_state(self, is_connected: bool):
        """Динамически блокирует элементы интерфейса при активной сессии связи."""
        if is_connected:
            self.connect_button.setText("Отключить")
            self.connect_button.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
            self.port_combobox.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.protocol_combobox.setEnabled(False)
        else:
            self.connect_button.setText("Подключить")
            self.connect_button.setStyleSheet("")
            self.port_combobox.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.protocol_combobox.setEnabled(True)

    def update_port_settings_display(self, settings: dict):
        """Отображает подпись настроек физического уровня на форме."""
        text = f"Параметры шины: {settings.get('baud_rate')} {settings.get('bytesize')}-{settings.get('parity')}-{settings.get('stopbits')}"
        self.settings_label.setText(text)

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)
