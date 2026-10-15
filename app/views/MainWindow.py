from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.views.ComPortView import ComPortView
from app.views.PortLoggerView import PortLoggerView
from app.views.SendCmdView import SendCmdView
from app.views.IdsPanelView import IdsPanelView


class MainWindow(QMainWindow):
    """
    Главное окно приложения (Root View Container).
    Управляет геометрией, левой колонкой (команды + телеметрия) и правой колонкой логов.
    """

    def __init__(self):
        super().__init__()

        # 1. Настройка базовых параметров окна
        self.setWindowTitle("Тестировщик протоколов")
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

        # 4. Сквозной горизонтальный слой для рабочих областей (Телеметрия / Логи)
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        # ИСПРАВЛЕНО: Создаем физический виджет-контейнер для левой колонки
        # и жестко зажимаем его ширину по эталону SendCmdView (350px)
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

        # Размещение виджета логов трафика в правой колонке (занимает всё пространство справа)
        self.port_logger_view = PortLoggerView(parent=self)
        self.right_column.addWidget(self.port_logger_view, stretch=1)

        # Подключаем нижние колонки с пропорциями весов (1:2) для расширения логгера
        self.columns_layout.addWidget(self.left_widget_container)
        self.columns_layout.addLayout(self.right_column, stretch=1)

        # Добавляем двухколоночную структуру в главный вертикальный слой окна
        self.main_layout.addLayout(self.columns_layout, stretch=1)

    # --- Публичные методы управления подсистемами представлений ---

    def show_ids_interface(self, identifiers_map: dict):
        """Интегрирует комплексную панель IdsPanelView в левую колонку главного окна."""
        self.clear_left_column_content()
        self.ids_panel_view = IdsPanelView(identifiers_map, parent=self)

        # Так как внешний контейнер left_widget_container уже жестко зажат в 350px,
        # панель IDS автоматически примет нужные габариты и рамки встанут пиксель в пиксель.
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
