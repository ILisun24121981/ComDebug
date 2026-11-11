import struct
from typing import Optional
from app.models.protocols.IProtocol import IProtocol
from app.models.protocols.GelsProtocol import GelsProtocol


class UniExecutionStatus:
    @classmethod
    def get_name(cls, val: int) -> str:
        mapping = {
            0x00: "ExecutionSuccess"
        }
        return mapping.get(val, f"UnknownStatus_0x{val:02X}")


class UniProtocol(IProtocol):
    """Реализация протокола обмена НПП 'Энергия-универсальный' (Uni, Little-Endian)."""
    HEAD_FORMAT = "<BBBH"  # DST(1B) + SRC(1B) + CMD/STATUS(1B) + DATA_SIZE(2B)
    HEAD_SIZE = 5
    TAIL_FORMAT = "<BB"    # CRC(1B) + END_MARKER(1B)
    TAIL_SIZE = 2
    END_MARKER = 0xFF

    @property
    def byte_order(self) -> str:
        return "<"

    def pack_message(self, dst_addr: int, src_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        head_bytes = struct.pack(self.HEAD_FORMAT, dst_addr, src_addr, cmd, len(payload))
        calculated_crc = GelsProtocol.calc_gels_checksum(head_bytes + payload)
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

        if end_marker != self.END_MARKER:
            return {"is_valid": False, "error": "Неверный маркер конца кадра Uni", "raw_packet": complete_packet}

        crc = GelsProtocol.calc_gels_checksum(complete_packet[:-self.TAIL_SIZE])
        if received_crc != crc:
            return {"is_valid": False, "error": "Ошибка КС Uni", "raw_packet": complete_packet}

        status_code = unpacked_head[2]
        return {
            "is_valid": True,
            "raw_packet": complete_packet,
            "destinationAddress": unpacked_head[0],
            "sourceAddress": unpacked_head[1],
            "status_code": status_code,
            "status_text": UniExecutionStatus.get_name(status_code),
            "payload": complete_packet[self.HEAD_SIZE:-self.TAIL_SIZE],
            "endMarker": end_marker
        }
