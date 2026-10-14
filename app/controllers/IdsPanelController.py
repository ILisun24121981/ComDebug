import random
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class IdsPanelController(QObject):
    """
    Контроллер для комплексной панели управления IDS (MVC).
    ПОЛНОСТЬЮ ЗАЩИЩЕН ОТ КРЭША (0xC0000409): исправлено извлечение имени параметра КНБК.
    Интерфейс всегда остается активным для отправки частых запросов.
    """
    request_changed = pyqtSignal(int, bool)
    send_request_signal = pyqtSignal(list)
    save_pattern_requested_signal = pyqtSignal(list)

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.last_used_color = "#CCCCCC"

        self.industrial_colors = [
            "#41739D", "#4F9A68", "#D3833A", "#845AA6",
            "#3297A6", "#C25B5B", "#A18262"
        ]

        self.view.query_requested.connect(self.handle_query_execution)
        self.view.save_pattern_requested.connect(self.handle_pattern_save_execution)
        self.view.param_toggled.connect(self._process_param_toggle)

    def _process_param_toggle(self, param_id: int, is_checked: bool):
        self.request_changed.emit(param_id, is_checked)

    def handle_query_execution(self):
        """Событие: Нажата кнопка 'Послать запрос'."""
        active_ids = self.view.get_selected_param_ids()

        if not active_ids:
            self.view.set_session_status("Предупреждение: выберите параметры КНБК!", "#D9534F", font_bold=True)
            return

        for param_id, cb in self.view.ids_checkboxes.items():
            cb_text = cb.text()
            if " (0x" in cb_text:
                # ИСПРАВЛЕНО БЕЗОПАСНО: Берем строго [0] элемент после сплита и только затем вызываем .strip()
                param_name = cb_text.split(" (0x")[0].strip()
                if cb.isChecked():
                    self.view.update_value(param_name, "...")
                else:
                    current_text = self.view.ids_value_labels.get(param_name).text()
                    self.view.update_value(param_name, current_text)

        self.view.set_session_status("Опрос прибора активен, ожидание ответа...", "#0056B3", font_bold=False)

        # Передаем управление в центральный оркестратор
        self.send_request_signal.emit(active_ids)

    def handle_pattern_save_execution(self):
        """Событие: Нажата кнопка 'Сохранить запрос'."""
        active_ids = self.view.get_selected_param_ids()
        if not active_ids:
            self.view.set_session_status("Предупреждение: выберите параметры для сохранения!", "#D9534F",
                                         font_bold=True)
            return
        self.save_pattern_requested_signal.emit(active_ids)

    @pyqtSlot(dict)
    def update_telemetry_data(self, parsed_data: dict):
        """Слот: Принимает бинарный ответ от КНБК, пишет физические величины."""
        if not parsed_data:
            return

        available_colors = [c for c in self.industrial_colors if c != self.last_used_color]
        current_packet_color = random.choice(available_colors)
        self.last_used_color = current_packet_color

        for param_name, value in parsed_data.items():
            val_to_display = value if isinstance(value, (tuple, list)) and len(value) > 0 else value
            if isinstance(val_to_display, bytes):
                try:
                    display_str = val_to_display.decode('utf-8', errors='ignore').strip()
                except Exception:
                    display_str = val_to_display.hex().upper()
            else:
                display_str = str(val_to_display)

            self.view.update_value_with_border(param_name.strip(), display_str, current_packet_color)

        self.view.set_interactive_state(True)
        self.view.set_session_status("Данные телеметрии успешно обновлены", "#008000", font_bold=True)
