from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class IdsPanelController(QObject):
    """
    Контроллер для комплексной панели управления IDS (MVC).
    Управляет адресацией, состояниями опроса и выводом телеметрии КНБК.
    """
    request_changed = pyqtSignal(int, bool)
    send_request_signal = pyqtSignal(list, dict)  # Передает список ID и словарь адресов {"dst": ..., "src": ...}

    def __init__(self, view):
        super().__init__()
        self.view = view

        # Подключаем сигналы панели IDS
        self.view.query_requested.connect(self.handle_query_execution)
        self.view.param_toggled.connect(self._process_param_toggle)

    def _process_param_toggle(self, param_id: int, is_checked: bool):
        self.request_changed.emit(param_id, is_checked)

    def handle_query_execution(self):
        """Событие: Нажата кнопка 'Запрос данных'. Собирает ID и активную адресацию шины."""
        active_ids = self.view.get_selected_param_ids()
        addresses = self.view.get_addresses()

        # Генерируем сигнал с полной конфигурацией запроса для ApplicationController
        self.send_request_signal.emit(active_ids, addresses)

    @pyqtSlot(dict)
    def update_telemetry_data(self, parsed_data: dict):
        """Принимает словарь забойных параметров и транслирует в поля результатов."""
        if not parsed_data:
            return

        for param_name, value in parsed_data.items():
            val_to_display = value[0] if isinstance(value, (tuple, list)) and len(value) > 0 else value
            if isinstance(val_to_display, bytes):
                try:
                    display_str = val_to_display.decode('utf-8', errors='ignore').strip()
                except Exception:
                    display_str = val_to_display.hex().upper()
            else:
                display_str = str(val_to_display)

            self.view.update_value(param_name, display_str)