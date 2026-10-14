import pathlib


class LogManager:
    """
    Модель управления файловыми журналами (MVC Model).
    Полностью изолирует физическую работу с файловой системой от графического интерфейса.
    """

    def __init__(self):
        # Автоматически резервируем директорию для логов, если потребуется локальное хранение
        self.logs_dir = pathlib.Path("./Logs")
        self.logs_dir.mkdir(exist_ok=True)

    def write_log_to_file(self, file_path_str: str, text_content: str) -> bool:
        """
        Физически перезаписывает или создает текстовый файл с переданным контентом.
        Возвращает True в случае успеха, иначе генерирует исключение для обработки выше.
        """
        if not file_path_str:
            return False

        file_path = pathlib.Path(file_path_str)

        # Гарантируем запись в кодировке UTF-8 для корректного сохранения кириллических спецсимволов
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        return True
