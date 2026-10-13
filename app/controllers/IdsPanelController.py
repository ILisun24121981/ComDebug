from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer


class IdsPanelController(QObject):
    """
    Контроллер для комплексной панели управления IDS (MVC).
    Полностью защищен от крэша (0xC0000409) за счет исправления вызова .strip() на списках.
    """
    request_changed = pyqtSignal(int, bool)
    send_request_signal = pyqtSignal(list)

    def __init__(self, view):
        super().__init__()
        self.view = view

        # Флаг состояния транзакции опроса (защищает от гонки сигналов)
        self.is_transaction_active = False

        self.view.query_requested.connect(self.handle_query_execution)
        self.view.param_toggled.connect(self._process_param_toggle)

    def _process_param_toggle(self, param_id: int, is_checked: bool):
        self.request_changed.emit(param_id, is_checked)

    def handle_query_execution(self):
        """Событие: Нажата кнопка 'Запрос данных'. Реализует защищенный транзакционный цикл опроса."""
        active_ids = self.view.get_selected_param_ids()

        if not active_ids:
            self.view.set_session_status("Предупреждение: выберите параметры КНБК!", "#D9534F", font_bold=True)
            return

        # Выставляем флаг активной транзакции
        self.is_transaction_active = True

        # Безопасно сбрасываем старые значения выбранных параметров в режим ожидания ответа
        for param_id, cb in self.view.ids_checkboxes.items():
            if cb.isChecked():
                cb_text = cb.text()  # Напр.: "INC (0x01)"
                if " (0x" in cb_text:
                    # ИСПРАВЛЕНО: Извлекаем строго 0-й элемент (str), а уже затем вызываем .strip()
                    param_name = cb_text.split(" (0x")[0].strip()
                    self.view.update_value(param_name, "...")

        # Блокируем элементы управления панели от случайных повторных кликов оператора
        self.view.set_interactive_state(False)
        self.view.set_session_status("Опрос прибора активен, ожидание ответа...", "#0056B3", font_bold=False)

        # Запускаем защитный таймаут-таймер на 1.5 секунды.
        QTimer.singleShot(1500, self._handle_transaction_timeout)

        # Генерируем сигнал с массивом ID для физической отправки пакета в порт оркестратором
        self.send_request_signal.emit(active_ids)

    def _handle_transaction_timeout(self):
        """Внутренний слот таймаута: безопасно восстанавливает интерактивность интерфейса, если нет ответа."""
        if self.is_transaction_active:
            self.is_transaction_active = False
            self.view.set_interactive_state(True)
            self.view.set_session_status("Предупреждение: таймаут ответа КНБК шины", "#D9534F", font_bold=True)

    @pyqtSlot(dict)
    def update_telemetry_data(self, parsed_data: dict):
        """Слот: Принимает бинарный ответ от КНБК, пишет физические величины и снимает блокировку."""
        if not parsed_data:
            return

        # Сбрасываем флаг транзакции, так как ответ успешно получен до истечения таймаута
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

            # Обновляем текстовое поле результата конкретного забойного параметра
            self.view.update_value(param_name.strip(), display_str)

        # Снимаем блокировку с элементов управления GUI
        self.view.set_interactive_state(True)
        self.view.set_session_status("Данные телеметрии успешно обновлены", "#008000", font_bold=True)