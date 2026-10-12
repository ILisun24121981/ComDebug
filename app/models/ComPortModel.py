import threading
import time
from collections.abc import Callable
from typing import Union, Optional

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class ComPortModel:
    """Транспортный уровень для работы с физическим последовательным интерфейсом прибора."""

    def __init__(self):
        self.serial_connection = None
        self.read_thread: Optional[threading.Thread] = None
        self.is_reading: bool = False
        # Слот-колбэк, куда мы будем перенаправлять считанные сырые байты
        self.on_data_received_callback: Optional[Callable[[bytes], None]] = None

    @staticmethod
    def get_available_ports() -> list[str]:
        """Сканирует операционную систему и возвращает список доступных физических COM-портов."""
        if SERIAL_AVAILABLE:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        return []

    def open_port(self, port_name: str, baud_rate: int = 9600, timeout_sec: float = 0.5,
                  bytesize: int = 8, parity: str = "None", stopbits: float = 1.0,
                  flow_control: str = "None") -> bool:
        """Открывает реальный COM-порт с низкоуровневыми настройками, считанными из JSON."""
        self.close_port()
        if not port_name:
            raise ValueError("Имя порта не задано.")

        if not SERIAL_AVAILABLE:
            raise RuntimeError("Библиотека pyserial не установлена. Работа с портами невозможна.")

        # Конвертация строковых конфигураций JSON в типы библиотеки pyserial
        parity_map = {
            "none": serial.PARITY_NONE, "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD, "mark": getattr(serial, 'PARITY_MARK', 'M'),
            "space": getattr(serial, 'PARITY_SPACE', 'S')
        }
        pyserial_parity = parity_map.get(parity.lower(), serial.PARITY_NONE)

        stopbits_map = {1.0: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2.0: serial.STOPBITS_TWO}
        try:
            sb_val = float(stopbits)
        except ValueError:
            sb_val = 1.0
        pyserial_stopbits = stopbits_map.get(sb_val, serial.STOPBITS_ONE)

        xonxoff = "xon" in flow_control.lower()
        rtscts = "rts" in flow_control.lower()

        # Выполнение системного открытия порта шины данных
        self.serial_connection = serial.Serial(
            port=port_name, baudrate=baud_rate, bytesize=bytesize,
            parity=pyserial_parity, stopbits=pyserial_stopbits,
            xonxoff=xonxoff, rtscts=rtscts, timeout=timeout_sec, write_timeout=1.0,
        )

        if self.serial_connection.is_open:
            self.is_reading = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            return True
        return False
    def close_port(self) -> None:
        """Безопасно останавливает фоновый поток вычитки шины и освобождает дескриптор порта."""
        self.is_reading = False
        if self.read_thread is not None:
            if self.read_thread.is_alive():
                self.read_thread.join(timeout=0.5)
            self.read_thread = None
        if self.serial_connection is not None:
            if hasattr(self.serial_connection, 'close'):
                if self.serial_connection.is_open:
                    self.serial_connection.close()
            self.serial_connection = None

    def is_connected(self) -> bool:
        """Возвращает текущий статус соединения."""
        return self.serial_connection is not None and self.serial_connection.is_open

    def send_data(self, data: Union[bytes, bytearray, str]) -> int:
        """Отправляет бинарный массив байт в открытый последовательный порт."""
        if not self.is_connected():
            raise RuntimeError("Физический порт закрыт. Отправка невозможна.")

        bytes_data = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        bytes_written = self.serial_connection.write(bytes_data)
        self.serial_connection.flush()
        return bytes_written

    def _read_loop(self):
        """Бесконечный фоновый поток побайтовой сборки входящего потока данных."""
        while self.is_reading:
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    if self.serial_connection.in_waiting > 0:
                        raw_bytes = self.serial_connection.read(self.serial_connection.in_waiting)
                        if raw_bytes and self.on_data_received_callback:
                            self.on_data_received_callback(raw_bytes)
                    else:
                        time.sleep(0.01)
                except Exception:
                    break
            else:
                break
