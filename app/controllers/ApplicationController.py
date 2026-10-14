import struct
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from app.models.ConfigManager import ConfigManager
from app.models.CmdPatternsManager import CmdPatternsManager
from app.models.protocols.IdsProtocol import IdsProtocol
from app.models.protocols.GelsProtocol import GelsProtocol
from app.models.protocols.ApsProtocol import ApsProtocol
from app.views.MainWindow import MainWindow
from app.views.SaveCmdPatternView import SaveCmdPatternView
from app.controllers.ComPortController import ComPortController
from app.controllers.IdsPanelController import IdsPanelController
from app.controllers.PortLoggerController import PortLoggerController
from app.controllers.SendCmdController import SendCmdController
from app.controllers.SaveCmdPatternController import SaveCmdPatternController


class ApplicationController(QObject):
    """
    Корневой оркестратор приложения (Root MVC Controller).
    Координирует межмодульную телеметрию, логирование и ручную/автоматическую отправку команд.
    """
    data_parsed_signal = pyqtSignal(dict)

    def __init__(self, config_manager: ConfigManager, main_window: MainWindow):
        super().__init__()
        self.config_manager = config_manager
        self.main_window = main_window

        self.rx_buffer = bytearray()

        self.com_port_controller = ComPortController(
            config_manager=self.config_manager,
            view=self.main_window.com_port_view
        )
        self.port_logger_controller = PortLoggerController(
            view=self.main_window.port_logger_view
        )
        self.send_cmd_controller = SendCmdController(
            view=self.main_window.send_cmd_view
        )
        self.send_cmd_controller.on_command_ready_to_dispatch = self.handle_manual_command_dispatch

        self.patterns_manager = CmdPatternsManager()
        self.send_cmd_controller.save_pattern_requested.connect(self.process_pattern_save_request)

        self.ids_panel_controller: Optional[IdsPanelController] = None
        self.ids_protocol_instance: Optional[IdsProtocol] = None
        self.gels_protocol_instance: Optional[GelsProtocol] = None
        self.aps_protocol_instance: Optional[ApsProtocol] = None

        self.com_port_controller.on_session_started = self.handle_session_start
        self.com_port_controller.on_session_stopped = self.handle_session_stop
        self.com_port_controller.model.data_received.connect(self.handle_incoming_bytes)

    def handle_session_start(self, protocol_name: str):
        """Вызывается при успешном открытии физического COM-порта."""
        self.rx_buffer.clear()
        self.port_logger_controller.write_log("sys", f"--- Физический канал связи успешно открыт [{protocol_name}] ---")
        self.send_cmd_controller.configure_for_protocol(protocol_name)

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

            # ИСПРАВЛЕНО: Подключаем обработчик сохранения шаблона из панели IDS
            self.ids_panel_controller.save_pattern_requested_signal.connect(self.process_ids_panel_pattern_save)

        elif protocol_name == "Gels":
            self.gels_protocol_instance = GelsProtocol()

        elif protocol_name == "Aps":
            self.aps_protocol_instance = ApsProtocol()

    def handle_session_stop(self):
        """Вызывается при закрытии физического COM-порта."""
        self.main_window.send_cmd_view.set_addresses_container_visible(False)
        self.main_window.send_cmd_view.set_radio_layout_visible(False)

        try:
            self.data_parsed_signal.disconnect()
        except TypeError:
            pass

        if self.ids_panel_controller:
            try:
                self.ids_panel_controller.send_request_signal.disconnect(self.execute_ids_data_query)
                self.ids_panel_controller.save_pattern_requested_signal.disconnect(self.process_ids_panel_pattern_save)
            except TypeError:
                pass

        self.ids_panel_controller = None
        self.ids_protocol_instance = None
        self.gels_protocol_instance = None
        self.aps_protocol_instance = None
        self.rx_buffer.clear()
        self.main_window.show_default_left_interface()
        self.port_logger_controller.write_log("sys", "--- Физический канал связи закрыт пользователем ---")

    @pyqtSlot(bytes)
    def handle_incoming_bytes(self, raw_bytes: bytes):
        if not raw_bytes:
            return
        active_proto = self.com_port_controller.active_protocol_name
        if active_proto not in ["IDS", "Gels", "Aps"]:
            self.port_logger_controller.write_log("in", raw_bytes.hex(" ").upper())
            return
        self.rx_buffer.extend(raw_bytes)

        if active_proto == "IDS" and self.ids_protocol_instance:
            while True:
                frame = self.ids_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None:
                    break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())
                if not frame.get("is_valid", False):
                    continue
                payload_bytes = frame.get("payload", b"")
                parsed_data = self.ids_protocol_instance.parse_dynamic_payload(payload_bytes)
                if parsed_data:
                    self.data_parsed_signal.emit(parsed_data)

        elif active_proto == "Gels" and self.gels_protocol_instance:
            while True:
                frame = self.gels_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None:
                    break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())

        elif active_proto == "Aps" and self.aps_protocol_instance:
            while True:
                frame = self.aps_protocol_instance.parse_stream(self.rx_buffer)
                if frame is None:
                    break
                raw_packet = frame.get("raw_packet", b"")
                if raw_packet:
                    direction = "in" if frame.get("is_valid", False) else "err"
                    self.port_logger_controller.write_log(direction, raw_packet.hex(" ").upper())

    def handle_manual_command_dispatch(self, dst_addr: int, src_addr: int, command_code: int, payload: bytes):
        if not self.com_port_controller.model.is_connected():
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return
        if self.com_port_controller.active_protocol_name == "IDS" and self.ids_protocol_instance:
            full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Gels" and self.gels_protocol_instance:
            full_packet = self.gels_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Aps" and self.aps_protocol_instance:
            full_packet = self.aps_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        else:
            full_packet = struct.pack("BB", dst_addr, src_addr) + payload
        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    def process_pattern_save_request(self, command_code: int, payload: bytes):
        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr = int(addrs["dst"], 16)
            src_addr = int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00

        if self.com_port_controller.active_protocol_name == "IDS" and self.ids_protocol_instance:
            full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Gels" and self.gels_protocol_instance:
            full_packet = self.gels_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        elif self.com_port_controller.active_protocol_name == "Aps":
            if self.aps_protocol_instance:
                full_packet = self.aps_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
            else:
                tmp_aps = ApsProtocol()
                full_packet = tmp_aps.pack_message(dst_addr, src_addr, command_code, payload)
        else:
            full_packet = struct.pack("BB", dst_addr, src_addr) + payload

        packet_hex_string = full_packet.hex(" ").upper()
        save_view = SaveCmdPatternView(formatted_packet_hex=packet_hex_string, parent=self.main_window)
        save_controller = SaveCmdPatternController(view=save_view, patterns_manager=self.patterns_manager)
        proto_name = self.com_port_controller.active_protocol_name
        if save_controller.execute_save(proto_name, full_packet):
            self.send_cmd_controller.configure_for_protocol(proto_name)

    # ИСПРАВЛЕНО: Новый метод формирования кодограммы 0x11 БЕЗ отправки в порт и вызова диалога сохранения
    def process_ids_panel_pattern_save(self, selected_ids: list):
        """Собирает бинарный пакет на основе выбранных в IdsPanelView чекбоксов и открывает окно сохранения шаблонов."""
        if not self.ids_protocol_instance:
            return

        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr = int(addrs["dst"], 16)
            src_addr = int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00

        # Формируем бинарный Payload команды 0x11 (ReadData)
        payload = bytearray()
        payload.append(len(selected_ids))
        for param_id in selected_ids:
            payload.append(param_id)

        command_code = 0x11

        # Собираем легитимный пакет по правилам IDS SBus протокола
        full_packet = self.ids_protocol_instance.pack_message(
            dst_addr=dst_addr, src_addr=src_addr, cmd=command_code, payload=bytes(payload)
        )
        packet_hex_string = full_packet.hex(" ").upper()

        # Разворачиваем модальное окно сохранения шаблонов
        save_view = SaveCmdPatternView(formatted_packet_hex=packet_hex_string, parent=self.main_window)
        save_controller = SaveCmdPatternController(view=save_view, patterns_manager=self.patterns_manager)

        proto_name = self.com_port_controller.active_protocol_name
        if save_controller.execute_save(proto_name, full_packet):
            # Обновляем комбобокс в SendCmdController, чтобы новый шаблон сразу там появился
            self.send_cmd_controller.configure_for_protocol(proto_name)

    def execute_ids_data_query(self, selected_ids: list):
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return
        if not selected_ids:
            return
        addrs = self.main_window.send_cmd_view.get_addresses_values()
        try:
            dst_addr = int(addrs["dst"], 16)
            src_addr = int(addrs["src"], 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00

        payload = bytearray()
        payload.append(len(selected_ids))
        for param_id in selected_ids:
            payload.append(param_id)

        command_code = 0x11
        full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, bytes(payload))
        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

