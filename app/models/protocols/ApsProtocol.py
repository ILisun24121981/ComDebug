import struct
from typing import Optional
from app.models.protocols.IProtocol import IProtocol

class ApsExecutionStatus:
    @classmethod
    def get_name(cls, val: int) -> str:
        mapping = {
            0x00: "ExecutionSuccess", 0x01: "ExecutionFailure",
            0x02: "ChecksumError", 0x04: "UndefinedCommand"
        }
        return mapping.get(val, f"UnknownStatus_0x{val:02X}")

class ApsProtocol(IProtocol):
    """Реализация промышленного протокола Aps (Big-Endian)."""
    HEAD_FORMAT = ">BBHB"
    HEAD_SIZE = 5
    TAIL_FORMAT = ">H"
    TAIL_SIZE = 2

    @property
    def byte_order(self) -> str:
        return ">"

    def pack_message(self, dst_addr: int, src_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        total_size = self.HEAD_SIZE + len(payload) + self.TAIL_SIZE
        head_bytes = struct.pack(self.HEAD_FORMAT, dst_addr, src_addr, total_size, cmd)
        crc = sum(head_bytes + payload) & 0xFFFF
        return head_bytes + payload + struct.pack(self.TAIL_FORMAT, crc)

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
        calculated_crc = sum(complete_packet[:-self.TAIL_SIZE]) & 0xFFFF

        if calculated_crc != received_crc:
            return {"is_valid": False, "error": "Ошибка КС Aps", "raw_packet": complete_packet}

        status_code = unpacked_head[3]
        return {
            "is_valid": True,
            "raw_packet": complete_packet,
            "destinationAddress": unpacked_head[0],
            "sourceAddress": unpacked_head[1],
            "status_code": status_code,
            "status_text": ApsExecutionStatus.get_name(status_code),
            "payload": complete_packet[self.HEAD_SIZE:-self.TAIL_SIZE]
        }