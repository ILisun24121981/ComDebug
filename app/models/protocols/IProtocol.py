from typing import Optional

class IProtocol:
    """Абстрактный интерфейс для полиморфных забойных протоколов связи КНБК."""

    @property
    def byte_order(self) -> str:
        raise NotImplementedError

    def pack_message(self, dst_addr: int, src_addr: int, cmd: int, payload: bytes = b"") -> bytes:
        raise NotImplementedError

    def parse_stream(self, rx_buffer: bytearray) -> Optional[dict]:
        raise NotImplementedError
