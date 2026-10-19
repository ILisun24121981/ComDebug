from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QSpinBox, QTableWidget, \
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
from PyQt6.QtCore import Qt


class AutoPollingSettingView(QDialog):
    """
    Модальное окно конфигурации циклического автоматического опроса (PyQt6 View).
    Полностью очищено от ошибочной рекурсивной строки импорта самого себя.
    """

    def __init__(self, saved_patterns: list[str], current_config: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Настройка автоматического опроса")
        self.setFixedSize(480, 420)
        self.setModal(True)

        # Контейнер для выгрузки финального результата
        self.final_configuration = {}

        # Главный вертикальный слой окна
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. ГРУППА ОПРЕДЕЛЕНИЯ ВРЕМЕННЫХ РЕЖИМОВ
        mode_frame = QFrame()
        mode_frame.setStyleSheet("QFrame { border: 1px solid #CCCCCC; border-radius: 3px; background-color: #FAFAFA; }")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(6)

        mode_layout.addWidget(QLabel("<b>Выберите алгоритм забойного опроса:</b>"))

        self.radio_fixed = QRadioButton("Фиксированный интервал для всех команд (мс):")
        self.radio_individual = QRadioButton("Индивидуальный интервал для каждой команды")
        self.radio_chain = QRadioButton("Режим цепочки (пауза после полного цикла, мс):")

        # Настройка цифровых полей (SpinBox)
        self.spin_fixed = QSpinBox()
        self.spin_fixed.setRange(100, 60000)
        self.spin_fixed.setSingleStep(500)
        self.spin_fixed.setFixedWidth(90)

        self.spin_chain = QSpinBox()
        self.spin_chain.setRange(500, 120000)
        self.spin_chain.setSingleStep(1000)
        self.spin_chain.setFixedWidth(90)

        # Компоновка строк режимов
        row_fixed = QHBoxLayout()
        row_fixed.addWidget(self.radio_fixed)
        row_fixed.addWidget(self.spin_fixed)
        row_fixed.addStretch()
        mode_layout.addLayout(row_fixed)

        mode_layout.addWidget(self.radio_individual)

        row_chain = QHBoxLayout()
        row_chain.addWidget(self.radio_chain)
        row_chain.addWidget(self.spin_chain)
        row_chain.addStretch()
        mode_layout.addLayout(row_chain)

        layout.addWidget(mode_frame)

        # 2. ТАБЛИЦА ШАБЛОНОВ И ТАЙМИНГОВ
        layout.addWidget(QLabel("<b>Выберите команды из сохраненных шаблонов:</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Опрос", "Название шаблона команды", "Интервал (мс)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

        # Заполнение таблицы данными
        self._populate_table_data(saved_patterns, current_config)

        # Привязка событий переключения режимов
        self.radio_fixed.toggled.connect(self._update_ui_interactive_states)
        self.radio_individual.toggled.connect(self._update_ui_interactive_states)
        self.radio_chain.toggled.connect(self._update_ui_interactive_states)

        # 3. НИЖНИЙ РЯД КНОПОК УПРАВЛЕНИЯ МОДАЛЬНЫМ ОКНОМ
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_cancel = QPushButton("Отменить")
        self.btn_cancel.setFixedWidth(90)
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setFixedWidth(90)
        self.btn_save.setStyleSheet(
            "font-weight: bold; background-color: #1D6477; color: white; border: 1px solid #144E5B; border-radius: 2px;")
        self.btn_save.clicked.connect(self._handle_save_clicked)
        buttons_layout.addWidget(self.btn_save)

        layout.addLayout(buttons_layout)

        # Применяем стартовую конфигурацию
        self._load_initial_values(current_config)
        self._update_ui_interactive_states()

    def _populate_table_data(self, saved_patterns: list[str], current_config: dict):
        self.table.blockSignals(True)
        self.table.setRowCount(len(saved_patterns))
        patterns_meta = current_config.get("patterns", {})

        for row, name in enumerate(saved_patterns):
            meta = patterns_meta.get(name, {})

            check_item = QTableWidgetItem()
            check_item.setCheckState(Qt.CheckState.Checked if meta.get("enabled", False) else Qt.CheckState.Unchecked)
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, check_item)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            interval_val = str(meta.get("interval_ms", 2000))
            interval_item = QTableWidgetItem(interval_val)
            interval_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, interval_item)

        self.table.blockSignals(False)

    def _load_initial_values(self, current_config: dict):
        mode = current_config.get("mode", "fixed")
        self.spin_fixed.setValue(current_config.get("global_interval_ms", 2000))
        self.spin_chain.setValue(current_config.get("chain_delay_ms", 5000))

        if mode == "custom":
            self.radio_individual.setChecked(True)
        elif mode == "chain":
            self.radio_chain.setChecked(True)
        else:
            self.radio_fixed.setChecked(True)

    def _update_ui_interactive_states(self):
        is_fixed = self.radio_fixed.isChecked()
        is_chain = self.radio_chain.isChecked()
        is_custom = self.radio_individual.isChecked()

        self.spin_fixed.setEnabled(is_fixed)
        self.spin_chain.setEnabled(is_chain)

        for row in range(self.table.rowCount()):
            interval_item = self.table.item(row, 2)
            if interval_item:
                if is_custom:
                    interval_item.setFlags(
                        interval_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
                else:
                    interval_item.setFlags(interval_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _handle_save_clicked(self):
        """Событие: Нажата кнопка 'Сохранить'."""
        self.final_configuration = self._collect_form_data()
        self.accept()

    def _collect_form_data(self) -> dict:
        """Внутренний сборщик текущего состояния полей формы."""
        mode = "fixed"
        if self.radio_individual.isChecked():
            mode = "custom"
        elif self.radio_chain.isChecked():
            mode = "chain"

        patterns_result = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text()

            check_item = self.table.item(row, 0)
            is_enabled = False
            if check_item:
                is_enabled = (check_item.checkState().value == Qt.CheckState.Checked.value)

            interval_item = self.table.item(row, 2)
            try:
                val = int(interval_item.text()) if interval_item and interval_item.text().strip() else 2000
            except ValueError:
                val = 2000

            patterns_result[name] = {
                "enabled": is_enabled,
                "interval_ms": val
            }

        return {
            "mode": mode,
            "global_interval_ms": self.spin_fixed.value(),
            "chain_delay_ms": self.spin_chain.value(),
            "patterns": patterns_result
        }

    def get_user_configuration(self) -> dict:
        """Безопасный метод выгрузки данных после успешного закрытия окна."""
        return self.final_configuration
