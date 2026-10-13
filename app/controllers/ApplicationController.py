import struct
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from app.models.ConfigManager import ConfigManager
from app.models.CmdPatternsManager import CmdPatternsManager
from app.models.protocols.IdsProtocol import IdsProtocol
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
    data_parsed_signal = pyqtSignal(dict)  # Сигнал для безопасной межпотоковой передачи словарей

    def __init__(self, config_manager: ConfigManager, main_window: MainWindow):
        super().__init__()
        self.config_manager = config_manager
        self.main_window = main_window

        # Накапливаемый буфер байт для потоковой сборки кадров
        self.rx_buffer = bytearray()

        # Инициализируем дочерние контроллеры постоянного присутствия
        self.com_port_controller = ComPortController(
            config_manager=self.config_manager,
            view=self.main_window.com_port_view
        )

        self.port_logger_controller = PortLoggerController(
            view=self.main_window.port_logger_view
        )

        # Сквозной контроллер ручной отправки (активен всегда)
        self.send_cmd_controller = SendCmdController(
            view=self.main_window.send_cmd_view
        )
        self.send_cmd_controller.on_command_ready_to_dispatch = self.handle_manual_command_dispatch

        # Инициализируем синглтон-менеджер сохранения файлов шаблонов на диске
        self.patterns_manager = CmdPatternsManager()

        # Подключаем сигнал запроса на сохранение шаблона посылки от SendCmdController
        self.send_cmd_controller.save_pattern_requested.connect(self.process_pattern_save_request)

        # Ссылка на динамический контроллер комплексной панели IDS
        self.ids_panel_controller: Optional[IdsPanelController] = None
        self.ids_protocol_instance: Optional[IdsProtocol] = None

        # Привязываем обработчики сессий связи
        self.com_port_controller.on_session_started = self.handle_session_start
        self.com_port_controller.on_session_stopped = self.handle_session_stop

        # Связываем потоковый сигнал из модели порта со слотом обработки в реальном времени
        self.com_port_controller.model.data_received.connect(self.handle_incoming_bytes)

    def handle_session_start(self, protocol_name: str):
        """Вызывается при успешном открытии физического COM-порта."""
        self.rx_buffer.clear()
        self.port_logger_controller.write_log("sys", f"--- Физический канал связи успешно открыт [{protocol_name}] ---")

        # Приказываем дочернему SendCmdController настроить радиокнопки и загрузить шаблоны для выбранного протокола
        self.send_cmd_controller.configure_for_protocol(protocol_name)

        if protocol_name == "IDS":
            ids_map = self.config_manager.load_ids_identifiers()
            self.main_window.show_ids_interface(ids_map)

            self.ids_protocol_instance = IdsProtocol(ids_map)

            # Создаем комплексный контроллер панели управления IDS
            self.ids_panel_controller = IdsPanelController(
                view=self.main_window.ids_panel_view
            )

            # Связываем сигналы панели IDS с оркестратором
            self.data_parsed_signal.connect(self.ids_panel_controller.update_telemetry_data)
            self.ids_panel_controller.send_request_signal.connect(self.execute_ids_data_query)

    def handle_session_stop(self):
        """Вызывается при закрытии физического COM-порта."""
        try:
            if self.ids_panel_controller:
                self.data_parsed_signal.disconnect(self.ids_panel_controller.update_telemetry_data)
                self.ids_panel_controller.send_request_signal.disconnect(self.execute_ids_data_query)
        except Exception:
            pass

        self.ids_panel_controller = None
        self.ids_protocol_instance = None
        self.rx_buffer.clear()
        self.main_window.show_default_left_interface()
        self.port_logger_controller.write_log("sys", "--- Физический канал связи закрыт пользователем ---")

    @pyqtSlot(bytes)
    def handle_incoming_bytes(self, raw_bytes: bytes):
        """
        Потокобезопасный слот: выполняется строго в главном GUI-потоке.
        Мгновенно выводит любые пришедшие байты (включая мусор) на экран в реал-тайме.
        """
        if not raw_bytes:
            return

        # Любой мусор или системные байты сразу отображаются зеленым цветом в логгере
        self.port_logger_controller.write_log("in", raw_bytes.hex(" ").upper())

        if self.com_port_controller.active_protocol_name != "IDS" or not self.ids_protocol_instance:
            return

        # Накапливаем байты для сборки кадров протокола IDS
        self.rx_buffer.extend(raw_bytes)

        while True:
            frame = self.ids_protocol_instance.parse_stream(self.rx_buffer)
            if frame is None:
                break

            if not frame.get("is_valid", False):
                continue

            payload_bytes = frame.get("payload", b"")
            parsed_data = self.ids_protocol_instance.parse_dynamic_payload(payload_bytes)
            if parsed_data:
                self.data_parsed_signal.emit(parsed_data)

    def handle_manual_command_dispatch(self, command_code: int, payload: bytes):
        """Принимает сигнал ручной отправки команды от SendCmdController."""
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return

        # Динамически считываем адреса прямо с развернутой комплексной панели управления IDS (если она активна)
        if self.main_window.ids_panel_view is not None:
            addrs = self.main_window.ids_panel_view.get_addresses()
            try:
                dst_addr = int(addrs["dst"], 16)
                src_addr = int(addrs["src"], 16)
            except ValueError:
                dst_addr, src_addr = 0x29, 0x00
        else:
            dst_addr, src_addr = 0x29, 0x00

        # Собираем кастомный бинарный кадр с полезной нагрузкой через IdsProtocol
        full_packet = self.ids_protocol_instance.pack_message(
            dst_addr=dst_addr, src_addr=src_addr, cmd=command_code, payload=payload
        )

        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    def process_pattern_save_request(self, command_code: int, payload: bytes):
        """Перехватывает запрос, собирает полный бинарный кадр и открывает модальное окно сохранения шаблонов."""
        if self.main_window.ids_panel_view is not None:
            addrs = self.main_window.ids_panel_view.get_addresses()
            try:
                dst_addr = int(addrs["dst"], 16)
                src_addr = int(addrs["src"], 16)
            except ValueError:
                dst_addr, src_addr = 0x29, 0x00
        else:
            dst_addr, src_addr = 0x29, 0x00

        if self.ids_protocol_instance:
            full_packet = self.ids_protocol_instance.pack_message(dst_addr, src_addr, command_code, payload)
        else:
            from app.models.protocols.IdsProtocol import IdsProtocol
            tmp_proto = IdsProtocol({})
            full_packet = tmp_proto.pack_message(dst_addr, src_addr, command_code, payload)

        packet_hex_string = full_packet.hex(" ").upper()

        # Инициализируем MVC-подсистему сохранения шаблона команды
        save_view = SaveCmdPatternView(formatted_packet_hex=packet_hex_string, parent=self.main_window)
        save_controller = SaveCmdPatternController(view=save_view, patterns_manager=self.patterns_manager)

        proto_name = self.com_port_controller.active_protocol_name
        if save_controller.execute_save(proto_name, full_packet):
            # Мгновенно обновляем список шаблонов и состояние радиокнопок на экране после успешной записи на диск
            self.send_cmd_controller.configure_for_protocol(proto_name)

    def execute_ids_data_query(self, selected_ids: list, addresses: dict):
        """Формирует кодограмму запроса 0x11 по протоколу IDS на основе сигналов от IdsPanelController."""
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return

        if not selected_ids:
            self.main_window.com_port_view.show_error("Предупреждение", "Выберите хотя бы один параметр для запроса.")
            return

        try:
            dst_addr = int(addresses.get("dst", "29"), 16)
            src_addr = int(addresses.get("src", "00"), 16)
        except ValueError:
            dst_addr, src_addr = 0x29, 0x00

        payload = bytearray()
        payload.append(len(selected_ids))  # NumberOfItems
        for param_id in selected_ids:
            payload.append(param_id)

        command_code = 0x11  # ReadData

        full_packet = self.ids_protocol_instance.pack_message(
            dst_addr=dst_addr, src_addr=src_addr, cmd=command_code, payload=bytes(payload)
        )

        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())