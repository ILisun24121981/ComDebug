from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from app.views.PortLoggerView import PortLoggerView


class PortLoggerController(QObject):
    """
    Контроллер монитора забойного трафика (MVC).
    Обеспечивает сбор временных меток и безопасную межпотоковую передачу строк в GUI.
    """
    # Регистрируем строго типизированный Qt-сигнал: (метка_времени, направление, данные_HEX)
    log_requested = pyqtSignal(str, str, str)

    def __init__(self, view: PortLoggerView):
        super().__init__()
        self.view: PortLoggerView = view

        # Связываем сигнал со слотом отрисовки в графическом текстовом поле
        self.log_requested.connect(self.view.append_log)

    def write_log(self, direction: str, hex_string: str):
        """Формирует временную метку и генерирует потокобезопасный сигнал для главного потока."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Эмитируем сигнал в очередь сообщений Qt
        self.log_requested.emit(timestamp, direction, hex_string)
