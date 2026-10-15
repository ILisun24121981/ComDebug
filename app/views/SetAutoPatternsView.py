# === ФАЙЛ: app/views/SetAutoPatternsView.py (ЧАСТЬ 1 ИЗ 2) ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QRadioButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class SetAutoPatternsView(QWidget):
    """
    Графическая панель автоопроса (PyQt6 View).
    Полностью устраняет наложение элементов и намертво фиксирует
    соосность с левым пультом (ширина 350px) без прыжков и рамок.
    """
    mode_radio_changed = pyqtSignal(bool)  # True - Saved, False - New

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.border_frame = QFrame()
        self.border_frame.setStyleSheet("""
            QFrame { 
                border: 1px solid #CCCCCC; 
                border-radius: 3px; 
                background-color: #FAFAFA; 
            }
            QLabel { 
                border: none; 
                background-color: transparent; 
                color: #333333; 
                font-weight: bold; 
            }
            QLineEdit, QComboBox { 
                border: 1px solid #B0B0B0; 
                border-radius: 2px; 
                background-color: #FFFFFF; 
                padding-left: 3px; 
                height: 22px;
            }
            QPushButton { 
                border: 1px solid #999999; 
                border-radius: 2px; 
                background-color: #EAEAEA; 
                color: #222222; 
                font-size: 11px; 
                height: 24px;
            }
            QPushButton:hover { border-color: #666666; background-color: #DFDFDF; }
            QRadioButton { background-color: transparent; color: #000000; }
            QRadioButton::indicator { width: 12px; height: 12px; border: 1px solid #777777; border-radius: 7px; background-color: #FFFFFF; }
            QRadioButton::indicator:checked { border: 2px solid #1D6477; background-color: #E6F2F7; width: 8px; height: 8px; padding: 2px; border-radius: 7px; }
        """)

        self.grid = QGridLayout(self.border_frame)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setSpacing(6)
        self.main_layout.addWidget(self.border_frame)

        self.setFixedWidth(350)

        self.radio_container = QWidget()
        radio_layout = QHBoxLayout(self.radio_container)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(12)

        self.lbl_radio_title = QLabel("Автоопрос:")
        radio_layout.addWidget(self.lbl_radio_title)

        self.radio_saved = QRadioButton("Сохраненный")
        self.radio_new = QRadioButton("Новый")

        self.radio_saved.toggled.connect(
            lambda ch: self.mode_radio_changed.emit(True) if ch else None
        )
        self.radio_new.toggled.connect(
            lambda ch: self.mode_radio_changed.emit(False) if ch else None
        )

        radio_layout.addWidget(self.radio_saved)
        radio_layout.addWidget(self.radio_new)
        radio_layout.addStretch()
        self.grid.addWidget(self.radio_container, 0, 0, 1, 3, Qt.AlignmentFlag.AlignLeft)

        self.lbl_fallback = QLabel("Автоопрос:")
        self.grid.addWidget(self.lbl_fallback, 0, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.btn_initial_config = QPushButton("Настроить автоопрос")
        self.btn_initial_config.setFixedWidth(175)
        self.grid.addWidget(self.btn_initial_config, 1, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.combo_patterns = QComboBox()
        self.combo_patterns.setFixedWidth(175)
        self.grid.addWidget(self.combo_patterns, 1, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.input_pattern_name = QLineEdit()
        self.input_pattern_name.setFixedWidth(175)
        self.input_pattern_name.setPlaceholderText("Имя шаблона")
        self.grid.addWidget(self.input_pattern_name, 1, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.btn_start = QPushButton("Запустить")
        self.btn_start.setFixedWidth(145)
        self.btn_start.setStyleSheet(
            "font-weight: bold; background-color: #E6F2F7; border-color: #1D6477; color: #1D6477;")
        self.grid.addWidget(self.btn_start, 1, 2, Qt.AlignmentFlag.AlignLeft)

        self.btn_save_pattern = QPushButton("Сохранить")
        self.btn_save_pattern.setFixedWidth(90)
        self.grid.addWidget(self.btn_save_pattern, 2, 0, Qt.AlignmentFlag.AlignLeft)

        self.btn_edit_patterns = QPushButton("Редактировать")
        self.btn_edit_patterns.setFixedWidth(90)
        self.grid.addWidget(self.btn_edit_patterns, 2, 0, Qt.AlignmentFlag.AlignLeft)

        self.btn_config = QPushButton("Настроить")
        self.btn_config.setFixedWidth(80)
        self.grid.addWidget(self.btn_config, 2, 1, Qt.AlignmentFlag.AlignLeft)

        self.btn_stop = QPushButton("Остановить")
        self.btn_stop.setFixedWidth(145)
        self.grid.addWidget(self.btn_stop, 2, 2, Qt.AlignmentFlag.AlignLeft)

        self.grid.setRowStretch(3, 1)
        self.radio_saved.setChecked(True)
        self.show_initial_empty_state()

    # === ФАЙЛ: app/views/SetAutoPatternsView.py (ЧАСТЬ 2 ИЗ 2) ===

    def show_initial_empty_state(self):
        """Стартовый вид: Мягко скрывает элементы без удаления хэндлов окон."""
        self.radio_container.setVisible(False)
        self.lbl_fallback.setVisible(True)
        self.btn_initial_config.setVisible(True)

        self.combo_patterns.setVisible(False)
        self.input_pattern_name.setVisible(False)
        self.btn_start.setVisible(False)
        self.btn_config.setVisible(False)
        self.btn_edit_patterns.setVisible(False)
        self.btn_save_pattern.setVisible(False)
        self.btn_stop.setVisible(False)

    def set_initial_capture_name_view(self):
        self.radio_container.setVisible(False)
        self.lbl_fallback.setVisible(True)
        self.btn_initial_config.setVisible(False)

        self.combo_patterns.setVisible(False)
        self.input_pattern_name.setVisible(True)
        self.btn_start.setVisible(True)
        self.btn_config.setVisible(True)
        self.btn_edit_patterns.setVisible(False)
        self.btn_save_pattern.setVisible(True)
        self.btn_stop.setVisible(True)

    def set_saved_mode_view(self):
        self.radio_container.setVisible(True)
        self.lbl_fallback.setVisible(False)
        self.btn_initial_config.setVisible(False)

        self.combo_patterns.setVisible(True)
        self.input_pattern_name.setVisible(False)
        self.btn_start.setVisible(True)
        self.btn_config.setVisible(True)
        self.btn_edit_patterns.setVisible(True)
        self.btn_save_pattern.setVisible(False)
        self.btn_stop.setVisible(True)

    def set_new_mode_view(self):
        self.radio_container.setVisible(True)
        self.lbl_fallback.setVisible(False)
        self.btn_initial_config.setVisible(False)

        self.combo_patterns.setVisible(False)
        self.input_pattern_name.setVisible(True)
        self.btn_start.setVisible(True)
        self.btn_config.setVisible(True)
        self.btn_edit_patterns.setVisible(False)
        self.btn_save_pattern.setVisible(True)
        self.btn_stop.setVisible(True)

    def set_running_ui_state(self, is_running: bool):
        self.btn_start.setEnabled(not is_running)
        self.btn_config.setEnabled(not is_running)
        self.btn_initial_config.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)

        self.radio_saved.setEnabled(not is_running)
        self.radio_new.setEnabled(not is_running)
        self.combo_patterns.setEnabled(not is_running)
        self.input_pattern_name.setEnabled(not is_running)
        self.btn_edit_patterns.setEnabled(not is_running)
        self.btn_save_pattern.setEnabled(not is_running)
