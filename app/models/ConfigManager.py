import os
import json
import pathlib
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Класс-менеджер для централизованной работы с конфигурациями проекта.
    Изолирует логику чтения JSON и XML от бизнес-моделей приложения.
    """

    def __init__(self):
        self.project_root: pathlib.Path = pathlib.Path(os.getcwd()).resolve()
        self.cmd_json_path: pathlib.Path = self.project_root / "Config" / "cmd.json"
        self.port_json_path: pathlib.Path = self.project_root / "Config" / "port_settings.json"
        self.struct_path: pathlib.Path = self.project_root / "Config" / "struct.xml"
        self.ids_json_path: pathlib.Path = self.project_root / "Config" / "IDS_ID.json"

    @staticmethod
    def _parse_int(value: Any) -> int:
        """Вспомогательный метод для безопасной конвертации HEX-строк или чисел в int."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.lower().startswith("0x"):
                return int(value, 16)
            return int(value)
        return 0

    def get_port_settings(self, protocol_name: str) -> Dict[str, Any]:
        """
        Вычитывает физические настройки связи COM-порта для указанного протокола.
        Данные загружаются из изолированного файла Config/port_settings.json.
        """
        default_settings = {
            "baud_rate": 9600, "bytesize": 8, "parity": "None",
            "stopbits": 1.0, "flow_control": "None"
        }

        if not self.port_json_path.exists():
            print(f"[ConfigManager] Предупреждение: {self.port_json_path.name} не найден.")
            return default_settings

        try:
            with open(self.port_json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            proto_data = config_data.get("protocols", {}).get(protocol_name, {})
            if not proto_data:
                return default_settings

            return {
                "baud_rate": int(proto_data.get("Speed", 9600)),
                "bytesize": int(proto_data.get("DataBits", 8)),
                "parity": proto_data.get("Parity", "None"),
                "stopbits": float(proto_data.get("StopBits", 1.0)),
                "flow_control": proto_data.get("FlowControl", "None")
            }
        except Exception as e:
            print(f"[ConfigManager] Ошибка чтения настроек COM-порта: {e}")

        return default_settings
    def load_commands(self, target_mnem: str, protocol_name: str) -> Dict[str, Any]:
        """
        Загружает адреса, команды и таблицы ResponseMapping для устройства из cmd.json.
        Возвращает структурированный словарь с конфигурацией.
        """
        result = {
            "target_address": 0x00, "sender_address": 0x00,
            "commands": {}, "response_mappings": {}
        }

        if not self.cmd_json_path.exists():
            return result

        try:
            with open(self.cmd_json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            device_data = config_data.get("Device", {})
            if device_data.get("mnemonics") != target_mnem:
                return result

            protocol_data = device_data.get("protocols", {}).get(protocol_name, {})
            if not protocol_data:
                return result

            # Извлекаем адреса в зависимости от выбранного протокола обмена
            if protocol_name == "Gels":
                target_addr_raw = protocol_data.get("DeviceAddress", "0x00")
                sender_addr_raw = protocol_data.get("ModuleAddress", "0x00")
            else:
                target_addr_raw = protocol_data.get("DestinationAddress", "0x00")
                sender_addr_raw = protocol_data.get("SourceAddress", "0x00")

            result["target_address"] = self._parse_int(target_addr_raw)
            result["sender_address"] = self._parse_int(sender_addr_raw)

            # Собираем жесткие команды
            json_commands = protocol_data.get("Commands", {})
            for key, meta in json_commands.items():
                result["commands"][key] = {
                    "value": self._parse_int(meta.get("value")),
                    "struct_id": meta.get("struct_id")
                }

            # Собираем таблицу ResponseMapping (для динамических ответов радиоканала)
            json_mapping = protocol_data.get("ResponseMapping", {})
            for packet_id_str, meta in json_mapping.items():
                packet_id = self._parse_int(packet_id_str)
                result["response_mappings"][packet_id] = meta.get("struct_id")

        except Exception as e:
            print(f"[ConfigManager] Ошибка парсинга команд из JSON: {e}")

        return result

    def load_structures(self, byte_order_marker: str) -> Dict[str, Any]:
        """
        Загружает описание бинарных структур из Config/struct.xml.
        Автоматически компилирует форматные строки для struct.unpack с учетом byte_order.
        """
        import struct
        structures_dict = {}

        if not self.struct_path.exists():
            print(f"[ConfigManager] Ошибка: {self.struct_path.name} отсутствует!")
            return structures_dict

        try:
            tree = ET.parse(str(self.struct_path))
            root = tree.getroot()
            for node in root.findall("Structure"):
                struct_id = node.get("id")
                if not struct_id:
                    continue

                fields = []
                format_parts = [byte_order_marker]  # Первым идет маркер порядка байт (< или >)

                for f_node in node.findall("Field"):
                    fields.append(f_node.get("name"))
                    format_parts.append(f_node.get("type"))

                fmt_string = "".join(format_parts)
                structures_dict[struct_id] = {
                    "format": fmt_string,
                    "fields": fields,
                    "size": struct.calcsize(fmt_string)
                }
        except Exception as e:
            print(f"[ConfigManager] Ошибка разбора struct.xml: {e}")

        return structures_dict

    def load_ids_identifiers(self) -> Dict[int, str]:
        """
        Загружает карту динамических идентификаторов параметров для протокола IDS из IDS_ID.json.
        Возвращает плоский словарь {int_id: "строковое_имя"}.
        """
        default_ids = {
            0x01: "INC", 0x02: "AZM", 0x03: "SHRISK", 0x04: "MSHRMS",
            0x05: "SS", 0x06: "CMD", 0x07: "GRUP", 0x08: "GRR",
            0x09: "GRD", 0x0A: "GRL", 0x0B: "GRA", 0xF0: "STATUS"
        }

        if not self.ids_json_path.exists():
            print(f"[ConfigManager] Предупреждение: {self.ids_json_path.name} не найден.")
            return default_ids

        try:
            with open(self.ids_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = {}
            json_ids = data.get("IDS_Identifiers", {})
            for hex_id_str, meta in json_ids.items():
                int_id = int(hex_id_str, 16) if hex_id_str.lower().startswith("0x") else int(hex_id_str)
                result[int_id] = meta.get("name", f"ID_{hex_id_str}")
            return result
        except Exception as e:
            print(f"[ConfigManager] Ошибка парсинга IDS_ID.json: {e}")
            return default_ids
