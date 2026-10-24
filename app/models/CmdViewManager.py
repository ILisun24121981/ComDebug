# === ФАЙЛ: app/models/CmdViewManager.py ===
import json
import pathlib
import sys
import re


class CmdViewManager:
    """
    Модель управления картой соответствий команд и представлений (MVC Model).
    Изолированно работает с комплексными шаблонами в папке ViewMappings.
    """

    def __init__(self):
        # Автоматическое определение пути запуска (для отладки в IDE vs Сборка в EXE)
        if getattr(sys, 'frozen', False):
            base_dir = pathlib.Path(sys.executable).parent
        else:
            base_dir = pathlib.Path(".").resolve()

        # Гарантируем физическое наличие папки ViewMappings
        self.mappings_dir = base_dir / "ViewMappings"
        self.mappings_dir.mkdir(exist_ok=True)

        # Гарантируем физическое наличие папки ViewStructures в корне
        self.view_structs_dir = base_dir / "ViewStructures"
        self.view_structs_dir.mkdir(exist_ok=True)

    def _get_file_path(self, protocol_name: str) -> pathlib.Path:
        return self.mappings_dir / f"{protocol_name}CmdViewMappings.json"

    def load_available_view_structures(self) -> dict:
        """Сканирует папку ViewStructures и парсит JSON-файлы описания View."""
        available_structs = {}
        if not self.view_structs_dir.exists():
            return available_structs

        for file_path in self.view_structs_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                struct_name = file_path.stem
                size = data.get("Total_Size_Bytes", 0)
                fields = data.get("Fields", [])

                available_structs[struct_name] = {
                    "size": size,
                    "fields": fields
                }
            except Exception as e:
                print(f"[CmdViewManager] Ошибка парсинга структуры {file_path.name}: {e}")

        return available_structs

    def load_pattern_names(self, protocol_name: str) -> list[str]:
        """Возвращает список названий сохраненных комплексных конфигураций."""
        data = self._read_file(protocol_name)
        return list(data.keys())

    def load_pattern_config(self, protocol_name: str, name: str) -> dict:
        """Вычитывает конкретную конфигурацию маппингов по имени."""
        data = self._read_file(protocol_name)
        return data.get(name, {})

    def save_pattern(self, protocol_name: str, name: str, config: dict) -> bool:
        """Записывает комплексную конфигурацию маппингов на диск."""
        if not protocol_name or not name:
            return False
        data = self._read_file(protocol_name)
        data[name] = config
        return self._write_file(protocol_name, data)

    def delete_patterns(self, protocol_name: str, names: list[str]) -> bool:
        """Удаляет выбранные конфигурации маппингов из файла."""
        if not protocol_name or not names:
            return False
        data = self._read_file(protocol_name)
        for name in names:
            if name in data:
                del data[name]
        return self._write_file(protocol_name, data)

    def generate_next_default_name(self, protocol_name: str) -> str:
        """Автоматически вычисляет и возвращает следующее имя TempX по аналогии с автоопросом."""
        names = self.load_pattern_names(protocol_name)
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
        file_path = self._get_file_path(protocol_name)
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_file(self, protocol_name: str, data: dict) -> bool:
        file_path = self._get_file_path(protocol_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def generate_next_struct_default_name(self) -> str:
        """Сканирует папку ViewStructures и вычисляет следующее имя TempX по аналогии с шаблонами."""
        if not self.view_structs_dir.exists():
            return "Temp1"

        max_num = 0
        pattern = re.compile(r"^Temp(\d+)$", re.IGNORECASE)

        # Сканируем все JSON файлы в папке структур отображения
        for file_path in self.view_structs_dir.glob("*.json"):
            match = pattern.match(file_path.stem.strip())
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        if max_num == 0:
            return "Temp1"

        return f"Temp{max_num + 1}"

    def create_empty_structure_template(self, struct_name: str) -> tuple[bool, str]:
        """Физически создает новый файл-заготовку на диске с нативными типами данных языка Си."""
        if not struct_name:
            return False, "Имя структуры пустое"

        file_path = self.view_structs_dir / f"{struct_name}.json"
        if file_path.exists():
            return False, f"Файл {struct_name}.json уже существует!"

        # Генерируем наполнение файла с примерами типов данных ANSI C и произвольных битовых полей
        template_content = {
            "//_COMMENT_//": "ЗАПОЛНИТЕ СТРУКТУРУ ДАННЫМИ В ФОРМАТЕ УКАЗАННОМ В ПРИМЕРЕ (ТИПЫ ДАННЫХ С)",
            "Structure_Name": struct_name,
            "Total_Size_Bytes": 22,
            "Fields": [
                {"name": "status_flags", "type": "uint32_t", "description": "Беззнаковое 32-битное целое Си (4 байта)"},
                {"name": "temperature", "type": "int16_t", "description": "Знаковое 16-битное целое Си (2 байта)"},
                {"name": "param_float", "type": "float", "description": "Число с плавающей точкой Си (4 байта)"},
                {"name": "param_char", "type": "char", "description": "Символьный тип Си / знаковый байт (1 байт)"},
                {"name": "param_uint8", "type": "uint8_t", "description": "Беззнаковый байт Си (1 байт)"},

                {"name": "bitfield_stick", "type": "uint8_t:3",
                 "description": "Произвольное битовое поле (3 бита из общего uint8_t)"},
                {"name": "bitfield_slip", "type": "uint8_t:5",
                 "description": "Произвольное битовое поле (оставшиеся 5 бит из того же uint8_t)"},

                {"name": "custom_bit_1", "type": "uint16_t:4",
                 "description": "Произвольное битовое поле (4 бита из контейнера uint16_t)"},
                {"name": "custom_bit_2", "type": "uint16_t:12",
                 "description": "Произвольное битовое поле (12 бит, заполняющие контейнер uint16_t)"}
            ]
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(template_content, f, ensure_ascii=False, indent=2)

            import os
            import subprocess

            normalized_path = os.path.abspath(str(file_path))
            if os.name == 'nt':
                subprocess.Popen(f'explorer /select,"{normalized_path}"')
            else:
                subprocess.Popen(['xdg-open', os.path.dirname(normalized_path)])

            return True, str(file_path)
        except Exception as e:
            return False, str(e)