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
        """Вычитывает JSON и возвращает плоский список названий шаблонов для ComboBox."""
        patterns = self._read_file(protocol_name)
        return list(patterns.keys())

    def extract_pattern_data(self, protocol_name: str, pattern_name: str) -> dict:
        """
        Вычитывает сохраненную HEX-строку кадра и разбирает её на логические составляющие.
        Освобождает контроллер от низкоуровневой бинарной логики.
        """
        patterns = self._read_file(protocol_name)
        hex_string = patterns.get(pattern_name, "").replace(" ", "")

        result = {
            "cmd_code": 0x00,
            "payload_bytes": b""
        }

        if not hex_string:
            return result

        try:
            full_frame_bytes = bytes.fromhex(hex_string)

            # Извлекаем код команды и полезную нагрузку на основе структуры кадра протокола
            if protocol_name == "IDS":
                # IDS SBus: DST(1B) + SRC(1B) + SIZE(2B) + CMD(1B) + PAYLOAD + CRC(1B)
                if len(full_frame_bytes) >= 6:
                    # Сохраняем оригинальный байт команды (находится на 5-й позиции, индекс 4)
                    result["cmd_code"] = full_frame_bytes[4]
                    result["payload_bytes"] = full_frame_bytes[5:-1]
            elif protocol_name == "Aps":
                # APS: DST(1B) + SRC(1B) + SIZE(2B) + CMD(1B) + PAYLOAD + CRC(2B)
                if len(full_frame_bytes) >= 6:
                    result["cmd_code"] = full_frame_bytes[4]
                    result["payload_bytes"] = full_frame_bytes[5:-2]
            else:
                # Gels: DEV(1B) + MOD(1B) + CMD(1B) + SIZE(2B) + PAYLOAD + CRC(1B) + END(1B)
                if len(full_frame_bytes) >= 5:
                    result["cmd_code"] = full_frame_bytes[2]
                    result["payload_bytes"] = full_frame_bytes[5:-2]

        except Exception as e:
            print(f"[CmdPatternsManager] КРИТИЧЕСКАЯ ОШИБКА РАЗБОРА КАДРА ШАБЛОНА: {e}")

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
            print(f"[CmdPatternsManager] Шаблон '{pattern_name}' успешно сохранен в {file_name}")
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
            print(f"[CmdPatternsManager] Ошибка чтения {file_name}: {e}")
            return {}