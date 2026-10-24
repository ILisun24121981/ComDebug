# === ФАЙЛ: app/controllers/StructuresDisplayController.py (ЧАСТЬ 1 ИЗ 2) ===
import struct
import re
from PyQt6.QtCore import QObject, pyqtSignal


class StructuresDisplayController(QObject):
    """
    Выделенный контроллер декомпозиции бинарных структур данных Си (MVC Controller).
    Потокобезопасно транслирует распакованные Си-величины КНБК через Qt-сигналы.
    """
    data_unpacked_signal = pyqtSignal(str, str, int)

    def __init__(self, cmd_view_manager, patterns_manager):
        super().__init__()
        self.cmd_view_manager = cmd_view_manager
        self.patterns_manager = patterns_manager
        self.live_display_dialog = None

        # Маппинг стандартных типов данных языка Си в символы struct Python
        self.c_type_mapping = {
            "uint32_t": "I", "unsigned int": "I", "unsigned long": "I",
            "int32_t": "i", "int": "i", "long": "i",
            "uint16_t": "H", "unsigned short": "H",
            "int16_t": "h", "short": "h",
            "uint8_t": "B", "unsigned char": "B",
            "int8_t": "b", "char": "b", "signed char": "b",
            "uint64_t": "Q", "unsigned long long": "Q",
            "int64_t": "q", "long long": "q",
            "float": "f",
            "double": "d"
        }

    def set_active_display_dialog(self, dialog):
        """Регистрирует текущую активную форму вывода."""
        self.live_display_dialog = dialog
        if self.live_display_dialog:
            try:
                self.data_unpacked_signal.disconnect()
            except TypeError:
                pass
            self.data_unpacked_signal.connect(self.live_display_dialog.update_live_telemetry_field)

    def process_and_unpack_payload(self, active_proto: str, current_pattern_name: str, command_code: int,
                                   payload_bytes: bytes):
        """Динамически распаковывает payload Си-структур и генерирует безопасный сигнал для GUI."""
        if not self.live_display_dialog or not self.live_display_dialog.isVisible():
            return
        if not current_pattern_name:
            return

        config = self.cmd_view_manager.load_pattern_config(active_proto, current_pattern_name)
        active_mappings = config.get("mappings", {})

        target_cmd_name = None
        patterns = self.patterns_manager._read_file(active_proto)
        for p_name in patterns.keys():
            if p_name == "__service_address__":
                continue
            frame_data = self.patterns_manager.extract_pattern_data(active_proto, p_name)
            if frame_data.get("cmd_code") == command_code:
                target_cmd_name = p_name
                break

        if not target_cmd_name or target_cmd_name not in active_mappings:
            return

        struct_name = active_mappings[target_cmd_name]
        available_views = self.cmd_view_manager.load_available_view_structures()
        if struct_name not in available_views:
            return

        struct_meta = available_views[struct_name]
        fields_list = struct_meta.get("fields", [])

        # Выбор порядка байт КНБК (Эндианность)
        byte_order_marker = ">" if active_proto == "Aps" else "<"

        # Регулярное выражение для поиска произвольных Си-битовых полей, например: "uint8_t:3" или "int:5"
        bitfield_pattern = re.compile(r"^([^:]+):(\d+)$")
        # === ФАЙЛ: app/controllers/StructuresDisplayController.py (ЧАСТЬ 2 ИЗ 2) ===

        # Проход 1: Анализ структуры и компиляция чистой форматной строки struct
        format_parts = [byte_order_marker]
        bit_processing_queue = []  # Список для отложенного побитового разбора

        # Переменные для сборки последовательных битовых полей КНБК
        current_bit_container_size = 0
        current_bit_accumulated = 0

        for idx, field in enumerate(fields_list):
            f_type = str(field.get("type", "uint32_t")).strip()
            bit_match = bitfield_pattern.match(f_type)

            if bit_match:
                # Обнаружено Си битовое поле произвольного размера
                base_c_type = bit_match.group(1).strip()
                bit_width = int(bit_match.group(2))

                # Определяем размер базового Си-контейнера в байтах
                sample_fmt = self.c_type_mapping.get(base_c_type, "B")
                container_bytes = struct.calcsize(sample_fmt)

                # Если это первое битовое поле или мы заполнили предыдущий контейнер — выделяем новый байт/слово
                if current_bit_container_size == 0 or current_bit_accumulated + bit_width > (container_bytes * 8):
                    format_parts.append(sample_fmt)
                    current_bit_container_size = container_bytes
                    current_bit_accumulated = 0

                # Запоминаем параметры для Прохода 2 (индекс в unpaked_values, смещение, маска)
                bit_processing_queue.append({
                    "field_index": idx,
                    "field_name": field.get("name", "Unknown"),
                    "struct_fmt_index": len(format_parts) - 1 - 1,  # Корректируем индекс с учетом маркера порядка байт
                    "bit_offset": current_bit_accumulated,
                    "bit_mask": (1 << bit_width) - 1,
                    "is_bit": True
                })
                current_bit_accumulated += bit_width
            else:
                # Обычный стандартный Си-тип данных
                current_bit_container_size = 0  # Сбрасываем битовый контейнер
                fmt_char = self.c_type_mapping.get(f_type, "I")
                format_parts.append(fmt_char)

                bit_processing_queue.append({
                    "field_index": idx,
                    "field_name": field.get("name", "Unknown"),
                    "struct_fmt_index": len(format_parts) - 1 - 1,
                    "is_bit": False
                })

        fmt_string = "".join(format_parts)
        print(f"[TRACE-Unpack] Скомпилированная Си-форматная строка: '{fmt_string}'")

        try:
            expected_size = struct.calcsize(fmt_string)
        except Exception as e:
            print(f"[TRACE-Unpack] Ошибка calcsize Си-формата: {e}")
            return

        if len(payload_bytes) < expected_size:
            print(
                f"[StructuresDisplayController] Буфер ({len(payload_bytes)} Б) меньше Си-структуры ({expected_size} Б)")
            return

        # Проход 2: Распаковка и атомарное извлечение бит
        try:
            slice_bytes = bytes(payload_bytes[:expected_size])
            unpacked_raw = struct.unpack(fmt_string, slice_bytes)

            for item in bit_processing_queue:
                f_name = item["field_name"]
                raw_value = unpacked_raw[item["struct_fmt_index"]]

                if item["is_bit"]:
                    # Вычленяем битовый срез с помощью побитового сдвига и маски
                    live_value = (raw_value >> item["bit_offset"]) & item["bit_mask"]
                else:
                    live_value = raw_value

                # Отправляем очищенное значение Си-переменной в сигнальное русло Qt
                self.data_unpacked_signal.emit(struct_name, f_name, int(live_value))

        except Exception as e:
            print(f"[StructuresDisplayController] Исключение Си-распаковки: {e}")
