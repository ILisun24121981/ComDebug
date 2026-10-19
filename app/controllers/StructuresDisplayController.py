# === ФАЙЛ: app/controllers/StructuresDisplayController.py ===
import struct
from PyQt6.QtCore import QObject, pyqtSignal


class StructuresDisplayController(QObject):
    """
    Выделенный контроллер декомпозиции бинарных структур данных (MVC Controller).
    Потокобезопасно транслирует распакованные величины КНБК через Qt-сигналы.
    """
    data_unpacked_signal = pyqtSignal(str, str, int)

    def __init__(self, cmd_view_manager, patterns_manager):
        super().__init__()
        self.cmd_view_manager = cmd_view_manager
        self.patterns_manager = patterns_manager
        self.live_display_dialog = None

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
        """Динамически распаковывает payload и генерирует безопасный сигнал для GUI."""
        if not self.live_display_dialog or not self.live_display_dialog.isVisible():
            return
        if not current_pattern_name:
            return

        # 1. Извлекаем маппинги текущего выбранного шаблона
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

        # 2. Выбор порядка байт КНБК КНБК
        byte_order_marker = ">" if active_proto == "Aps" else "<"

        # Полная таблица типов данных промышленной телеметрии (включая биты)
        type_mapping = {
            "uint32": "I", "int32": "i",
            "uint16": "H", "int16": "h",
            "uint8": "B", "int8": "b",
            "uint64": "Q", "int64": "q",
            "float": "f", "double": "d",
            "3bits": "B", "2bits": "B", "4bits": "B", "1bit": "B"
        }

        # 3. Безопасная сборка форматной строки
        format_parts = [byte_order_marker]
        for field in fields_list:
            # Очищаем строку типа от мусорных спецсимволов и пробелов
            f_type = str(field.get("type", "uint32")).lower().strip()

            # Если тип битовый (например '3bits'), вычленяем его базовый контейнер
            if "bits" in f_type or "bit" in f_type:
                format_parts.append("B")
            else:
                format_parts.append(type_mapping.get(f_type, "I"))

        fmt_string = "".join(format_parts)

        try:
            expected_size = struct.calcsize(fmt_string)
        except Exception:
            return

        # 4. Жесткая валидация достаточности физического буфера
        if len(payload_bytes) < expected_size:
            print(
                f"[StructuresDisplayController] ОШИБКА: Буфер прибора ({len(payload_bytes)} Б) меньше структуры ({expected_size} Б)")
            return

        # 5. Потокобезопасная распаковка и отправка в сигнальное русло Qt
        try:
            # Берем точный атомарный кусок памяти буфера ответа
            slice_bytes = bytes(payload_bytes[:expected_size])
            unpacked_values = struct.unpack(fmt_string, slice_bytes)

            for idx, field in enumerate(fields_list):
                f_name = field.get("name", "Unknown")
                live_value = unpacked_values[idx]

                # Эмитируем межпотоковый Qt-сигнал
                self.data_unpacked_signal.emit(struct_name, f_name, int(live_value))
        except Exception as e:
            print(f"[StructuresDisplayController] Исключение распаковки: {e}")
