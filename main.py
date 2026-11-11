import sys
import pathlib
import traceback
import faulthandler
from PyQt6.QtWidgets import QApplication
from app.models.ConfigManager import ConfigManager
from app.views.MainWindow import MainWindow
from app.controllers.ApplicationController import ApplicationController

# Включаем низкоуровневый дамп стека при C++ сбоях
faulthandler.enable()

def global_exception_hook(exc_type, exc_value, exc_tb):
    print("\n" + "=" * 60, file=sys.stderr, flush=True)
    print("[CRITICAL PYTHON EXCEPTION IN QT SLOT]", file=sys.stderr, flush=True)
    traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr, flush=True)
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = global_exception_hook

def ensure_config_environment():
    """Гарантирует физическое наличие структуры папок конфигураций."""
    cfg_dir = pathlib.Path("./Config")
    cfg_dir.mkdir(exist_ok=True)

    # Минимальный шаблон для настроек портов, если файла нет на диске
    port_file = cfg_dir / "port_settings.json"
    if not port_file.exists():
        with open(port_file, "w", encoding="utf-8") as f:
            f.write('{"protocols": {}}')


def main():
    # Проверяем рабочую среду конфигураций JSON перед стартом
    ensure_config_environment()

    # Инициализация системного движка PyQt6
    app = QApplication(sys.argv)

    # 1. Инициализируем центральную модель конфигураций (Model)
    config_manager = ConfigManager()

    # 2. Инициализируем главное окно (View Container)
    main_window = MainWindow()

    # 3. Запускаем корневой оркестратор, передавая ему Модель и Вид
    # Он автоматически соберет всю иерархию изолированных контроллеров
    root_controller = ApplicationController(
        config_manager=config_manager,
        main_window=main_window
    )

    # Отображаем главное окно оператора КНБК на экране
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
