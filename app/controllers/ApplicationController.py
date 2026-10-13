import struct
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from app.models.ConfigManager import ConfigManager
from app.models.protocols.IdsProtocol import IdsProtocol
from app.views.MainWindow import MainWindow
from app.controllers.ComPortController import ComPortController
from app.controllers.IdsParametersController import IdsParametersController
from app.controllers.PortLoggerController import PortLoggerController


class ApplicationController(QObject):
    """
    Корневой оркестратор приложения (Root MVC Controller).
    Управляет межпотоковой передачей данных и ручной диагностической отправкой команд.
    """
    data_parsed_signal = pyqtSignal(dict)

    def __init__(self, config_manager: ConfigManager, main_window: MainWindow):
        super().__init__()
        self.config_manager = config_manager
        self.main_window = main_window

        # Накапливаемый буфер байт для потоковой сборки кадров
        self.rx_buffer = bytearray()

        # Инициализируем дочерние контроллеры
        self.com_port_controller = ComPortController(
            config_manager=self.config_manager,
            view=self.main_window.com_port_view
        )

        self.port_logger_controller = PortLoggerController(
            view=self.main_window.port_logger_view
        )

        self.ids_params_controller: Optional[IdsParametersController] = None
        self.ids_protocol_instance: Optional[IdsProtocol] = None

        # Привязываем обработчики сессий связи
        self.com_port_connection = self.com_port_controller.on_session_started = self.handle_session_start
        self.com_port_controller.on_session_stopped = self.handle_session_stop

        # Связываем потоковый сигнал из модели порта со слотом обработки в реальном времени
        self.com_port_controller.model.data_received.connect(self.handle_incoming_bytes)

        # Связываем нажатие верхней кнопки диагностики с методом ручной отправки
        self.main_window.send_button.clicked.connect(self.execute_manual_hex_send)

    def handle_session_start(self, protocol_name: str):
        """Вызывается при успешном открытии физического COM-порта."""
        self.rx_buffer.clear()
        self.port_logger_controller.write_log("sys", f"--- Физический канал связи успешно открыт [{protocol_name}] ---")

        if protocol_name == "IDS":
            # ИСПРАВЛЕНО: Делаем панель настройки адресов КНБК видимой только для IDS
            self.main_window.addresses_widget.setVisible(True)

            ids_map = self.config_manager.load_ids_identifiers()
            self.main_window.show_ids_interface(ids_map)

            self.ids_protocol_instance = IdsProtocol(ids_map)
            self.ids_params_controller = IdsParametersController(
                view=self.main_window.ids_params_view
            )

            self.data_parsed_signal.connect(self.ids_params_controller.update_telemetry_data)
            self.ids_params_controller.send_request_signal.connect(self.execute_ids_data_query)

    def handle_session_stop(self):
        """Вызывается при закрытии физического COM-порта."""
        # ИСПРАВЛЕНО: Скрываем панель настройки адресов при отключении сессии связи
        self.main_window.addresses_widget.setVisible(False)

        try:
            if self.ids_params_controller:
                self.data_parsed_signal.disconnect(self.ids_params_controller.update_telemetry_data)
                self.ids_params_controller.send_request_signal.disconnect(self.execute_ids_data_query)
        except Exception:
            pass

        self.ids_params_controller = None
        self.ids_protocol_instance = None
        self.rx_buffer.clear()
        self.main_window.show_default_left_interface()
        self.port_logger_controller.write_log("sys", "--- Физический канал связи закрыт пользователем ---")

    @pyqtSlot(bytes)
    def handle_incoming_bytes(self, raw_bytes: bytes):
        """Мгновенно выводит любые пришедшие байты (включая мусор) на экран в реал-тайме."""
        if not raw_bytes:
            return

        self.port_logger_controller.write_log("in", raw_bytes.hex(" ").upper())

        if self.com_port_controller.active_protocol_name != "IDS" or not self.ids_protocol_instance:
            return

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

    def execute_manual_hex_send(self):
        """Парсит введенные HEX-значения адресов/команд и отправляет кастомный кадр IDS в порт."""
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return

        dst_str = self.main_window.dst_input.text().strip()
        src_str = self.main_window.src_input.text().strip()
        cmd_str = self.main_window.cmd_input.text().strip()

        if not dst_str or not src_str or not cmd_str:
            self.main_window.com_port_view.show_error("Предупреждение", "Заполните поля адресов и код команды.")
            return

        try:
            dst_addr = int(dst_str, 16)
            src_addr = int(src_str, 16)
            command_code = int(cmd_str, 16)
        except ValueError:
            self.main_window.com_port_view.show_error("Ошибка формата",
                                                      "Вводите значения строго в HEX формате (например: 29 или 00).")
            return

        full_packet = self.ids_protocol_instance.pack_message(
            dst_addr=dst_addr, src_addr=src_addr, cmd=command_code, payload=b""
        )

        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())

    def execute_ids_data_query(self, selected_ids: list):
        """Формирует кодограмму запроса 0x11 по протоколу IDS и отправляет в COM-порт."""
        if not self.com_port_controller.model.is_connected() or not self.ids_protocol_instance:
            self.main_window.com_port_view.show_error("Ошибка", "Передача невозможна: COM-порт закрыт.")
            return

        if not selected_ids:
            self.main_window.com_port_view.show_error("Предупреждение", "Выберите хотя бы один параметр для запроса.")
            return

        payload = bytearray()
        payload.append(len(selected_ids))  # NumberOfItems
        for param_id in selected_ids:
            payload.append(param_id)

        try:
            dst_addr = int(self.main_window.dst_input.text().strip(), 16)
            src_addr = int(self.main_window.src_input.text().strip(), 16)
        except ValueError:
            # ИСПРАВЛЕНО: Безопасный дефолт под новые адреса
            dst_addr, src_addr = 0x29, 0x00

        command_code = 0x11  # ReadData

        full_packet = self.ids_protocol_instance.pack_message(
            dst_addr=dst_addr, src_addr=src_addr, cmd=command_code, payload=bytes(payload)
        )

        self.com_port_controller.model.send_data(full_packet)
        self.port_logger_controller.write_log("out", full_packet.hex(" ").upper())
