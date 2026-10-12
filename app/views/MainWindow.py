from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from app.views.ComPortView import ComPortView


class MainWindow(QMainWindow):
    """
    Главное окно приложения (Root View Container).
    Управляет геометрией и двухколоночной структурой рабочих областей.
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

        # 4. Создание горизонтального слоя для разделения рабочего пространства на 2 колонки
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(12)

        # Создаем левый и правый вертикальные слои
        self.left_column = QVBoxLayout()
        self.right_column = QVBoxLayout()

        # 5. Слой для отправки команд в левой колонке
        self.diagnostic_layout = QVBoxLayout()
        self.diagnostic_layout.setSpacing(6)

        self.send_cmd_layout = QHBoxLayout()
        self.send_cmd_layout.setSpacing(8)

        # Элементы интерфейса ручной отправки кодограмм
        self.cmd_label = QLabel("Команда (HEX):")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Например: 1A или CA 17 1A")
        self.cmd_input.setFixedWidth(150)

        self.send_button = QPushButton("Отправить")
        self.send_button.setFixedWidth(90)

        # Собираем элементы в горизонтальную линию отправки
        self.send_cmd_layout.addWidget(self.cmd_label)
        self.send_cmd_layout.addWidget(self.cmd_input)
        self.send_cmd_layout.addWidget(self.send_button)
        self.send_cmd_layout.addStretch()

        # Помещаем горизонтальную строку в диагностический слой
        self.diagnostic_layout.addLayout(self.send_cmd_layout)
        # Добавляем диагностический слой в самое начало левой колонки
        self.left_column.addLayout(self.diagnostic_layout)

        # 6. Визуальная заглушка для ЛЕВОЙ колонки (располагается под панелью команд)
        self.left_placeholder = QLabel("Левая колонка\n(Таблицы параметров КНБК / Телеметрия)")
        self.left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_placeholder.setStyleSheet(
            "border: 1px dashed #4A90E2; color: #4A90E2; "
            "background-color: #F0F4F8; font-style: italic; font-size: 12px;"
        )
        self.left_column.addWidget(self.left_placeholder, stretch=1)

        # 7. Визуальная заглушка для ПРАВОЙ колонки
        self.right_placeholder = QLabel("Правая колонка\n(Графики забойных шоков / Монитор трафика)")
        self.right_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_placeholder.setStyleSheet(
            "border: 1px dashed #2ECC71; color: #2ECC71; "
            "background-color: #F4FBF7; font-style: italic; font-size: 12px;"
        )
        self.right_column.addWidget(self.right_placeholder, stretch=1)

        # Подключаем обе вертикальные колонки в общий горизонтальный слой
        self.columns_layout.addLayout(self.left_column, stretch=1)
        self.columns_layout.addLayout(self.right_column, stretch=1)

        # Добавляем двухколоночную структуру в главный вертикальный слой окна
        self.main_layout.addLayout(self.columns_layout, stretch=1)
