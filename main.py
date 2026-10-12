import sys
import pathlib
from PyQt6.QtWidgets import QApplication
from app.models.ConfigManager import ConfigManager
from app.views.MainWindow import MainWindow
from app.controllers.ComPortController import ComPortController


def ensure_config_environment():
    """Гарантирует физическое наличие структуры папок конфигураций."""
    cfg_dir = pathlib.Path("./Config")
    cfg_dir.mkdir(exist_ok=True)

    port_file = cfg_dir / "port_settings.json"
    if not port_file.exists():
        with open(port_file, "w", encoding="utf-8") as f:
            f.write('{"protocols": {}}')


def main():
    ensure_config_environment()

    # Инициализация движка PyQt6
    app = QApplication(sys.argv)

    # 1. Создаем менеджер конфигураций (Model)
    config_manager = ConfigManager()

    # 2. Создаем главное окно, которое внутри себя уже содержит ComPortView (View)
    main_window = MainWindow()

    # 3. Соединяем слои через Контроллер, передавая ComPortView из главного окна
    controller = ComPortController(
        config_manager=config_manager,
        view=main_window.com_port_view
    )

    # Отображаем окно на экране
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
