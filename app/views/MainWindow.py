# === ФАЙЛ: app/views/MainWindow.py (ЦЕЛИКОМ) ===
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt
from app.views.ComPortView import ComPortView
from app.views.PortLoggerView import PortLoggerView
from app.views.SendCmdView import SendCmdView
from app.views.IdsPanelView import IdsPanelView
from app.views.SetAutoPatternsView import SetAutoPatternsView


class MainWindow(QMainWindow):
    """Главное окно приложения (Root View Container) RSS проекта."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Тестировщик протоколов КНБК")
        self.resize(1150, 650)
        self.setMinimumSize(900, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.com_port_view = ComPortView(parent=self)
        self.main_layout.addWidget(self.com_port_view)

        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        self.left_widget_container = QWidget()
        self.left_widget_container.setFixedWidth(350)

        self.left_column = QVBoxLayout(self.left_widget_container)
        self.left_column.setContentsMargins(0, 0, 0, 0)
        self.left_column.setSpacing(10)

        self.right_column = QVBoxLayout()
        self.ids_panel_view = None

        self.send_cmd_view = SendCmdView(parent=self)
        self.left_column.addWidget(self.send_cmd_view)

        # Стартовая инициализация заглушки (она будет жить в макете ВСЕГДА)
        self.left_placeholder = QLabel(
            "Левая колонка\n(Таблицы параметров КНБК / Телеметрия)"
        )
        self.left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_placeholder.setStyleSheet(
            "border: 1px dashed #4A90E2; color: #4A90E2; "
            "background-color: #F0F4F8; font-style: italic; font-size: 12px;"
        )
        self.left_column.addWidget(self.left_placeholder, stretch=1)

        # Интеграция изолированного виджета автоопроса
        self.auto_patterns_view = SetAutoPatternsView(parent=self)
        self.right_column.addWidget(self.auto_patterns_view)

        self.port_logger_view = PortLoggerView(parent=self)
        self.right_column.addWidget(self.port_logger_view, stretch=1)

        self.columns_layout.addWidget(self.left_widget_container)
        self.columns_layout.addLayout(self.right_column, stretch=1)
        self.main_layout.addLayout(self.columns_layout, stretch=1)

    def set_auto_polling_panel_running_state(self, running: bool):
        self.auto_patterns_view.set_running_ui_state(running)

    def show_ids_interface(self, identifiers_map: dict):
        """Переключает левую колонку на отображение интерфейса IDS."""
        self.clear_left_column_content()

        # Скрываем постоянную заглушку вместо её физического удаления
        self.left_placeholder.setVisible(False)

        self.ids_panel_view = IdsPanelView(identifiers_map, parent=self)
        self.left_column.addWidget(self.ids_panel_view, stretch=1)

    def show_default_left_interface(self):
        """Безопасно возвращает стандартную заглушку на экран."""
        self.clear_left_column_content()

        # Просто делаем постоянную заглушку видимой! Краш 0xC0000409 устранен!
        self.left_placeholder.setVisible(True)

    def clear_left_column_content(self):
        """
        ИСПРАВЛЕНО: Безопасное удаление динамических панелей КНБК.
        Удаляет только IdsPanelView, никогда не трогая постоянный left_placeholder.
        """
        if self.ids_panel_view is not None:
            try:
                self.left_column.removeWidget(self.ids_panel_view)
                self.ids_panel_view.setParent(None)
                self.ids_panel_view.deleteLater()
            except Exception:
                pass
            self.ids_panel_view = None
