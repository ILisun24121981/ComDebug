from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer


class IdsPanelController(QObject):
    """
    Контроллер для комплексной панели управления IDS (MVC).
    ИСПРАВЛЕНО: Добавлен сигнал проброса сохранения шаблонов в главный ApplicationController.
    """
    request_changed = pyqtSignal(int, bool)
    send_request_signal = pyqtSignal(list)
    # Сигнал для запроса сохранения шаблона на основе активных чекбоксов
    save_pattern_requested_signal = pyqtSignal(list)

    def __init__(self, view):
        super().__init__()
        self.view = view

        self.is_transaction_active = False

        self.view.query_requested.connect(self.handle_query_execution)
        # Связываем нажатие новой кнопки на форме с обработчиком контроллера
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

        self.is_transaction_active = True

        for param_id, cb in self.view.ids_checkboxes.items():
            if cb.isChecked():
                cb_text = cb.text()
                if " (0x" in cb_text:
                    param_name = cb_text.split(" (0x")[0].strip()
                    self.view.update_value(param_name, "...")

        self.view.set_interactive_state(False)
        self.view.set_session_status("Опрос прибора активен, ожидание ответа...", "#0056B3", font_bold=False)

        QTimer.singleShot(1500, self._handle_transaction_timeout)
        self.send_request_signal.emit(active_ids)

    def handle_pattern_save_execution(self):
        """Событие: Нажата кнопка 'Сохранить запрос'. Вычитывает чекбоксы и отправляет на сохранение."""
        active_ids = self.view.get_selected_param_ids()

        if not active_ids:
            self.view.set_session_status("Предупреждение: выберите параметры для сохранения!", "#D9534F", font_bold=True)
            return

        # Генерируем сигнал сохранения, передавая массив выбранных ID параметров вверх оркестратору
        self.save_pattern_requested_signal.emit(active_ids)

    def _handle_transaction_timeout(self):
        if self.is_transaction_active:
            self.is_transaction_active = False
            self.view.set_interactive_state(True)
            self.view.set_session_status("Предупреждение: таймаут ответа КНБК шины", "#D9534F", font_bold=True)

    @pyqtSlot(dict)
    def update_telemetry_data(self, parsed_data: dict):
        if not parsed_data:
            return

        self.is_transaction_active = False

        for param_name, value in parsed_data.items():
            val_to_display = value if isinstance(value, (tuple, list)) and len(value) > 0 else value
            if isinstance(val_to_display, bytes):
                try:
                    display_str = val_to_display.decode('utf-8', errors='ignore').strip()
                except Exception:
                    display_str = val_to_display.hex().upper()
            else:
                display_str = str(val_to_display)

            self.view.update_value(param_name.strip(), display_str)

        self.view.set_interactive_state(True)
        self.view.set_session_status("Данные телеметрии успешно обновлены", "#008000", font_bold=True)
