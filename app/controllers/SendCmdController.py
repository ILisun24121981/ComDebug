from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QDialog
from app.views.HexPayloadDialog import HexPayloadDialog
from app.models.CmdPatternsManager import CmdPatternsManager


class SendCmdController(QObject):
    """
    Контроллер ручной отправки и интеллектуального переключения шаблонов (MVC).
    Полностью защищен от зацикливания C++ стека за счет физического disconnect/connect сигналов.
    """
    save_pattern_requested = pyqtSignal(int, bytes)

    def __init__(self, view):
        super().__init__()
        self.view = view

        self.patterns_manager = CmdPatternsManager()
        self.active_protocol = "Gels"
        self.loaded_service_addrs = {"dst": "", "src": ""}

        self.current_cmd_code = 0x00
        self.current_payload_hex = ""
        self.current_payload_bytes = b""

        self.is_saved_mode_active = False
        self.on_command_ready_to_dispatch = None

        # Первичное безопасное подключение сигналов интерфейса
        self._connect_view_signals()

        # Стартовая чистая инициализация дефолтного состояния
        self.view.blockSignals(True)
        self.view.set_radio_layout_visible(False)
        self.view.set_addresses_container_visible(False)
        self.view.radio_new.setChecked(True)
        self.view.set_view_mode(False)
        self.view.blockSignals(False)

    def _connect_view_signals(self):
        """Внутренний метод: связывает сигналы представления со слотами контроллера."""
        self.view.send_clicked.connect(self.process_manual_send)
        self.view.save_clicked.connect(self.process_manual_save_click)
        self.view.payload_requested.connect(self.open_payload_dialog)
        self.view.edit_payload_requested.connect(self.open_payload_dialog)
        self.view.mode_changed.connect(self.handle_mode_change)
        self.view.pattern_selected.connect(self.handle_pattern_selection)

    def _disconnect_view_signals(self):
        """Внутренний метод: полностью изолирует контроллер от ложных ивентов рендеринга."""
        try:
            self.view.send_clicked.disconnect(self.process_manual_send)
            self.view.save_clicked.disconnect(self.process_manual_save_click)
            self.view.payload_requested.disconnect(self.open_payload_dialog)
            self.view.edit_payload_requested.disconnect(self.open_payload_dialog)
            self.view.mode_changed.disconnect(self.handle_mode_change)
            self.view.pattern_selected.disconnect(self.handle_pattern_selection)
        except TypeError:
            pass

    def configure_for_protocol(self, protocol_name: str):
        """Вызывается внешним оркестратором сразу после нажатия кнопки 'Подключить'."""
        self.active_protocol = protocol_name

        # ИЗОЛИРУЕМ View на время тотальной перезаписи полей комбобокса и радиокнопок
        self._disconnect_view_signals()
        self.view.blockSignals(True)

        self.view.update_addresses_labels(protocol_name)
        self.view.set_addresses_container_visible(True)

        self.loaded_service_addrs = self.patterns_manager.load_service_addresses(protocol_name)
        self.view.set_addresses_values(self.loaded_service_addrs["dst"], self.loaded_service_addrs["src"])

        pattern_names = self.patterns_manager.load_patterns_names(protocol_name)
        self.view.populate_patterns(pattern_names)

        if pattern_names:
            self.view.set_radio_layout_visible(True)
            self.view.radio_saved.setChecked(True)
            self.is_saved_mode_active = True
            self.view.set_view_mode(True)

            # Возвращаем контроль над сигналами
            self.view.blockSignals(False)
            self._connect_view_signals()

            # Считываем параметры стартового выбранного шаблона
            self.handle_pattern_selection(self.view.pattern_combobox.currentText())
        else:
            self.view.set_radio_layout_visible(False)
            self.view.radio_new.setChecked(True)
            self.is_saved_mode_active = False
            self.view.set_view_mode(False)
            self.current_cmd_code = 0x00
            self.current_payload_hex = ""
            self.current_payload_bytes = b""
            self.view.update_payload_status(0)

            self.view.blockSignals(False)
            self._connect_view_signals()

    def handle_mode_change(self, is_saved_mode: bool):
        self.is_saved_mode_active = is_saved_mode
        self.view.set_view_mode(is_saved_mode)

        if is_saved_mode:
            self.handle_pattern_selection(self.view.pattern_combobox.currentText())
        else:
            self._disconnect_view_signals()
            self.view.blockSignals(True)
            self.view.set_addresses_values(self.loaded_service_addrs["dst"], self.loaded_service_addrs["src"])
            self.view.blockSignals(False)
            self._connect_view_signals()

            self.current_cmd_code = 0x00
            self.current_payload_hex = ""
            self.current_payload_bytes = b""
            self.view.update_payload_status(0)

    def handle_pattern_selection(self, pattern_name: str):
        if not pattern_name:
            self.view.set_info_cmd_text("—")
            self.view.update_payload_status(0)
            return

        data = self.patterns_manager.extract_pattern_data(self.active_protocol, pattern_name)

        dst_hex_str = f"{data['dst_addr']:02X}"
        src_hex_str = f"{data['src_addr']:02X}"

        self._disconnect_view_signals()
        self.view.blockSignals(True)
        self.view.set_addresses_values(dst_hex_str, src_hex_str)
        self.view.blockSignals(False)
        self._connect_view_signals()

        raw_cmd = data["cmd_code"]
        if isinstance(raw_cmd, (bytes, bytearray)) and len(raw_cmd) >= 5:
            self.current_cmd_code = int(raw_cmd[2]) if self.active_protocol == "Gels" else int(raw_cmd[4])
        elif isinstance(raw_cmd, int):
            self.current_cmd_code = raw_cmd
        else:
            self.current_cmd_code = 0x00

        self.current_payload_bytes = data["payload_bytes"]
        self.current_payload_hex = self.current_payload_bytes.hex(" ").upper() if self.current_payload_bytes else ""

        self.view.set_info_cmd_text(f"{self.current_cmd_code:02X}")
        self.view.update_payload_status(len(self.current_payload_bytes))

    def open_payload_dialog(self):
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
        addrs = self.view.get_addresses_values()
        dst_str = addrs["dst"].strip().upper()
        src_str = addrs["src"].strip().upper()

        try:
            dst_addr = int(dst_str, 16)
            src_addr = int(src_str, 16)
        except ValueError:
            self.view.show_error("Ошибка формата", "Адреса должны быть в HEX формате.")
            return

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

            if dst_str != self.loaded_service_addrs["dst"] or src_str != self.loaded_service_addrs["src"]:
                self.patterns_manager.save_service_addresses(self.active_protocol, dst_str, src_str)
                self.loaded_service_addrs = {"dst": dst_str, "src": src_str}

        final_cmd = int(self.current_cmd_code)

        if self.on_command_ready_to_dispatch:
            self.on_command_ready_to_dispatch(dst_addr, src_addr, final_cmd, self.current_payload_bytes)

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

        final_cmd = int(self.current_cmd_code)
        self.save_pattern_requested.emit(final_cmd, self.current_payload_bytes)