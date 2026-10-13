import struct
from typing import Optional
from app.models.protocols.IProtocol import IProtocol


class IdsExecutionStatus:
    @classmethod
    def get_name(cls, val: int) -> str:
        mapping = {
            0x00: "ExecutionSuccess", 0x01: "ExecutionFailure",
            0x02: "ChecksumError", 0x04: "UndefinedCommand",
            0x08: "AccessDenied"
        }
        return mapping.get(val, f"UnknownStatus_0x{val:02X}")


class IdsProtocol(IProtocol):
    """Реализация промышленного протокола IDS SBus (Little-Endian)."""
    HEAD_FORMAT = "<BBHB"  # DST(1B) + SRC(1B) + TOTAL_SIZE(2B) + CMD/STATUS(1B)
    HEAD_SIZE = 5
    TAIL_FORMAT = "<B"  # CRC(1B)
    TAIL_SIZE = 1

    def __init__(self, identifiers_map: Optional[dict] = None):
        super().__init__()
        self.identifiers_map = identifiers_map if identifiers_map else {}

    @property
    def byte_order(self) -> str:
        return "<"

    @staticmethod
    def calc_checksum(data: bytes | bytearray) -> int:
        return sum(data) & 0xFF

    def pack_message(self, dst_addr: int, src_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        total_size = self.HEAD_SIZE + len(payload) + self.TAIL_SIZE
        head_bytes = struct.pack(self.HEAD_FORMAT, dst_addr, src_addr, total_size, cmd)
        packet_without_crc = head_bytes + payload
        crc = self.calc_checksum(packet_without_crc)
        return packet_without_crc + struct.pack(self.TAIL_FORMAT, crc)

    def parse_stream(self, rx_buffer: bytearray) -> Optional[dict]:
        if len(rx_buffer) < self.HEAD_SIZE:
            return None

        unpacked_head = struct.unpack(self.HEAD_FORMAT, rx_buffer[:self.HEAD_SIZE])
        total_size = unpacked_head[2]

        if total_size < (self.HEAD_SIZE + self.TAIL_SIZE):
            del rx_buffer[:1]
            return None

        if len(rx_buffer) < total_size:
            return None

        complete_packet = bytes(rx_buffer[:total_size])
        del rx_buffer[:total_size]

        received_crc = struct.unpack(self.TAIL_FORMAT, complete_packet[-self.TAIL_SIZE:])[0]
        calculated_crc = self.calc_checksum(complete_packet[:-self.TAIL_SIZE])

        if calculated_crc != received_crc:
            return {"is_valid": False, "error": "Ошибка КС IDS", "raw_packet": complete_packet}

        status_code = unpacked_head[3]
        return {
            "is_valid": True,
            "raw_packet": complete_packet,
            "destinationAddress": unpacked_head[0],
            "sourceAddress": unpacked_head[1],
            "status_code": status_code,
            "status_text": IdsExecutionStatus.get_name(status_code),
            "payload": complete_packet[self.HEAD_SIZE:-self.TAIL_SIZE]
        }

    def parse_dynamic_payload(self, payload_bytes: bytes) -> dict:
        """
        ИСПРАВЛЕНО: Прецизионный разбор структуры кадра имитатора КНБК.
        Пакет уложен как: [1B Количество параметров] + [Массив ID параметров] + [Массив 32-битных значений].
        """
        result = {}
        if len(payload_bytes) < 2:
            return result

        # 1. Считываем количество параметров
        items_count = int(payload_bytes[0])

        # 2. Вычленяем список ID параметров (идут сразу за количеством)
        param_ids = []
        for i in range(items_count):
            if 1 + i < len(payload_bytes):
                param_ids.append(int(payload_bytes[1 + i]))

        # 3. Начальная точка сдвига для вычитывания 32-битных значений данных (сразу после массива ID)
        data_start_offset = 1 + items_count

        # 4. Проходим по вытащенным ID параметров и забираем их индивидуальные 32-битные контейнеры
        for idx, param_id in enumerate(param_ids):
            # Вычисляем точное физическое смещение текущего 4-байтового блока данных на шине
            current_offset = data_start_offset + (idx * 4)

            if current_offset + 4 > len(payload_bytes):
                break

            # ИСПРАВЛЕНО: Извлекаем чистый int[0] из кортежа struct.unpack, полностью убирая крэш 0xC0000409
            raw_32bit_value = struct.unpack("<I", payload_bytes[current_offset: current_offset + 4])[0]

            # Ищем метаданные и динамические маски типов в нашей JSON конфигурации
            if param_id in self.identifiers_map:
                meta = self.identifiers_map[param_id]
                param_name = meta["name"]
                type_str = meta["type"].lower().strip()

                # Накладываем маски и битовые фильтры в соответствии с IDS_ID.json
                if type_str == "uint16":
                    interpreted_value = raw_32bit_value & 0xFFFF
                elif type_str == "uint8":
                    interpreted_value = raw_32bit_value & 0xFF
                elif type_str == "uint32":
                    interpreted_value = raw_32bit_value
                elif "bits" in type_str:
                    # Извлекаем количество бит из строки конфигурации (напр., "3bits" -> 3)
                    try:
                        bit_count = int(type_str.replace("bits", "").strip())
                        mask = (1 << bit_count) - 1  # Для 3 бит маска будет 0x07 (111)
                        interpreted_value = raw_32bit_value & mask
                    except ValueError:
                        interpreted_value = raw_32bit_value
                else:
                    interpreted_value = raw_32bit_value

                result[param_name] = interpreted_value
            else:
                # Резервный вывод для неизвестных параметров на шине
                result[f"Param_0x{param_id:02X}"] = raw_32bit_value

        return result