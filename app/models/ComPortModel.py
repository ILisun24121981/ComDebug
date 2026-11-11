import sys
import threading
import time
from typing import Union, Optional
from PyQt6.QtCore import QObject, pyqtSignal

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

if sys.platform.startswith("win"):
    import winreg

class ComPortModel(QObject):
    """
    Транспортный уровень последовательного интерфейса (PyQt6 Model).
    Генерирует сигналы при поступлении байт или при возникновении аппаратных сбоев.
    """
    data_received = pyqtSignal(bytes)
    # ИСПРАВЛЕНО: Добавлен сигнал для отправки текстового описания причины ошибки связи
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.read_thread: Optional[threading.Thread] = None
        self.is_reading: bool = False

    @staticmethod
    def get_available_ports() -> list[str]:
        """
        Сканирует как физические PnP-порты, так и виртуальные COM-порты
        (через реестр Windows SERIALCOMM и символические ссылки).
        """
        found_ports = set()

        # 1. Стандартный поиск pyserial (включая символические ссылки)
        if SERIAL_AVAILABLE:
            try:
                ports = serial.tools.list_ports.comports(include_links=True)
                for port in ports:
                    if port.device:
                        found_ports.add(port.device)
            except Exception as e:
                print(f"[ComPortModel] Ошибка pyserial.comports: {e}")

        # 2. Прямое чтение ветки реестра Windows (находит com0com, VSPD и нестандартные порты)
        if sys.platform.startswith("win"):
            reg_path = r"HARDWARE\DEVICEMAP\SERIALCOMM"
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    i = 0
                    while True:
                        try:
                            _, port_name, _ = winreg.EnumValue(key, i)
                            if port_name:
                                found_ports.add(str(port_name))
                            i += 1
                        except OSError:
                            # Достигнут конец списка значений в ключе реестра
                            break
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[ComPortModel] Ошибка чтения реестра SERIALCOMM: {e}")

        # 3. Естественная сортировка (COM2 идет перед COM10)
        def _port_sort_key(name: str):
            digits = "".join(filter(str.isdigit, name))
            prefix = "".join(filter(str.isalpha, name))
            return (prefix, int(digits) if digits else 0, name)

        return sorted(found_ports, key=_port_sort_key)

    def open_port(self, port_name: str, baud_rate: int = 9600, timeout_sec: float = 0.5,
                  bytesize: int = 8, parity: str = "None", stopbits: float = 1.0,
                  flow_control: str = "None") -> bool:
        self.close_port()
        if not port_name:
            raise ValueError("Имя порта не задано.")

        if not SERIAL_AVAILABLE:
            raise RuntimeError("Библиотека pyserial не установлена. Работа с портами невозможна.")

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
        self.is_reading = False
        if self.read_thread is not None:
            if self.read_thread.is_alive():
                self.read_thread.join(timeout=0.3)
            self.read_thread = None
        if self.serial_connection is not None:
            if hasattr(self.serial_connection, 'close'):
                if self.serial_connection.is_open:
                    self.serial_connection.close()
            self.serial_connection = None

    def is_connected(self) -> bool:
        return self.serial_connection is not None and self.serial_connection.is_open

    def send_data(self, data: Union[bytes, bytearray, str]) -> int:
        if not self.is_connected():
            raise RuntimeError("Физический порт закрыт. Отправка невозможна.")

        bytes_data = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        bytes_written = self.serial_connection.write(bytes_data)
        self.serial_connection.flush()
        return bytes_written

    def _read_loop(self):
        """Бесконечный фоновый поток. ИСПРАВЛЕНО: перехват и проброс точной причины падения связи."""
        while self.is_reading:
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    if self.serial_connection.in_waiting > 0:
                        raw_bytes = self.serial_connection.read(self.serial_connection.in_waiting)
                        if raw_bytes:
                            self.data_received.emit(raw_bytes)
                    else:
                        time.sleep(0.01)
                except Exception as err:
                    # Извлекаем текстовое описание системного сбоя ОС (например: "Device disconnected")
                    error_message = str(err) if str(err) else "Физический разрыв линии или аппаратный сбой USB"
                    self.is_reading = False

                    # Генерируем сигнал с точным указанием причины для вывода в терминал логов
                    self.error_occurred.emit(error_message)
                    break
            else:
                break
