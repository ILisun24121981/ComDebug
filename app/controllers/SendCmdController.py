from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QDialog
from app.views.HexPayloadDialog import HexPayloadDialog
from app.models.CmdPatternsManager import CmdPatternsManager


class SendCmdController(QObject):
    """
    Контроллер ручной отправки и интеллектуального переключения шаблонов (MVC).
    Динамически скрывает горизонтальный ряд радиокнопок, если шаблоны на диске отсутствуют.
    """
    save_pattern_requested = pyqtSignal(int, bytes)

    def __init__(self, view):
        super().__init__()
        self.view = view

        self.patterns_manager = CmdPatternsManager()
        self.active_protocol = "Gels"

        self.current_cmd_code = 0x00
        self.current_payload_hex = ""
        self.current_payload_bytes = b""

        self.is_saved_mode_active = False
        self.on_command_ready_to_dispatch = None

        # Подключаем сигналы View к методам
        self.view.send_clicked.connect(self.process_manual_send)
        self.view.save_clicked.connect(self.process_manual_save_click)
        self.view.payload_requested.connect(self.open_payload_dialog)
        self.view.edit_payload_requested.connect(self.open_payload_dialog)

        self.view.mode_changed.connect(self.handle_mode_change)
        self.view.pattern_selected.connect(self.handle_pattern_selection)

        # Стартовое принудительное скрытие радиокнопок при запуске программы
        self.view.set_radio_layout_visible(False)
        self.view.radio_new.setChecked(True)
        self.handle_mode_change(False)

    def configure_for_protocol(self, protocol_name: str):
        """Вызывается внешним оркестратором при старте сессии."""
        self.active_protocol = protocol_name

        pattern_names = self.patterns_manager.load_patterns_names(protocol_name)

        self.view.pattern_combobox.blockSignals(True)
        self.view.populate_patterns(pattern_names)
        self.view.pattern_combobox.blockSignals(False)

        # ИСПРАВЛЕНО: Радиокнопки появляются ТОЛЬКО если есть хотя бы одна сохраненная команда
        if pattern_names:
            self.view.set_radio_layout_visible(True)  # Показываем весь горизонтальный лейаут
            self.view.radio_saved.setChecked(True)  # Выбираем "Сохраненная" по умолчанию
            self.handle_mode_change(True)
        else:
            self.view.set_radio_layout_visible(False)  # Начисто скрываем горизонтальный ряд радиокнопок
            self.view.radio_new.setChecked(True)  # Сбрасываем режим на "Новая"
            self.handle_mode_change(False)

    def handle_mode_change(self, is_saved_mode: bool):
        """Обрабатывает щелчок оператора по радиокнопкам."""
        self.is_saved_mode_active = is_saved_mode
        self.view.set_view_mode(is_saved_mode)

        if is_saved_mode:
            self.handle_pattern_selection(self.view.pattern_combobox.currentText())
        else:
            self.current_cmd_code = 0x00
            self.current_payload_hex = ""
            self.current_payload_bytes = b""
            self.view.update_payload_status(0)

    def handle_pattern_selection(self, pattern_name: str):
        """Обрабатывает выбор шаблона из выпадающего списка."""
        if not pattern_name:
            self.view.set_info_cmd_text("—")
            self.view.update_payload_status(0)
            return

        data = self.patterns_manager.extract_pattern_data(self.active_protocol, pattern_name)

        self.current_cmd_code = data["cmd_code"]
        self.current_payload_bytes = data["payload_bytes"]
        self.current_payload_hex = self.current_payload_bytes.hex(" ").upper() if self.current_payload_bytes else ""

        # Вычленяем байт команды из возвращаемой структуры кадра
        if isinstance(self.current_cmd_code, (bytes, bytearray)) and len(self.current_cmd_code) > 4:
            cmd_val = self.current_cmd_code[4]  # 5-й байт (индекс 4) — код команды в IDS SBus
        elif isinstance(self.current_cmd_code, int):
            cmd_val = self.current_cmd_code
        else:
            cmd_val = 0x00

        self.view.set_info_cmd_text(f"{cmd_val:02X}")
        self.view.update_payload_status(len(self.current_payload_bytes))

    def open_payload_dialog(self):
        """Открывает диалог редактирования прикрепленного payload."""
        dialog = HexPayloadDialog(initial_hex=self.current_payload_hex, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            raw_hex = dialog.get_hex_string()
            clean_hex = raw_hex.replace(" ", "")
            try:
                parsed_bytes = bytes.fromhex(clean_hex) if clean_hex else b""

                if parsed_bytes != self.current_payload_bytes:
                    self.current_payload_hex = raw_hex
                    self.current_payload_bytes = parsed_bytes
                    self.view.update_payload_status(len(parsed_bytes))

                    if self.is_saved_mode_active:
                        self.view.show_save_button(True)
            except ValueError:
                self.view.show_error("Ошибка формата", "Неверный формат HEX-данных.")

    def process_manual_send(self):
        if not self.is_saved_mode_active:
            cmd_str = self.view.get_cmd_value()
            if not cmd_str:
                self.view.show_error("Предупреждение", "Введите код команды.")
                return
            try:
                self.current_cmd_code = int(cmd_str, 16)
            except ValueError:
                self.view.show_error("Ошибка формата", "Вводите код строго в HEX.")
                return

        final_cmd = self.current_cmd_code if isinstance(self.current_cmd_code, int) else 0x00
        if isinstance(self.current_cmd_code, (bytes, bytearray)) and len(self.current_cmd_code) > 4:
            final_cmd = self.current_cmd_code[4]

        if self.on_command_ready_to_dispatch:
            self.on_command_ready_to_dispatch(final_cmd, self.current_payload_bytes)

            if not self.is_saved_mode_active:
                self.current_payload_hex = ""
                self.current_payload_bytes = b""
                self.view.update_payload_status(0)
            else:
                self.configure_for_protocol(self.active_protocol)

    def process_manual_save_click(self):
        if not self.is_saved_mode_active:
            cmd_str = self.view.get_cmd_value()
            if not cmd_str:
                self.view.show_error("Предупреждение", "Введите код команды.")
                return
            try:
                self.current_cmd_code = int(cmd_str, 16)
            except ValueError:
                self.view.show_error("Ошибка формата", "Вводите код строго в HEX.")
                return

        final_cmd = self.current_cmd_code if isinstance(self.current_cmd_code, int) else 0x00
        if isinstance(self.current_cmd_code, (bytes, bytearray)) and len(self.current_cmd_code) > 4:
            final_cmd = self.current_cmd_code[4]

        self.save_pattern_requested.emit(final_cmd, self.current_payload_bytes)