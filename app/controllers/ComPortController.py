from app.models.ConfigManager import ConfigManager
from app.models.ComPortModel import ComPortModel
from app.views.ComPortView import ComPortView


class ComPortController:
    """
    Контроллер последовательного интерфейса (PyQt6).
    Координирует низкоуровневую сессию связи и динамически перенастраивает
    физические параметры порта на основе выбранного протокола.
    """

    def __init__(self, config_manager: ConfigManager, view: ComPortView):
        self.config_manager = config_manager
        self.view = view

        # Инициализируем один независимый экземпляр модели физического порта
        self.model = ComPortModel()
        self.active_protocol_name = "Gels"

        # Сигналы-колбэки для уведомления главного ApplicationController
        self.on_session_started = None  # Вызывается при успешном открытии порта
        self.on_session_stopped = None  # Вызывается при закрытии порта

        # Привязываем сигналы от графической формы к методам контроллера
        self.view.on_refresh_clicked = self.handle_refresh
        self.view.on_connect_toggle_clicked = self.handle_connect_toggle
        self.view.on_protocol_changed_callback = self.handle_protocol_change

        # Выполняем стартовую инициализацию параметров
        self.handle_protocol_change("Gels")
        self.handle_refresh()

    def handle_refresh(self):
        """Сканирует операционную систему и выводит список реальных COM-портов."""
        available_ports = self.model.get_available_ports()
        self.view.update_ports_list(available_ports)

    def handle_connect_toggle(self, port_name: str):
        """Управляет открытием и закрытием физического канала связи."""
        if self.model.is_connected():
            self.model.close_port()
            self.view.set_connected_state(False)
            print(f"[ComPortController] Порт {port_name} успешно закрыт.")

            # Оповещаем главный контроллер о завершении сессии связи
            if self.on_session_stopped:
                self.on_session_stopped()
        else:
            if not port_name or port_name == "Нет портов":
                self.view.show_error("Ошибка", "Выберите валидный COM-порт для работы.")
                return

            s = self.config_manager.get_port_settings(self.active_protocol_name)

            try:
                # Физически открываем дескриптор порта на шине данных
                if self.model.open_port(
                        port_name=port_name,
                        baud_rate=s.get("baud_rate", 9600),
                        bytesize=s.get("bytesize", 8),
                        parity=s.get("parity", "None"),
                        stopbits=s.get("stopbits", 1.0),
                        flow_control=s.get("flow_control", "None")
                ):
                    self.view.set_connected_state(True)
                    print(f"[ComPortController] Порт {port_name} успешно открыт.")

                    # Оповещаем главный контроллер об успешном запуске сессии связи
                    if self.on_session_started:
                        self.on_session_started(self.active_protocol_name)
            except Exception as err:
                self.view.show_error("Ошибка связи", f"Не удалось открыть порт {port_name}.\nДетали: {err}")

    def handle_protocol_change(self, protocol_name: str):
        """Событие GUI: Пользователь выбрал другой протокол в выпадающем списке."""
        self.active_protocol_name = protocol_name
        settings = self.config_manager.get_port_settings(protocol_name)
        self.view.update_port_settings_display(settings)
        print(f"[ComPortController] Стратегия порта перенастроена под стандарт: {protocol_name}")
