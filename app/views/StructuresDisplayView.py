# === ФАЙЛ: app/views/StructuresDisplayView.py (ЧАСТЬ 1 ИЗ 2 С ЛОГАМИ) ===
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QScrollArea, QWidget, QFrame, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSlot


class StructuresDisplayView(QDialog):
    """
    Монитор декомпозиции забойных структур данных КНБК (Gels/Aps).
    Дополнен расширенной трассировкой для поиска причин аппаратного краша.
    """

    def __init__(self, active_mappings: dict, structures_definitions: dict, parent=None):
        print("[TRACE-StructuresDisplayView] Вход в __init__ конструктора окна...")
        super().__init__(parent)
        self.setWindowTitle("Монитор декомпозиции структур данных (Gels/Aps)")
        self.resize(850, 520)
        self.setMinimumSize(450, 350)

        self.value_inputs_registry = {}
        self.raw_values_cache = {}
        self.field_types_registry = {}
        self.active_formats = {}

        print("[TRACE-StructuresDisplayView] Создание корневых макетов QVBoxLayout и QScrollArea...")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #EAEAEA;")

        self.scroll_content_widget = QWidget()
        self.horizontal_layout = QHBoxLayout(self.scroll_content_widget)
        self.horizontal_layout.setContentsMargins(5, 5, 5, 5)
        self.horizontal_layout.setSpacing(12)
        self.horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        print("[TRACE-StructuresDisplayView] Переход к вызову метода _build_telemetry_frames...")
        self._build_telemetry_frames(active_mappings, structures_definitions)

        print("[TRACE-StructuresDisplayView] Укладываем макеты в контейнер прокрутки...")
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area)
        print("[TRACE-StructuresDisplayView] Конструктор __init__ успешно завершил работу.")

    # === ФАЙЛ: app/views/StructuresDisplayView.py (ЧАСТЬ 2 ИЗ 2 С ЛОГАМИ) ===

    def _build_telemetry_frames(self, active_mappings: dict, structures_definitions: dict):
        """Парсит маппинги и строит фреймы со строчной компоновкой и блоком смены формата."""
        print(
            f"[TRACE-StructuresDisplayView] Метод _build_telemetry_frames запущен. Маппинги для сборки: {active_mappings}")
        used_struct_names = set(active_mappings.values())
        print(f"[TRACE-StructuresDisplayView] Уникальные структуры View, требующие отрисовки: {used_struct_names}")

        if not used_struct_names:
            print("[TRACE-StructuresDisplayView] Список требуемых структур пуст. Вывод заглушки.")
            empty_lbl = QLabel("В текущей конфигурации отображения нет назначенных структур View.")
            empty_lbl.setStyleSheet("color: #666666; font-style: italic; font-size: 13px;")
            self.horizontal_layout.addWidget(empty_lbl)
            return

        for struct_name in sorted(used_struct_names):
            print(f"[TRACE-StructuresDisplayView] ---> Начинаем сборку фрейма для структуры: '{struct_name}'")
            if struct_name not in structures_definitions:
                print(
                    f"[TRACE-StructuresDisplayView] ВНИМАНИЕ: Описание структуры '{struct_name}' отсутствует в structures_definitions! Пропуск.")
                continue

            struct_meta = structures_definitions[struct_name]
            fields_list = struct_meta.get("fields", [])
            print(f"[TRACE-StructuresDisplayView] Метаданные структуры найдены. Обнаружено полей: {len(fields_list)}")

            # Инициализация внутренних хранилищ для фрейма
            self.active_formats[struct_name] = "dec"
            self.value_inputs_registry[struct_name] = {}
            self.raw_values_cache[struct_name] = {}
            self.field_types_registry[struct_name] = {}

            print(
                f"[TRACE-StructuresDisplayView] Создание объекта QFrame и применение CSS-стилей для '{struct_name}'...")
            frame = QFrame()
            frame.setFixedWidth(290)
            frame.setStyleSheet("""
                QFrame { border: 1px solid #999999; border-radius: 4px; background-color: #FAFAFA; }
                QLabel { border: none; font-weight: bold; color: #444444; font-size: 11px; }
                QLineEdit {
                    border: 1px solid #CCCCCC; border-radius: 1px; background-color: #FFFFFF;
                    color: #0000FF; font-family: monospace; font-size: 11px; height: 18px; padding-left: 2px;
                }
                QRadioButton { background: transparent; color: #000000; font-size: 11px; font-weight: normal; }
                QRadioButton::indicator { width: 12px; height: 12px; border: 1px solid #777777; border-radius: 7px; background-color: #FFFFFF; }
                QRadioButton::indicator:checked { border: 2px solid #1D6477; background-color: #E6F2F7; width: 8px; height: 8px; padding: 2px; border-radius: 7px; }
            """)

            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame_layout.setSpacing(2)

            title_lbl = QLabel(f"СТРУКТУРА: {struct_name.upper()}")
            title_lbl.setStyleSheet("color: #1D6477; font-size: 12px; font-weight: bold; padding-bottom: 2px;")
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(title_lbl)

            print(
                f"[TRACE-StructuresDisplayView] Создание панели радиокнопок форматов (Dec/Hex/Bin) для '{struct_name}'...")
            format_widget = QWidget()
            format_widget.setStyleSheet("border: none; background: transparent;")
            format_layout = QHBoxLayout(format_widget)
            format_layout.setContentsMargins(0, 0, 0, 4)
            format_layout.setSpacing(12)

            rb_dec = QRadioButton("Dec")
            rb_hex = QRadioButton("Hex")
            rb_bin = QRadioButton("Bin")
            rb_dec.setChecked(True)

            bg = QButtonGroup(frame)
            bg.addButton(rb_dec)
            bg.addButton(rb_hex)
            bg.addButton(rb_bin)

            rb_dec.toggled.connect(lambda ch, s=struct_name: self._handle_format_toggle(s, "dec") if ch else None)
            rb_hex.toggled.connect(lambda ch, s=struct_name: self._handle_format_toggle(s, "hex") if ch else None)
            rb_bin.toggled.connect(lambda ch, s=struct_name: self._handle_format_toggle(s, "bin") if ch else None)

            format_layout.addStretch()
            format_layout.addWidget(rb_dec)
            format_layout.addWidget(rb_hex)
            format_layout.addWidget(rb_bin)
            format_layout.addStretch()
            frame_layout.addWidget(format_widget)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("color: #DDDDDD; margin-bottom: 4px;")
            frame_layout.addWidget(line)

            print(f"[TRACE-StructuresDisplayView] Построение соосной QGridLayout сетки полей для '{struct_name}'...")
            grid_widget = QWidget()
            grid_widget.setStyleSheet("border: none; background: transparent;")
            grid = QGridLayout(grid_widget)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(4)

            for idx, field in enumerate(fields_list):
                f_name = field.get("name", "Unknown")
                f_type = field.get("type", "uint32").lower().strip()

                print(f"[TRACE-StructuresDisplayView] Поле {idx}: name='{f_name}', type='{f_type}'")
                self.field_types_registry[struct_name][f_name] = f_type

                lbl_name = QLabel(f_name)
                lbl_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                grid.addWidget(lbl_name, idx, 0)

                val_input = QLineEdit()
                val_input.setText("—")
                val_input.setReadOnly(True)
                val_input.setFixedWidth(140)
                grid.addWidget(val_input, idx, 1)

                self.value_inputs_registry[struct_name][f_name] = val_input

            frame_layout.addWidget(grid_widget)
            frame_layout.addStretch()
            self.horizontal_layout.addWidget(frame)
            print(
                f"[TRACE-StructuresDisplayView] <--- Фрейм для структуры '{struct_name}' собран полностью и добавлен в макет.")

    def _handle_format_toggle(self, struct_name: str, fmt_type: str):
        self.active_formats[struct_name] = fmt_type
        if struct_name in self.raw_values_cache:
            for field_name, raw_val in self.raw_values_cache[struct_name].items():
                formatted_str = self._format_numeric_value(struct_name, field_name, raw_val)
                if field_name in self.value_inputs_registry[struct_name]:
                    self.value_inputs_registry[struct_name][field_name].setText(formatted_str)

    def _format_numeric_value(self, struct_name: str, field_name: str, value) -> str:
        if not isinstance(value, int):
            return str(value)

        fmt = self.active_formats.get(struct_name, "dec")
        f_type = self.field_types_registry.get(struct_name, {}).get(field_name, "uint32")

        if fmt == "hex":
            if "8" in f_type: return f"0x{value & 0xFF:02X}"
            if "16" in f_type: return f"0x{value & 0xFFFF:04X}"
            return f"0x{value & 0xFFFFFFFF:08X}"

        elif fmt == "bin":
            if "8" in f_type: return f"0b{value & 0xFF:08b}"
            if "16" in f_type:
                v = value & 0xFFFF
                return f"0b{v >> 8:08b}_{v & 0xFF:08b}"
            v = value & 0xFFFFFFFF
            return f"0b{v >> 24:08b}_{v >> 16 & 0xFF:08b}_{v >> 8 & 0xFF:08b}_{v & 0xFF:08b}"

        if f_type == "int16":
            return str(value if value < 32768 else value - 65536)
        if f_type == "int8":
            return str(value if value < 128 else value - 256)
        return str(value)

    @pyqtSlot(str, str, int)
    def update_live_telemetry_field(self, struct_name: str, field_name: str, value: int):
        if struct_name not in self.value_inputs_registry or field_name not in self.value_inputs_registry[struct_name]:
            return
        if struct_name not in self.raw_values_cache:
            self.raw_values_cache[struct_name] = {}
        self.raw_values_cache[struct_name][field_name] = value
        display_str = self._format_numeric_value(struct_name, field_name, value)
        self.value_inputs_registry[struct_name][field_name].setText(display_str)