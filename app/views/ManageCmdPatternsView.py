from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QScrollArea, QPushButton, \
    QWidget, QLabel, QFrame
from PyQt6.QtCore import Qt


class ManageCmdPatternsView(QDialog):
    """
    Модальное окно управления и удаления сохраненных шаблонов команд (PyQt6 View).
    Использует строгий нативный промышленный стиль чекбоксов.
    """

    def __init__(self, pattern_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование сохраненных команд")
        self.setMinimumSize(350, 400)
        self.setModal(True)

        self.checkboxes = {}  # {pattern_name: QCheckBox}

        # Корневой слой диалога
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Чекбокс общего выделения в шапке окна
        self.select_all_checkbox = QCheckBox("Выделить все")
        self.select_all_checkbox.setStyleSheet("QCheckBox { color: #333333; font-weight: bold; }")
        self.select_all_checkbox.clicked.connect(self._handle_select_all_clicked)
        layout.addWidget(self.select_all_checkbox)

        # Разделительная линия
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(line)

        # 2. Область прокрутки со списком названий команд
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: 1px solid #CCCCCC; background-color: #FFFFFF; border-radius: 2px;")

        container_widget = QWidget()
        self.grid = QGridLayout(container_widget)
        self.grid.setSpacing(6)
        self.grid.setContentsMargins(5, 5, 5, 5)

        # Строим строки команд
        self._build_rows(pattern_names)

        self.scroll_area.setWidget(container_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        # 3. Нижний горизонтальный ряд кнопок управления
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Кнопка «Удалить»
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setFixedHeight(28)
        self.delete_button.setStyleSheet(
            "font-weight: bold; background-color: #D9534F; color: white; border: 1px solid #D43F3A; border-radius: 2px;")
        buttons_layout.addWidget(self.delete_button, stretch=1)

        # Кнопка «ОК»
        self.ok_button = QPushButton("ОК")
        self.ok_button.setFixedHeight(28)
        self.ok_button.setStyleSheet(
            "font-weight: bold; background-color: #EAEAEA; color: #222222; border: 1px solid #999999; border-radius: 2px;")
        self.ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_button, stretch=1)

        layout.addLayout(buttons_layout)

    def _build_rows(self, pattern_names: list[str]):
        """Заполняет список имеющимися названиями шаблонов."""
        if not pattern_names:
            empty_lbl = QLabel("Нет сохраненных шаблонов")
            empty_lbl.setStyleSheet("color: #777777; font-style: italic; padding: 5px;")
            self.grid.addWidget(empty_lbl, 0, 0)
            self.select_all_checkbox.setEnabled(False)
            return

        for row, name in enumerate(pattern_names):
            cb = QCheckBox(name)

            # Применяем точный стиль отмеченного состояния, дублирующий радиокнопки КНБК
            cb.setStyleSheet("""
                QCheckBox { color: #000000; font-weight: normal; padding-top: 1px; padding-bottom: 1px; }
                QCheckBox::indicator:checked {
                    box-sizing: border-box;
                    border: 2px solid #1D6477;
                    background-color: #E6F2F7;
                }
            """)
            self.grid.addWidget(cb, row, 0)
            self.checkboxes[name] = cb

        self.grid.setRowStretch(len(pattern_names), 1)

    def _handle_select_all_clicked(self, is_checked: bool):
        """Реализует массовое выделение чекбоксов списка."""
        for cb in self.checkboxes.values():
            cb.setChecked(is_checked)

    def get_selected_patterns(self) -> list[str]:
        """Возвращает список названий шаблонов, отмеченных галочками."""
        return [name for name, cb in self.checkboxes.items() if cb.isChecked()]
