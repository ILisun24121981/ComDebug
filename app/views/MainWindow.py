from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from app.views.ComPortView import ComPortView
from app.views.IdsParametersView import IdsParametersView
from app.views.PortLoggerView import PortLoggerView


class MainWindow(QMainWindow):
    """
    Главное окно приложения (Root View Container).
    Управляет двухколоночной структурой с динамической диагностической панелью.
    """

    def __init__(self):
        super().__init__()

        # 1. Настройка базовых параметров окна
        self.setWindowTitle("Инженерный комплекс КНБК (JSON MVC)")
        self.resize(1150, 650)
        self.setMinimumSize(900, 500)

        # 2. Создание центрального виджета и корневого вертикального слоя
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 3. Добавление компактной панели выбора параметров связи
        self.com_port_view = ComPortView(parent=self)
        self.main_layout.addWidget(self.com_port_view)

        # 4. Создание горизонтального слоя разделения рабочего пространства
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        self.left_column = QVBoxLayout()
        self.right_column = QVBoxLayout()

        # 5. ДИАГНОСТИЧЕСКАЯ ПАНЕЛЬ (Вертикальный слой)
        self.diagnostic_layout = QVBoxLayout()
        self.diagnostic_layout.setSpacing(6)

        # А. Верхняя строка: Ручная отправка произвольных команд
        self.send_cmd_layout = QHBoxLayout()
        self.send_cmd_layout.setSpacing(8)

        self.cmd_label = QLabel("Команда (HEX):")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Например: 1A")
        self.cmd_input.setFixedWidth(150)

        self.send_button = QPushButton("Отправить")
        self.send_button.setFixedWidth(90)

        self.send_cmd_layout.addWidget(self.cmd_label)
        self.send_cmd_layout.addWidget(self.cmd_input)
        self.send_cmd_layout.addWidget(self.send_button)
        self.send_cmd_layout.addStretch()

        # Б. Перенесенная вниз строка: Адреса (упакована в QWidget для управления видимостью)
        self.addresses_widget = QWidget()
        addresses_main_layout = QVBoxLayout(self.addresses_widget)
        addresses_main_layout.setContentsMargins(0, 0, 0, 0)

        self.addresses_layout = QHBoxLayout()
        self.addresses_layout.setSpacing(8)

        self.dst_label = QLabel("Адрес Получателя (HEX):")
        self.dst_input = QLineEdit()
        self.dst_input.setPlaceholderText("Например: 29")
        self.dst_input.setFixedWidth(80)
        self.dst_input.setText("29")  # ИСПРАВЛЕНО: Дефолтный адрес получателя 0x29

        self.src_label = QLabel("Адрес Отправителя (HEX):")
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Например: 00")
        self.src_input.setFixedWidth(80)
        self.src_input.setText("00")  # ИСПРАВЛЕНО: Дефолтный адрес отправителя 0x00

        self.addresses_layout.addWidget(self.dst_label)
        self.addresses_layout.addWidget(self.dst_input)
        self.addresses_layout.addWidget(self.src_label)
        self.addresses_layout.addWidget(self.src_input)
        self.addresses_layout.addStretch()
        addresses_main_layout.addLayout(self.addresses_layout)

        # По умолчанию скрываем панель адресов (будет включаться только для IDS)
        self.addresses_widget.setVisible(False)

        # Собираем панель диагностики в левой колонке
        self.diagnostic_layout.addLayout(self.send_cmd_layout)
        self.diagnostic_layout.addWidget(self.addresses_widget)
        self.left_column.addLayout(self.diagnostic_layout)
        # Ссылка на динамический виджет параметров IDS
        self.ids_params_view = None

        # Базовая визуальная заглушка для ЛЕВОЙ колонки (для Gels/Aps)
        self.left_placeholder = QLabel("Левая колонка\n(Таблицы параметров КНБК / Телеметрия)")
        self.left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_placeholder.setStyleSheet(
            "border: 1px dashed #4A90E2; color: #4A90E2; "
            "background-color: #F0F4F8; font-style: italic; font-size: 12px;"
        )
        self.left_column.addWidget(self.left_placeholder, stretch=1)

        # 6. Размещение специализированного виджета логов в правой колонке
        self.port_logger_view = PortLoggerView(parent=self)
        self.right_column.addWidget(self.port_logger_view, stretch=1)

        # Подключаем обе вертикальные колонки в общий горизонтальный слой
        self.columns_layout.addLayout(self.left_column, stretch=1)
        self.columns_layout.addLayout(self.right_column, stretch=2)

        self.main_layout.addLayout(self.columns_layout, stretch=1)

    # --- Публичные методы управления подсистемами представлений ---

    def show_ids_interface(self, identifiers_map: dict):
        """Интегрирует обособленный виджет параметров IDS в левую колонку главного окна."""
        self.clear_left_column_content()
        self.ids_params_view = IdsParametersView(identifiers_map, parent=self)
        self.left_column.addWidget(self.ids_params_view, stretch=1)

    def show_default_left_interface(self):
        """Возвращает стандартную заглушку левой колонки при смене режима работы."""
        self.clear_left_column_content()
        self.left_column.addWidget(self.left_placeholder, stretch=1)

    def clear_left_column_content(self):
        """Безопасно извлекает активные виджеты из контейнера левой колонки."""
        self.left_placeholder.setParent(None)
        if self.ids_params_view is not None:
            self.ids_params_view.setParent(None)
            self.ids_params_view = None
