from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from app.views.AutoPollingSettingView import AutoPollingSettingView


class AutoPollingController(QObject):
    """
    Контроллер управления автоматическим циклическим опросом КНБК (MVC Controller).
    Защищен от зависаний и крашей стека (0xC0000409) за счет асинхронного автомата шагов.
    """
    send_command_signal = pyqtSignal(str)

    def __init__(self, view, model, main_controller=None):
        super().__init__()
        self.view = view
        self.model = model
        self.main_controller = main_controller

        # Системные переменные состояния
        self.execution_queue = []
        self.current_index = 0
        self.is_running = False

        # Подключаем сигналы кнопок автоопроса из MainWindow
        self.view.auto_query_configure_requested.connect(self.handle_configure_execution)
        self.view.auto_query_start_requested.connect(self.handle_start_execution)
        self.view.auto_query_stop_requested.connect(self.handle_stop_execution)

    def handle_configure_execution(self):
        """Событие: Нажата кнопка 'Настроить'."""
        try:
            saved_patterns = [self.view.send_cmd_view.pattern_combobox.itemText(i)
                              for i in range(self.view.send_cmd_view.pattern_combobox.count())]
        except Exception:
            saved_patterns = []

        current_config = {
            "mode": self.model.current_mode,
            "global_interval_ms": self.model.global_interval_ms,
            "chain_delay_ms": self.model.chain_delay_ms,
            "patterns": self.model.patterns_config
        }

        dialog = AutoPollingSettingView(saved_patterns, current_config, parent=self.view)

        if dialog.exec() == AutoPollingSettingView.DialogCode.Accepted:
            new_config = dialog.get_user_configuration()
            self.model.update_configuration(
                mode=new_config["mode"],
                global_int=new_config["global_interval_ms"],
                chain_del=new_config["chain_delay_ms"],
                config=new_config["patterns"]
            )
            print("[AutoPollingController] Конфигурация КНБК обновлена.")

    def handle_start_execution(self):
        """Событие: Нажата кнопка 'Запустить'."""
        if self.is_running:
            return

        # Ленивая фоновая инициализация из моделей (без UI комбобокса)
        if not self.model.patterns_config and self.main_controller:
            try:
                proto_name = self.main_controller.com_port_controller.active_protocol_name
                saved_names = self.main_controller.patterns_manager.load_patterns_names(proto_name)

                default_config = {}
                for name in saved_names:
                    if name != "__service_address__":
                        default_config[name] = {"enabled": True, "interval_ms": self.model.global_interval_ms}

                self.model.update_configuration(
                    mode=self.model.current_mode,
                    global_int=self.model.global_interval_ms,
                    chain_del=self.model.chain_delay_ms,
                    config=default_config
                )
            except Exception as e:
                print(f"[AutoPollingController] Ошибка сбора шаблонов: {e}")

        self.execution_queue = self.model.get_active_polling_queue()

        if not self.execution_queue:
            self.view.send_cmd_view.show_error(
                "Предупреждение автоопроса",
                "В конфигурации автоопроса нет активных команд! Проверьте шаблоны или откройте 'Настроить'."
            )
            return

        self.is_running = True
        self.current_index = 0

        self.view.set_auto_polling_buttons_state(True)
        print("[AutoPollingController] Асинхронный автоопрос ЗАПУЩЕН.")

        # Стартуем строго через изолированный singleShot в очереди событий
        QTimer.singleShot(10, self._execute_current_step)

    def _execute_current_step(self):
        """Выполняет отправку текущей кодограммы без перезапуска внутренних циклов."""
        if not self.is_running or not self.execution_queue:
            return

        cmd_meta = self.execution_queue[self.current_index]
        pattern_name = cmd_meta["name"]

        # Генерируем сигнал отправки, который уйдет в ApplicationController
        self.send_command_signal.emit(pattern_name)

    def schedule_next_step(self):
        """Планирует следующий шаг. Вызывается только из ApplicationController, когда порт свободен!"""
        if not self.is_running or not self.execution_queue:
            return

        cmd_meta = self.execution_queue[self.current_index]
        next_delay = self.model.global_interval_ms
        mode = self.model.current_mode

        # Расчет сдвига индексов и задержек в зависимости от инженерного режима
        if mode == "fixed":
            next_delay = self.model.global_interval_ms
            self.current_index = (self.current_index + 1) % len(self.execution_queue)

        elif mode == "custom":
            next_delay = cmd_meta["interval_ms"]
            self.current_index = (self.current_index + 1) % len(self.execution_queue)

        elif mode == "chain":
            if self.current_index < len(self.execution_queue) - 1:
                next_delay = 100  # Минимальный зазор между ячейками внутри одной пачки
                self.current_index += 1
            else:
                next_delay = self.model.chain_delay_ms  # Большая пауза между сериями опроса
                self.current_index = 0

        # Планируем атомарный вызов следующего шага
        QTimer.singleShot(max(10, next_delay), self._execute_current_step)

    def handle_stop_execution(self):
        """Событие: Нажата кнопка 'Остановить'."""
        if not self.is_running:
            return

        self.is_running = False
        self.view.set_auto_polling_buttons_state(False)
        print("[AutoPollingController] Асинхронный автоопрос ОСТАНОВЛЕН.")
