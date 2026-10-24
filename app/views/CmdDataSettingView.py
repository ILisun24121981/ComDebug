# === ФАЙЛ: app/views/CmdDataSettingView.py (ЧАСТЬ 1 ИЗ 2 С КНОПКОЙ СОЗДАНИЯ) ===
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QInputDialog,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from app.models.CmdViewManager import CmdViewManager


class CmdDataSettingView(QDialog):
    """
    Модальное окно конфигурации распределения структур отображения (PyQt6 View).
    Дополнен функционалом динамического создания шаблонов JSON на жестком диске.
    """

    def __init__(self, saved_commands: list[str], available_structures: dict, current_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка структур отображения данных")
        self.setFixedSize(620, 420)
        self.setModal(True)

        self.available_structures = available_structures
        self.final_configuration = {}
        self.cmd_view_manager = CmdViewManager()
        self.saved_commands = saved_commands
        self.current_config = current_config

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

        # Нижний ряд кнопок управления
        buttons_layout = QHBoxLayout()

        # ВНЕДРЕНИЕ: Левая кнопка создания новой структуры отображения КНБК
        self.btn_create_struct = QPushButton("Создать структуру отображения")
        self.btn_create_struct.setHeight = 24
        self.btn_create_struct.setStyleSheet("font-weight: normal; color: #1D6477;")
        self.btn_create_struct.clicked.connect(self._handle_create_structure_clicked)
        buttons_layout.addWidget(self.btn_create_struct)

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

    # === ФАЙЛ: app/views/CmdDataSettingView.py (ЧАСТЬ 2 ИЗ 2 С КНОПКОЙ СОЗДАНИЯ) ===

    def _populate_table_data(self, saved_commands: list[str], current_config: dict):
        self.table.setRowCount(len(saved_commands))
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

    def _handle_create_structure_clicked(self):
        """Обработчик нажатия кнопки 'Создать структуру отображения'."""
        # Вычисляем следующее дефолтное имя TempX на основе парсинга файлов
        default_name = self.cmd_view_manager.generate_next_struct_default_name()

        # Вызываем встроенный диалог ввода текста Qt
        text, ok = QInputDialog.getText(
            self, "Создание структуры",
            "Введите название файла структуры отображения:",
            text=default_name
        )

        if ok and text.strip():
            struct_clean_name = text.strip()
            success, message = self.cmd_view_manager.create_empty_structure_template(struct_clean_name)

            if success:
                QMessageBox.information(
                    self, "Успех",
                    f"Файл заготовки '{struct_clean_name}.json' успешно создан!\n\n"
                    "Заполните структуру данными в формате, указанном в примере, "
                    "в открывшемся окне проводника."
                )
                # Перечитываем доступные файлы и обновляем таблицу, чтобы новый файл сразу отобразился в ComboBox
                self.available_structures = self.cmd_view_manager.load_available_view_structures()
                self._populate_table_data(self.saved_commands, self.current_config)
            else:
                QMessageBox.critical(self, "Ошибка создания", f"Не удалось создать файл шаблона.\nДетали: {message}")

    def _handle_save_clicked(self):
        """Событие: Сохранение пачки маппингов."""
        mappings_result = {}

        for row in range(self.table.rowCount()):
            cmd_name = self.table.item(row, 0).text()
            combo = self.table.cellWidget(row, 1)
            struct_id = combo.currentData() if combo else None

            if struct_id:
                mappings_result[cmd_name] = struct_id

        self.final_configuration = {
            "mappings": mappings_result
        }
        self.accept()

    def get_user_configuration(self) -> dict:
        return self.final_configuration
