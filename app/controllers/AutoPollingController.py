# === ФАЙЛ: app/controllers/AutoPollingController.py (ЦЕЛИКОМ) ===
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from app.views.AutoPollingSettingView import AutoPollingSettingView
from app.models.AutoPollingPatternsManager import AutoPollingPatternsManager


class AutoPollingController(QObject):
    """
    Контроллер автоматического циклического опроса КНБК (MVC Engine).
    Обеспечивает асинхронный автомат шагов без переполнения стека Qt.
    """
    send_command_signal = pyqtSignal(str)

    def __init__(self, view, model, main_controller=None):
        super().__init__()
        self.view = view  # Ссылка на MainWindow
        self.model = model
        self.main_controller = main_controller
        self.auto_patterns_manager = AutoPollingPatternsManager()

        self.execution_queue = []
        self.current_index = 0
        self.is_running = False

        # ИСПРАВЛЕНО: Убраны привязки старых сигналов кнопок главного окна.
        # Все клики теперь делегируются через SetAutoPatternsController.

    def execute_polling_configuration_dialog(self) -> bool:
        """Открывает окно настройки и возвращает результат закрытия."""
        try:
            combo = self.view.send_cmd_view.pattern_combobox
            saved_patterns = [combo.itemText(i) for i in range(combo.count())]
        except Exception:
            saved_patterns = []

        current_config = {
            "mode": self.model.current_mode,
            "global_interval_ms": self.model.global_interval_ms,
            "chain_delay_ms": self.model.chain_delay_ms,
            "patterns": self.model.patterns_config
        }

        # Диалог привязан к MainWindow (self.view) для изоляции памяти
        dialog = AutoPollingSettingView(
            saved_patterns, current_config, parent=self.view
        )

        if dialog.exec() == AutoPollingSettingView.DialogCode.Accepted:
            new_config = dialog.get_user_configuration()
            self.model.update_configuration(
                mode=new_config["mode"],
                global_int=new_config["global_interval_ms"],
                chain_del=new_config["chain_delay_ms"],
                config=new_config["patterns"]
            )
            return True
        return False

    def handle_start_by_ui_context(self, is_saved_mode: bool):
        """Инициирует пуск фоновой сессии опроса."""
        if self.is_running:
            return

        self.execution_queue = self.model.get_active_polling_queue()

        if not self.execution_queue:
            self.view.send_cmd_view.show_error(
                "Предупреждение автоопроса",
                "В конфигурации нет активных команд! Настройте параметры."
            )
            return

        self.is_running = True
        self.current_index = 0

        # Транслируем запуск UI черезMainWindow в SetAutoPatternsView
        self.view.set_auto_polling_panel_running_state(True)
        print("[AutoPolling] Фоновый опрос запущен.")
        QTimer.singleShot(10, self._execute_current_step)

    def _execute_current_step(self):
        if not self.is_running or not self.execution_queue:
            return
        cmd_meta = self.execution_queue[self.current_index]
        self.send_command_signal.emit(cmd_meta["name"])

    def schedule_next_step(self):
        if not self.is_running or not self.execution_queue:
            return

        cmd_meta = self.execution_queue[self.current_index]
        next_delay = self.model.global_interval_ms
        mode = self.model.current_mode

        if mode == "fixed":
            next_delay = self.model.global_interval_ms
            self.current_index = (self.current_index + 1) % len(
                self.execution_queue
            )
        elif mode == "custom":
            next_delay = cmd_meta["interval_ms"]
            self.current_index = (self.current_index + 1) % len(
                self.execution_queue
            )
        elif mode == "chain":
            if self.current_index < len(self.execution_queue) - 1:
                next_delay = 100
                self.current_index += 1
            else:
                next_delay = self.model.chain_delay_ms
                self.current_index = 0

        QTimer.singleShot(max(10, next_delay), self._execute_current_step)

    def handle_stop_execution(self):
        """Вызывается при остановке или обрыве связи."""
        if not self.is_running:
            return
        self.is_running = False
        self.view.set_auto_polling_panel_running_state(False)
        print("[AutoPolling] Фоновый опрос КНБК остановлен.")
