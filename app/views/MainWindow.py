from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from app.views.ComPortView import ComPortView
from app.views.PortLoggerView import PortLoggerView
from app.views.SendCmdView import SendCmdView
from app.views.IdsPanelView import IdsPanelView


class MainWindow(QMainWindow):
    """
    Главное окно приложения (Root View Container).
    Управляет геометрией, левой колонкой (команды + телеметрия) и правой колонкой логов.
    """
    auto_query_configure_requested = pyqtSignal()
    auto_query_start_requested = pyqtSignal()
    auto_query_stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        # 1. Настройка базовых параметров окна
        self.setWindowTitle("Тестировщик протоколов")
        self.resize(1150, 650)
        self.setMinimumSize(900, 500)

        # 2. Создание центрального виджет-контейнера и корневого вертикального слоя
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 3. Панель выбора COM-портов связи (всегда сверху)
        self.com_port_view = ComPortView(parent=self)
        self.main_layout.addWidget(self.com_port_view)

        # 4. Сквозной горизонтальный слой для рабочих областей (Телеметрия / Логи)
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        # Физический виджет-контейнер левой колонки (жестко зажат по ширине SendCmdView в 350px)
        self.left_widget_container = QWidget()
        self.left_widget_container.setFixedWidth(350)

        self.left_column = QVBoxLayout(self.left_widget_container)
        self.left_column.setContentsMargins(0, 0, 0, 0)
        self.left_column.setSpacing(10)

        self.right_column = QVBoxLayout()

        # Ссылка на динамический комплексный виджет панели IDS
        self.ids_panel_view = None

        # Размещаем виджет ручной отправки SendCmdView в самый верх ЛЕВОЙ колонки
        self.send_cmd_view = SendCmdView(parent=self)
        self.left_column.addWidget(self.send_cmd_view)

        # Стандартная визуальная заглушка для ЛЕВОЙ колонки (для Gels/Aps), идет строго под пультом
        self.left_placeholder = QLabel("Левая колонка\n(Таблицы параметров КНБК / Телеметрия)")
        self.left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_placeholder.setStyleSheet(
            "border: 1px dashed #4A90E2; color: #4A90E2; "
            "background-color: #F0F4F8; font-style: italic; font-size: 12px;"
        )
        self.left_column.addWidget(self.left_placeholder, stretch=1)

        # Горизонтальный слой автоматического циклического опроса КНБК перед логгером
        self.auto_query_frame = QFrame()
        self.auto_query_frame.setFixedHeight(36)
        self.auto_query_frame.setStyleSheet("""
            QFrame { border: 1px solid #CCCCCC; border-radius: 3px; background-color: #FAFAFA; }
            QLabel { border: none; background-color: transparent; color: #333333; font-weight: bold; }
            QPushButton { border: 1px solid #999999; border-radius: 2px; background-color: #EAEAEA; color: #222222; padding-left: 10px; padding-right: 10px; }
            QPushButton:hover { border-color: #666666; background-color: #DFDFDF; }
        """)

        auto_query_layout = QHBoxLayout(self.auto_query_frame)
        auto_query_layout.setContentsMargins(10, 0, 10, 0)
        auto_query_layout.setSpacing(10)

        self.lbl_auto = QLabel("Автоопрос:")
        auto_query_layout.addWidget(self.lbl_auto)

        self.btn_config = QPushButton("Настроить")
        self.btn_config.setFixedHeight(24)
        self.btn_config.clicked.connect(self.auto_query_configure_requested.emit)
        auto_query_layout.addWidget(self.btn_config)

        self.btn_start = QPushButton("Запустить")
        self.btn_start.setFixedHeight(24)
        self.btn_start.setStyleSheet(
            "font-weight: bold; background-color: #E6F2F7; border-color: #1D6477; color: #1D6477;")
        self.btn_start.clicked.connect(self.auto_query_start_requested.emit)
        auto_query_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Остановить")
        self.btn_stop.setFixedHeight(24)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.auto_query_stop_requested.emit)
        auto_query_layout.addWidget(self.btn_stop)

        auto_query_layout.addStretch()
        self.right_column.addWidget(self.auto_query_frame)

        # Размещение виджета логов трафика в правой колонке строго под автоопросом
        self.port_logger_view = PortLoggerView(parent=self)
        self.right_column.addWidget(self.port_logger_view, stretch=1)

        # Подключаем нижние колонки
        self.columns_layout.addWidget(self.left_widget_container)
        self.columns_layout.addLayout(self.right_column, stretch=1)

        # Добавляем двухколоночную структуру в главный вертикальный слой окна
        self.main_layout.addLayout(self.columns_layout, stretch=1)

    def set_auto_polling_buttons_state(self, running: bool):
        """Управляет доступностью кнопок автоопроса на уровне интерфейса."""
        self.btn_start.setEnabled(not running)
        self.btn_config.setEnabled(not running)
        self.btn_stop.setEnabled(running)

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
        """
        ИСПРАВЛЕНО: Полная очистка содержимого под пультом ручной отправки.
        Метод обходит все элементы ниже send_cmd_view, полностью удаляет их из макета,
        что исключает наложение заглушек и сдвиг таблиц вниз.
        """
        # Безопасно удаляем виджеты из макета, начиная со 2-й позиции (индекс 1)
        while self.left_column.count() > 1:
            item = self.left_column.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        self.ids_panel_view = None
