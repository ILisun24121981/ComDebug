# === ФАЙЛ: app/views/CmdDataSettingView.py (ЧАСТЬ 1 ИЗ 2) ===
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt


class CmdDataSettingView(QDialog):
    """
    Модальное окно конфигурации распределения структур отображения (PyQt6 View).
    Полностью независим от длин отправляемых кодограмм.
    """

    def __init__(self, saved_commands: list[str], available_structures: dict, current_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка структур отображения данных")
        self.setFixedSize(540, 420)
        self.setModal(True)

        self.available_structures = available_structures
        self.final_configuration = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Задайте соответствие ответов команд бинарным структурам View:</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Сохраненная команда", "Выбранная структура View", "Размер кадра (Байт)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self._populate_table_data(saved_commands, current_config)

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
# === ФАЙЛ: app/views/CmdDataSettingView.py (ЧАСТЬ 2 ИЗ 2) ===

    def _populate_table_data(self, saved_commands: list[str], current_config: dict):
        self.table.setRowCount(len(saved_commands))
        # Извлекаем карту соответствий из переданной конфигурации шаблона
        active_mappings = current_config.get("mappings", {})

        for row, cmd_name in enumerate(saved_commands):
            cmd_item = QTableWidgetItem(cmd_name)
            cmd_item.setFlags(cmd_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, cmd_item)

            struct_combo = QComboBox()
            struct_combo.addItem("— Нет —", None)

            active_struct_id = active_mappings.get(cmd_name)

            for struct_id, meta in self.available_structures.items():
                struct_combo.addItem(f"{struct_id} ({meta['size']} B)", struct_id)
                if struct_id == active_struct_id:
                    struct_combo.setCurrentIndex(struct_combo.count() - 1)

            struct_combo.currentIndexChanged.connect(lambda _, r=row: self._update_row_size_display(r))
            self.table.setCellWidget(row, 1, struct_combo)

            size_item = QTableWidgetItem("—")
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, size_item)

            self._update_row_size_display(row)

    def _update_row_size_display(self, row: int):
        combo = self.table.cellWidget(row, 1)
        size_item = self.table.item(row, 2)
        if combo and size_item:
            struct_id = combo.currentData()
            if struct_id and struct_id in self.available_structures:
                size_item.setText(str(self.available_structures[struct_id]["size"]))
            else:
                size_item.setText("—")

    def _handle_save_clicked(self):
        """Событие: Сохранение пачки маппингов."""
        mappings_result = {}

        for row in range(self.table.rowCount()):
            cmd_name = self.table.item(row, 0).text()
            combo = self.table.cellWidget(row, 1)
            struct_id = combo.currentData() if combo else None

            if struct_id:
                mappings_result[cmd_name] = struct_id

        # Формируем итоговый упакованный конфиг шаблона
        self.final_configuration = {
            "mappings": mappings_result
        }
        self.accept()

    def get_user_configuration(self) -> dict:
        return self.final_configuration
