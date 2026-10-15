# === ФАЙЛ: app/models/CmdPatternsManager.py (ЦЕЛИКОМ) ===
import json
import pathlib
import re


class CmdPatternsManager:
    """
    Модель управления шаблонами команд (MVC Model).
    Инкапсулирует чтение, сохранение и бинарный разбор кадров.
    """

    def __init__(self):
        self.config_dir = pathlib.Path("./Config")
        self.config_dir.mkdir(exist_ok=True)

    def load_patterns_names(self, protocol_name: str) -> list[str]:
        """Выбирает названия команд, игнорируя служебную секцию."""
        patterns = self._read_file(protocol_name)
        return [n for n in patterns.keys() if n != "__service_address__"]

    def load_service_addresses(self, protocol_name: str) -> dict:
        patterns = self._read_file(protocol_name)
        service_data = patterns.get("__service_address__", {})

        if service_data:
            return service_data

        if protocol_name == "Gels":
            return {"dst": "CA", "src": "17"}
        else:
            return {"dst": "8A", "src": "0A"}

    def save_service_addresses(
        self, protocol_name: str, dst_hex: str, src_hex: str
    ):
        if not protocol_name:
            return

        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        patterns = self._read_file(protocol_name)
        patterns["__service_address__"] = {
            "dst": dst_hex.upper(),
            "src": src_hex.upper()
        }

        ordered = {"__service_address__": patterns["__service_address__"]}
        for k, v in patterns.items():
            if k != "__service_address__":
                ordered[k] = v

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ordered, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка сохранения адресов: {e}")

    def extract_pattern_data(
        self, protocol_name: str, pattern_name: str
    ) -> dict:
        patterns = self._read_file(protocol_name)
        hex_string = patterns.get(pattern_name, "").replace(" ", "")

        result = {
            "dst_addr": 0x00, "src_addr": 0x00,
            "cmd_code": 0x00, "payload_bytes": b""
        }

        if not hex_string or pattern_name == "__service_address__":
            return result

        try:
            full_frame_bytes = bytes.fromhex(hex_string)
            if len(full_frame_bytes) < 5:
                return result

            result["dst_addr"] = int(full_frame_bytes[0])
            result["src_addr"] = int(full_frame_bytes[1])

            if protocol_name == "IDS":
                if len(full_frame_bytes) >= 6:
                    result["cmd_code"] = int(full_frame_bytes[4])
                    result["payload_bytes"] = full_frame_bytes[5:-1]
            elif protocol_name == "Aps":
                if len(full_frame_bytes) >= 7:
                    result["cmd_code"] = int(full_frame_bytes[4])
                    result["payload_bytes"] = full_frame_bytes[5:-2]
            elif protocol_name == "Gels":
                if len(full_frame_bytes) >= 7:
                    result["cmd_code"] = int(full_frame_bytes[2])
                    result["payload_bytes"] = full_frame_bytes[5:-2]
        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка разбора кадра: {e}")

        return result

    def save_pattern(
        self, protocol_name: str, pattern_name: str, raw_packet: bytes
    ) -> bool:
        if not protocol_name:
            protocol_name = "Unknown"

        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        patterns = self._read_file(protocol_name)
        patterns[pattern_name] = raw_packet.hex(" ").upper()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка записи в {file_name}: {e}")
            return False

    def delete_patterns(
        self, protocol_name: str, patterns_to_delete: list[str]
    ) -> bool:
        if not protocol_name or not patterns_to_delete:
            return False

        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        patterns = self._read_file(protocol_name)
        for name in patterns_to_delete:
            if name in patterns:
                del patterns[name]

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка при удалении: {e}")
            return False

    def generate_next_default_cmd_name(self, protocol_name: str) -> str:
        """
        ИСПРАВЛЕНО: Сканирует сохраненные шаблоны команд в файле
        {Protocol}CmdPatterns.json и вычисляет следующее имя TempX.
        """
        names = self.load_patterns_names(protocol_name)
        if not names:
            return "Temp1"

        max_num = 0
        pattern = re.compile(r"^Temp(\d+)$", re.IGNORECASE)

        for name in names:
            match = pattern.match(name.strip())
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        if max_num == 0:
            return "Temp1"

        return f"Temp{max_num + 1}"

    def _read_file(self, protocol_name: str) -> dict:
        if not protocol_name:
            return {}
        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
