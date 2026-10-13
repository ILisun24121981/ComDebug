from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class IdsParametersController(QObject):
    """
    Изолированный контроллер для управления виджетом параметров IDS (MVC).
    Монументально стабилен за счет отсутствия промежуточных триггеров на чекбоксах.
    """
    send_request_signal = pyqtSignal(list)

    def __init__(self, view):
        super().__init__()
        self.view = view

        # Подключаем только сигнал клика по кнопке "Запрос данных"
        self.view.query_requested.connect(self.handle_query_execution)

    def handle_query_execution(self):
        """Событие: Нажата кнопка 'Запрос данных'. Безопасно вычитывает выбранные ID параметров."""
        active_ids = self.view.get_selected_param_ids()

        # Передаем список выбранных ID параметров на уровень вверх в ApplicationController
        self.send_request_signal.emit(active_ids)

    @pyqtSlot(dict)
    def update_telemetry_data(self, parsed_data: dict):
        """Принимает словарь забойных параметров и транслирует в поля результатов."""
        if not parsed_data:
            return

        for param_name, value in parsed_data.items():
            if isinstance(value, (tuple, list)) and len(value) > 0:
                val_to_display = value
            else:
                val_to_display = value

            if isinstance(val_to_display, bytes):
                try:
                    display_str = val_to_display.decode('utf-8', errors='ignore').strip()
                except Exception:
                    display_str = val_to_display.hex().upper()
            else:
                display_str = str(val_to_display)

            self.view.update_value(param_name, display_str)
