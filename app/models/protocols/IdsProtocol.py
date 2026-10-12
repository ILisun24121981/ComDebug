import struct
from typing import Optional, Dict, Any
# Импортируем базовый класс из текущего пакета протоколов
from app.models.protocols.IProtocol import IProtocol


class IdsProtocol(IProtocol):
    """
    Реализация промышленного протокола IDS (IdsSBus) на Python.
    Идентификаторы параметров загружаются динамически из файла IDS_ID.json.
    """
    HEAD_FORMAT = "<BBHB"
    HEAD_SIZE = 5
    TAIL_FORMAT = "<B"
    TAIL_SIZE = 1

    def __init__(self, id_names_map: Dict[int, str]):
        super().__init__()
        # Принимаем динамически загруженную карту идентификаторов из ConfigManager
        self.id_names = id_names_map

    @property
    def byte_order(self) -> str:
        return "<"  # Little-Endian для IDS

    @staticmethod
    def calc_checksum(data: bytes | bytearray) -> int:
        """Вычисляет контрольную сумму как простую сумму байт (uint8)."""
        return sum(data) & 0xFF

    def pack_message(self, dst_addr: int, src_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        """Формирует полный кадр IdsSBus с расчетом размера и CRC."""
        total_size = self.HEAD_SIZE + len(payload) + self.TAIL_SIZE
        head_bytes = struct.pack(self.HEAD_FORMAT, dst_addr, src_addr, total_size, cmd)
        full_body = head_bytes + payload

        crc = self.calc_checksum(full_body)
        return full_body + struct.pack(self.TAIL_FORMAT, crc)

    def parse_stream(self, rx_buffer: bytearray) -> Optional[dict]:
        """Вырезает из бинарного потока последовательного порта валидный кадр IDS."""
        if len(rx_buffer) < self.HEAD_SIZE:
            return None

        unpacked_head = struct.unpack(self.HEAD_FORMAT, rx_buffer[:self.HEAD_SIZE])
        total_size = unpacked_head[2]

        if total_size < (self.HEAD_SIZE + self.TAIL_SIZE):
            del rx_buffer[:1]  # Сдвигаем буфер на байт при рассинхронизации кадра
            return None

        if len(rx_buffer) < total_size:
            return None

        complete_packet = bytes(rx_buffer[:total_size])
        del rx_buffer[:total_size]

        received_crc = complete_packet[-self.TAIL_SIZE]
        calculated_crc = self.calc_checksum(complete_packet[:-self.TAIL_SIZE])

        if calculated_crc != received_crc:
            return {"is_valid": False, "error": "Ошибка КС IDS", "raw_packet": complete_packet}

        status_code = unpacked_head[3]
        return {
            "is_valid": True,
            "destinationAddress": unpacked_head[0],
            "sourceAddress": unpacked_head[1],
            "status_code": status_code,
            "payload": complete_packet[self.HEAD_SIZE:-self.TAIL_SIZE]
        }

    def parse_dynamic_payload(self, payload: bytes) -> Optional[dict]:
        """Парсит гибкий динамический ответ прибора IDS (uint32 значения)."""
        if len(payload) < 1:
            return None

        number_of_items = payload[0]
        expected_min_size = 1 + number_of_items + (number_of_items * 4)
        if len(payload) < expected_min_size:
            return None

        id_bytes = payload[1: 1 + number_of_items]
        data_bytes = payload[1 + number_of_items: 1 + number_of_items + (number_of_items * 4)]

        parsed_results = {}
        for i in range(number_of_items):
            param_id = id_bytes[i]
            val_offset = i * 4
            value_raw = struct.unpack("<I", data_bytes[val_offset: val_offset + 4])[0]

            param_name = self.id_names.get(param_id, f"UNKNOWN_ID_0x{param_id:02X}")
            parsed_results[param_name] = value_raw

        return parsed_results
