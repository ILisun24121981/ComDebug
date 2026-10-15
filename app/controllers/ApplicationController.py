# === ФАЙЛ: app/controllers/ApplicationController.py (ЧАСТЬ 1 ИЗ 3) ===
import struct
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, Qt
from app.models.ConfigManager import ConfigManager
from app.models.CmdPatternsManager import CmdPatternsManager
from app.models.protocols.IdsProtocol import IdsProtocol
from app.models.protocols.GelsProtocol import GelsProtocol
from app.models.protocols.ApsProtocol import ApsProtocol
from app.models.AutoPollingModel import AutoPollingModel
from app.controllers.AutoPollingController import AutoPollingController
from app.views.MainWindow import MainWindow
from app.views.SaveCmdPatternView import SaveCmdPatternView
from app.controllers.ComPortController import ComPortController
from app.controllers.IdsPanelController import IdsPanelController
from app.controllers.PortLoggerController import PortLoggerController
from app.controllers.SendCmdController import SendCmdController
from app.controllers.SaveCmdPatternController import SaveCmdPatternController


class ApplicationController(QObject):
    """Корневой оркестратор приложения (Root MVC Controller)."""
    data_parsed_signal = pyqtSignal(dict)

    def __init__(self, config_manager: ConfigManager, main_window: MainWindow):
        super().__init__()
        self.config_manager = config_manager
        self.main_window = main_window
        self.rx_buffer = bytearray()

        self.is_transaction_active = False
        self.current_transaction_id = 0

        self.global_timeout_timer = QTimer(self)
        self.global_timeout_timer.setSingleShot(True)
        self.global_timeout_timer.timeout.connect(
            self._handle_global_transaction_timeout_event
        )

        self.com_port_controller = ComPortController(
            config_manager=self.config_manager,
            view=self.main_window.com_port_view
        )
        self.port_logger_controller = PortLoggerController(
            view=self.main_window.port_logger_view
        )
        self.send_cmd_view = self.main_window.send_cmd_view
        self.send_cmd_controller = SendCmdController(view=self.send_cmd_view)
        self.send_cmd_controller.on_command_ready_to_dispatch = (
            self.handle_manual_command_dispatch
        )

        self.patterns_manager = CmdPatternsManager()
        self.send_cmd_controller.save_pattern_requested.connect(
            self.process_pattern_save_request
        )

        self.ids_panel_controller: Optional[IdsPanelController] = None
        self.ids_protocol_instance: Optional[IdsProtocol] = None
        self.gels_protocol_instance: Optional[GelsProtocol] = None
        self.aps_protocol_instance: Optional[ApsProtocol] = None

        self.auto_polling_model = AutoPollingModel()
        self.auto_polling_controller = AutoPollingController(
            view=self.main_window,
            model=self.auto_polling_model,
            main_controller=self
        )

        # Создаем и привязываем новый обособленный MVC контроллер панели автоопроса
        from app.controllers.SetAutoPatternsController import SetAutoPatternsController
        self.set_auto_patterns_controller = SetAutoPatternsController(
            view=self.main_window.auto_patterns_view,
            auto_polling_controller=self.auto_polling_controller
        )

        self.auto_polling_controller.send_command_signal.connect(
            self.handle_auto_polling_dispatch,
            Qt.ConnectionType.QueuedConnection
        )

        self.com_port_controller.on_session_started = self.handle_session_start
        self.com_port_controller.on_session_stopped = self.handle_session_stop

        self.com_port_controller.model.data_received.connect(self.handle_incoming_bytes)
        self.com_port_controller.model.error_occurred.connect(self.handle_hardware_connection_error)

    def handle_session_start(self, protocol_name: str):
        self.rx_buffer.clear()
        self.is_transaction_active = False
        self.current_transaction_id = 0
        self.port_logger_controller.write_log(
            "sys", f"--- Канал связи открыт [{protocol_name}] ---"
        )
        self.send_cmd_controller.configure_for_protocol(protocol_name)

        # Передаем имя активного прибора КНБК в контроллер автоопроса для загрузки списков
        self.set_auto_patterns_controller.configure_for_protocol(protocol_name)

        if protocol_name == "IDS":
            ids_map = self.config_manager.load_ids_identifiers()
            self.main_window.show_ids_interface(ids_map)
            try:
                self.data_parsed_signal.disconnect()
            except TypeError:
                pass
            self.ids_protocol_instance = IdsProtocol(ids_map)
            self.ids_panel_controller = IdsPanelController(view=self.main_window.ids_panel_view)
            self.data_parsed_signal.connect(self.ids_panel_controller.update_telemetry_data)
            self.ids_panel_controller.send_request_signal.connect(self.execute_ids_data_query)
            self.ids_panel_controller.save_pattern_requested_signal.connect(self.process_ids_panel_pattern_save)
        elif protocol_name == "Gels":
            self.gels_protocol_instance = GelsProtocol()
        elif protocol_name == "Aps":
            self.aps_protocol_instance = ApsProtocol()

# === ФАЙЛ: app/controllers/ApplicationController.py (ЧАСТЬ 2 ИЗ 3) ===

    def handle_session_stop(self):
        """Вызывается при штатном закрытии физического COM-порта пользователем."""
        self.auto_polling_controller.handle_stop_execution()
        self.global_timeout_timer.stop()

        self.main_window.send_cmd_view.set_addresses_container_visible(False)
        self.main_window.send_cmd_view.set_radio_layout_visible(False)

        try:
            self.data_parsed_signal.disconnect()
        except TypeError:
            pass

        if self.ids_panel_controller:
            try:
                self.ids_panel_controller.send_request_signal.disconnect(
                    self.execute_ids_data_query
                )
            except TypeError:
                pass
            try:
                self.ids_panel_controller.save_pattern_requested_signal.disconnect(
                    self.process_ids_panel_pattern_save
                )
            except TypeError:
                pass

            if self.ids_panel_controller.view:
                try:
                    self.ids_panel_controller.view.query_requested.disconnect()
                    self.ids_panel_controller.view.save_pattern_requested.disconnect()
                    self.ids_panel_controller.view.param_toggled.disconnect()
                except TypeError:
                    pass

        self.ids_panel_controller = None
        self.ids_protocol_instance = None
        self.gels_protocol_instance = None
        self.aps_protocol_instance = None
        self.rx_buffer.clear()
        self.is_transaction_active = False

        self.main_window.show_default_left_interface()
        self.port_logger_controller.write_log(
            "sys", "--- Физический канал связи закрыт пользователем ---"
        )

    @pyqtSlot(str)
    def handle_hardware_connection_error(self, reason_text: str):
        """Вызывается автоматически при критическом сбое порта (выдергивании USB)."""
        self.auto_polling_controller.handle_stop_execution()
        self.global_timeout_timer.stop()

        self.port_logger_controller.write_log(
            "err", f"КРИТИЧЕСКИЙ СБОЙ СВЯЗИ: {reason_text}".upper()
        )

        self.com_port_controller.view.set_connected_state(False)
        self.main_window.send_cmd_view.set_addresses_container_visible(False)
        self.main_window.send_cmd_view.set_radio_layout_visible(False)

        try:
            self.data_parsed_signal.disconnect()
        except TypeError:
            pass

        if self.ids_panel_controller:
            try:
                self.ids_panel_controller.send_request_signal.disconnect(
                    self.execute_ids_data_query
                )
            except TypeError:
                pass
            try:
                self.ids_panel_controller.save_pattern_requested_signal.disconnect(
                    self.process_ids_panel_pattern_save
                )
            except TypeError:
                pass

            if self.ids_panel_controller.view:
                try:
                    self.ids_panel_controller.view.query_requested.disconnect()
                    self.ids_panel_controller.view.save_pattern_requested.disconnect()
                    self.ids_panel_controller.view.param_toggled.disconnect()
                except TypeError:
                    pass

        self.ids_panel_controller = None
        self.ids_protocol_instance = None
        self.gels_protocol_instance = None
        self.aps_protocol_instance = None
        self.rx_buffer.clear()
        self.is_transaction_active = False

        self.main_window.show_default_left_interface()
        self.com_port_controller.model.close_port()

    def _start_global_timeout_timer(self):
        self.global_timeout_timer.stop()
        self.is_transaction_active = True
        self.current_transaction_id += 1
        self.global_timeout_timer.start(1500)

    def _handle_global_transaction_timeout_event(self):
        if self.is_transaction_active:
            self.is_transaction_active = False
            if self.ids_panel_controller:
                self.ids_panel_controller.view.set_interactive_state(True)
                self.ids_panel_controller.view.set_session_status(
                    "Таймаут ответа шины", "#D9534F", font_bold=True
                )
            self.port_logger_controller.write_log("err", "Таймаут ответа КНБК (1500 мс)")
            if self.auto_polling_controller.is_running:
                self.auto_polling_controller.schedule_next_step()

    @pyqtSlot(bytes)
    def handle_incoming_bytes(self, raw_bytes: bytes):
        if not raw_bytes: return
        active_proto = self.com_port_controller.active_protocol_name
        if active_proto not in ["IDS", "Gels", "Aps"]:
            self.port_logger_controller.write_log("in", raw_bytes.hex(" ").upper())
            return
        self.rx_buffer.extend(raw_bytes)

        if active_proto == "IDS" and self.ids_protocol_instance:
            while True:
                frame = self.ids_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None: break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())
                if not frame.get("is_valid", False): continue
                self.is_transaction_active = False
                self.global_timeout_timer.stop()
                payload_bytes = frame.get("payload", b"")
                parsed_data = self.ids_protocol_instance.parse_dynamic_payload(payload_bytes)
                if parsed_data: self.data_parsed_signal.emit(parsed_data)
                if self.auto_polling_controller.is_running:
                    self.auto_polling_controller.schedule_next_step()

        elif active_proto == "Gels" and self.gels_protocol_instance:
            while True:
                frame = self.gels_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None: break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())
                if frame.get("is_valid", False):
                    self.is_transaction_active = False
                    self.global_timeout_timer.stop()
                    if self.auto_polling_controller.is_running:
                        self.auto_polling_controller.schedule_next_step()

        elif active_proto == "Aps" and self.aps_protocol_instance:
            while True:
                frame = self.aps_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None: break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())
                if frame.get("is_valid", False):
                    self.is_transaction_active = False
                    self.global_timeout_timer.stop()
                    if self.auto_polling_controller.is_running:
                        self.auto_polling_controller.schedule_next_step()

    # === ФАЙЛ: app/controllers/ApplicationController.py (ЧАСТЬ 3 ИЗ 3) ===

    def handle_manual_command_dispatch(self, dst_addr: int, src_addr: int, command_code: int, payload: bytes):
        if not self.com_port_controller.model.is_connected():
            self.main_window.com_port_view.show_error("Ошибка", "Порт закрыт.")
            return
        if self.is_transaction_active:
            self.port_logger_controller.write_log("err", "ОТВЕТ НЕ ПОЛУЧЕН ДО ОТПРАВКИ СЛЕДУЮЩЕГО ЗАПРОСА")
            self.is_transaction_active = False
            self.global_timeout_timer.stop()

        if self.com_port_controller.active_protocol_name == "IDS" and self.ids_protocol_instance:
            full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Gels" and self.gels_protocol_instance:
            full_packet = self.gels_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Aps" and self.aps_protocol_instance:
            full_packet = self.aps_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        else:
            full_packet = struct.pack("BB", dst_addr, src_addr) + payload

        self._start_global_timeout_timer()
        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    def process_pattern_save_request(self, command_code: int, payload: bytes):
        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr, src_addr = int(addrs["dst"], 16), int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00
        proto = self.com_port_controller.active_protocol_name
        if proto == "IDS" and self.ids_protocol_instance:
            full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif proto == "Gels" and self.gels_protocol_instance:
            full_packet = self.gels_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif proto == "Aps":
            if self.aps_protocol_instance:
                full_packet = self.aps_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
            else:
                tmp_aps = ApsProtocol()
                full_packet = tmp_aps.pack_message(dst_addr, src_addr, command_code, payload)
        else:
            full_packet = struct.pack("BB", dst_addr, src_addr) + payload

        packet_hex_string = full_packet.hex(" ").upper()
        save_view = SaveCmdPatternView(formatted_packet_hex=packet_hex_string, parent=self.main_window)

        # Автоматически вычисляем и подставляем следующее Temp имя для пульта
        default_cmd_name = self.patterns_manager.generate_next_default_cmd_name(proto)
        save_view.name_input.setText(default_cmd_name)
        save_view.name_input.selectAll()

        save_controller = SaveCmdPatternController(view=save_view, patterns_manager=self.patterns_manager)
        if save_controller.execute_save(proto, full_packet):
            self.send_cmd_controller.configure_for_protocol(proto)

    def process_ids_panel_pattern_save(self, selected_ids: list):
        if not self.ids_protocol_instance: return
        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr, src_addr = int(addrs["dst"], 16), int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00
        payload = bytearray([len(selected_ids)])
        for param_id in selected_ids: payload.append(param_id)
        full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, 0x11, bytes(payload))
        save_view = SaveCmdPatternView(formatted_packet_hex=full_packet.hex(" ").upper(), parent=self.main_window)
        proto = self.com_port_controller.active_protocol_name

        # Подставляем инкрементируемый дефолт TempX при сохранении набора IDS-панели
        default_cmd_name = self.patterns_manager.generate_next_default_cmd_name(proto)
        save_view.name_input.setText(default_cmd_name)
        save_view.name_input.selectAll()

        save_controller = SaveCmdPatternController(view=save_view, patterns_manager=self.patterns_manager)
        if save_controller.execute_save(proto, full_packet):
            self.send_cmd_controller.configure_for_protocol(proto)

    def execute_ids_data_query(self, selected_ids: list):
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Порт закрыт.")
            return
        if not selected_ids: return
        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr, src_addr = int(addrs["dst"], 16), int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00
        payload = bytearray([len(selected_ids)])
        for param_id in selected_ids: payload.append(param_id)
        full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, 0x11, bytes(payload))
        if self.is_transaction_active:
            self.port_logger_controller.write_log("err", "ОТВЕТ НЕ ПОЛУЧЕН ДО ОТПРАВКИ СЛЕДУЮЩЕГО ЗАПРОСА")
            self.is_transaction_active = False
            self.global_timeout_timer.stop()
        self._start_global_timeout_timer()
        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    def send_saved_command_by_name(self, pattern_name: str):
        if not self.auto_polling_controller or not self.auto_polling_controller.is_running:
            return

        if not self.com_port_controller.model.is_connected():
            self.auto_polling_controller.handle_stop_execution()
            return
        proto_name = self.com_port_controller.active_protocol_name
        patterns = self.patterns_manager._read_file(proto_name)
        raw_data = patterns.get(pattern_name, "")
        if not raw_data: return
        if isinstance(raw_data, str):
            try:
                full_packet = bytes.fromhex(raw_data.replace(" ", ""))
            except ValueError:
                return
        elif isinstance(raw_data, (bytes, bytearray)):
            full_packet = bytes(raw_data)
        else:
            return

        if self.is_transaction_active:
            self.port_logger_controller.write_log("err", "ОТВЕТ НЕ ПОЛУЧЕН ДО ОТПРАВКИ СЛЕДУЮЩЕГО ЗАПРОСА")
            self.is_transaction_active = False
            self.global_timeout_timer.stop()
        self._start_global_timeout_timer()
        if self.com_port_controller.model.is_connected():
            self.com_port_controller.model.send_data(full_packet)
            self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    @pyqtSlot(str)
    def handle_auto_polling_dispatch(self, pattern_name: str):
        self.send_saved_command_by_name(pattern_name)
