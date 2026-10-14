from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.views.ComPortView import ComPortView
from app.views.PortLoggerView import PortLoggerView
from app.views.SendCmdView import SendCmdView
from app.views.IdsPanelView import IdsPanelView


class MainWindow(QMainWindow):
    """
    Главное окно приложения (Root View Container).
    Управляет геометрией, горизонтальной панелью генераторов команд и нижними колонками.
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

        # 3. Панель выбора COM-портов связи (всегда сверху)
        self.com_port_view = ComPortView(parent=self)
        self.main_layout.addWidget(self.com_port_view)

        # 4. Сквозной горизонтальный слой для панелей отправки команд
        self.command_generators_layout = QHBoxLayout()
        self.command_generators_layout.setSpacing(15)

        # А. Помещаем сюда наш виджет ручной отправки SendCmdView (виден всегда)
        self.send_cmd_view = SendCmdView(parent=self)
        self.command_generators_layout.addWidget(self.send_cmd_view)

        # Б. Временная визуальная заглушка под будущий PatternCmdView
        self.pattern_cmd_placeholder = QLabel("Панель PatternCmdView\n(Ожидает технических указаний...)")
        self.pattern_cmd_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pattern_cmd_placeholder.setStyleSheet(
            "border: 1px dashed #9B59B6; color: #9B59B6; "
            "background-color: #FAF0FA; font-style: italic; font-size: 11px;"
        )
        self.pattern_cmd_placeholder.setMinimumHeight(55)
        self.command_generators_layout.addWidget(self.pattern_cmd_placeholder)

        self.command_generators_layout.addStretch()

        # Подключаем весь горизонтальный ряд команд в главный вертикальный слой окна
        self.main_layout.addLayout(self.command_generators_layout)

        # 5. Двухколоночный слой для рабочих областей (Телеметрия / Логи)
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        self.left_column = QVBoxLayout()
        self.right_column = QVBoxLayout()

        # Ссылка на динамический комплексный виджет панели IDS
        self.ids_panel_view = None

        # Стандартная визуальная заглушка для ЛЕВОЙ колонки (для Gels/Aps)
        self.left_placeholder = QLabel("Левая колонка\n(Таблицы параметров КНБК / Телеметрия)")
        self.left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_placeholder.setStyleSheet(
            "border: 1px dashed #4A90E2; color: #4A90E2; "
            "background-color: #F0F4F8; font-style: italic; font-size: 12px;"
        )
        self.left_column.addWidget(self.left_placeholder, stretch=1)

        # Размещение виджета логов трафика в правой колонке
        self.port_logger_view = PortLoggerView(parent=self)
        self.right_column.addWidget(self.port_logger_view, stretch=1)

        # Подключаем нижние колонки с пропорциями весов (1:2) для расширения логгера
        self.columns_layout.addLayout(self.left_column, stretch=1)
        self.columns_layout.addLayout(self.right_column, stretch=2)

        # Добавляем двухколоночную структуру в главный вертикальный слой окна
        self.main_layout.addLayout(self.columns_layout, stretch=1)

    # --- Публичные методы управления подсистемами представлений ---

    def show_ids_interface(self, identifiers_map: dict):
        """Интегрирует комплексную панель IdsPanelView в левую колонку главного окна."""
        self.clear_left_column_content()
        self.ids_panel_view = IdsPanelView(identifiers_map, parent=self)
        self.left_column.addWidget(self.ids_panel_view, stretch=1)

    def show_default_left_interface(self):
        """Возвращает стандартную заглушку левой колонки при смене режима работы."""
        self.clear_left_column_content()
        self.left_column.addWidget(self.left_placeholder, stretch=1)

    def clear_left_column_content(self):
        """Безопасно извлекает активные виджеты из контейнера левой колонки."""
        self.left_placeholder.setParent(None)
        if self.ids_panel_view is not None:
            self.ids_panel_view.setParent(None)
            self.ids_panel_view = None