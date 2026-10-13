import json
import pathlib


class CmdPatternsManager:
    """
    Модель управления шаблонами команд (MVC Model).
    Полностью инкапсулирует чтение, сохранение и бинарный разбор кадров по протоколам.
    """

    def __init__(self):
        self.config_dir = pathlib.Path("./Config")
        self.config_dir.mkdir(exist_ok=True)

    def load_patterns_names(self, protocol_name: str) -> list[str]:
        """Вычитывает JSON и возвращает список названий команд, игнорируя служебную секцию адресов."""
        patterns = self._read_file(protocol_name)
        return [name for name in patterns.keys() if name != "__service_address__"]

    def load_service_addresses(self, protocol_name: str) -> dict:
        """Вычитывает сохраненную из файла служебную адресацию шины."""
        patterns = self._read_file(protocol_name)
        service_data = patterns.get("__service_address__", {})

        if service_data:
            return service_data

        if protocol_name == "Gels":
            return {"dst": "CA", "src": "17"}
        else:
            return {"dst": "8A", "src": "0A"}

    def save_service_addresses(self, protocol_name: str, dst_hex: str, src_hex: str):
        """Физически перезаписывает служебную секцию адресов в JSON файле."""
        if not protocol_name:
            return

        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        patterns = self._read_file(protocol_name)
        patterns["__service_address__"] = {
            "dst": dst_hex.upper(),
            "src": src_hex.upper()
        }

        ordered_patterns = {"__service_address__": patterns["__service_address__"]}
        for k, v in patterns.items():
            if k != "__service_address__":
                ordered_patterns[k] = v

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ordered_patterns, f, ensure_ascii=False, indent=2)
            print(f"[CmdPatternsManager] Служебные адреса успешно сохранены для {protocol_name}")
        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка сохранения служебных адресов: {e}")

    def extract_pattern_data(self, protocol_name: str, pattern_name: str) -> dict:
        """
        Вычитывает сохраненную HEX-строку кадра и разбирает её на логические составляющие.
        ИСПРАВЛЕНО: Срез полезной нагрузки Gels переведен на индекс 5, исключая байты длины.
        """
        patterns = self._read_file(protocol_name)
        hex_string = patterns.get(pattern_name, "").replace(" ", "")

        result = {
            "dst_addr": 0x00,
            "src_addr": 0x00,
            "cmd_code": 0x00,
            "payload_bytes": b""
        }

        if not hex_string or pattern_name == "__service_address__":
            return result

        try:
            full_frame_bytes = bytes.fromhex(hex_string)
            if len(full_frame_bytes) < 5:
                return result

            # Первые два байта во всех протоколах — адресация
            result["dst_addr"] = int(full_frame_bytes[0])
            result["src_addr"] = int(full_frame_bytes[1])

            # Извлекаем код команды и полезную нагрузку в зависимости от протокола
            if protocol_name == "IDS":
                if len(full_frame_bytes) >= 6:
                    result["cmd_code"] = int(full_frame_bytes[4])
                    result["payload_bytes"] = full_frame_bytes[5:-1]

            elif protocol_name == "Aps":
                if len(full_frame_bytes) >= 7:
                    result["cmd_code"] = int(full_frame_bytes[4])
                    result["payload_bytes"] = full_frame_bytes[5:-2]

            elif protocol_name == "Gels":
                # Gels заголовок: DEV(1B) + MOD(1B) + CMD(1B) + SIZE(2B)
                if len(full_frame_bytes) >= 7:
                    result["cmd_code"] = int(full_frame_bytes[2])  # Код команды лежит в 3-м байте (индекс 2)
                    # ИСПРАВЛЕНО: Payload начинается строго с 6-го байта (индекс 5), пропуская 2 байта размера
                    result["payload_bytes"] = full_frame_bytes[5:-2]

        except Exception as e:
            print(f"[CmdPatternsManager] Ошибка бинарного разбора кадра шаблона {protocol_name}: {e}")

        return result

    def save_pattern(self, protocol_name: str, pattern_name: str, raw_packet: bytes) -> bool:
        """Физически сериализует байты готовой посылки в JSON-файл."""
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

    def _read_file(self, protocol_name: str) -> dict:
        """Внутренний вспомогательный метод безопасного чтения файла с диска."""
        if not protocol_name:
            return {}
        file_name = f"{protocol_name}CmdPatterns.json"
        file_path = self.config_dir / file_name

        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {}