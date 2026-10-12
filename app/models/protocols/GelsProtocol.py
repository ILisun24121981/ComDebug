import struct
from typing import Optional
from app.models.protocols.IProtocol import IProtocol

class GelsExecutionStatus:
    @classmethod
    def get_name(cls, val: int) -> str:
        mapping = {
            0x00: "ExecutionSuccess", 0x01: "ExecutionFailure",
            0x02: "ChecksumError", 0x04: "UndefinedCommand",
            0x20: "BsiNoResponse"
        }
        return mapping.get(val, f"UnknownStatus_0x{val:02X}")

class GelsProtocol(IProtocol):
    """Реализация забойного протокола ГЭЛС (Little-Endian)."""
    HEAD_FORMAT = "<BBBH"
    HEAD_SIZE = 5
    TAIL_FORMAT = "<BB"
    TAIL_SIZE = 2
    END_MARKER = 0xFF

    @property
    def byte_order(self) -> str:
        return "<"

    @staticmethod
    def calc_gels_checksum(data: bytes | bytearray, check_sum: int = 0) -> int:
        """Вычисление циклической контрольной суммы ГЭЛС."""
        for byte in data:
            check_sum ^= byte
            left_shift = (check_sum << 7) & 0xFF
            right_shift = check_sum >> 1
            check_sum = left_shift | right_shift

            if check_sum > 127:
                check_sum ^= 0x3C
        return check_sum

    def pack_message(self, dev_addr: int, mod_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        head_bytes = struct.pack(self.HEAD_FORMAT, dev_addr, mod_addr, cmd, len(payload))
        calculated_crc = self.calc_gels_checksum(head_bytes + payload)
        return head_bytes + payload + struct.pack(self.TAIL_FORMAT, calculated_crc, self.END_MARKER)
    def parse_stream(self, rx_buffer: bytearray) -> Optional[dict]:
        if len(rx_buffer) < self.HEAD_SIZE:
            return None

        unpacked_head = struct.unpack(self.HEAD_FORMAT, rx_buffer[:self.HEAD_SIZE])
        body_size = unpacked_head[3]
        total_size = self.HEAD_SIZE + body_size + self.TAIL_SIZE

        if len(rx_buffer) < total_size:
            return None

        complete_packet = bytes(rx_buffer[:total_size])
        del rx_buffer[:total_size]

        tail = struct.unpack(self.TAIL_FORMAT, complete_packet[-self.TAIL_SIZE:])
        received_crc = tail[0]
        end_marker = tail[1]

        crc = self.calc_gels_checksum(complete_packet[:-self.TAIL_SIZE])

        if received_crc != crc:
            return {"is_valid": False, "error": "Ошибка КС Gels", "raw_packet": complete_packet}

        status_code = unpacked_head[2]
        return {
            "is_valid": True,
            "deviceAddress": unpacked_head[0],
            "moduleAddress": unpacked_head[1],
            "status_code": status_code,
            "status_text": GelsExecutionStatus.get_name(status_code),
            "payload": complete_packet[self.HEAD_SIZE:-self.TAIL_SIZE],
            "endMarker": end_marker
        }
