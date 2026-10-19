from typing import List, Dict, Any


class AutoPollingModel:
    """
    Модель конфигурации автоматического опроса КНБК (MVC Model).
    Хранит структуру выбранных сохраненных команд, режимы таймингов и задержек.
    """
    MODE_FIXED = "fixed"  # Одинаковый интервал для всех
    MODE_INDIVIDUAL = "custom"  # Свой интервал для каждой команды
    MODE_CHAIN = "chain"  # Пауза после прохода всей цепочки

    def __init__(self):
        self.current_mode = self.MODE_FIXED
        self.global_interval_ms = 2000  # Дефолт для фиксированного режима
        self.chain_delay_ms = 5000  # Дефолт для режима цепочки

        # Структура: { "pattern_name": {"enabled": bool, "interval_ms": int} }
        self.patterns_config: Dict[str, Dict[str, Any]] = {}

    def update_configuration(self, mode: str, global_int: int, chain_del: int, config: Dict[str, Dict[str, Any]]):
        """Обновляет параметры сессии автоопроса."""
        self.current_mode = mode
        self.global_interval_ms = global_int
        self.chain_delay_ms = chain_del
        self.patterns_config = config

    def get_active_polling_queue(self) -> list:
        """
        Формирует и возвращает список активных команд для циклического опроса КНБК.
        СИНХРОНИЗИРОВАНО: Команда опрашивается, если она перечислена в patterns_config
        и у неё не выставлен явный старый флаг "enabled": false.
        """
        queue = []
        if not self.patterns_config or not isinstance(self.patterns_config, dict):
            return queue

        for cmd_name, cmd_meta in self.patterns_config.items():
            if isinstance(cmd_meta, dict):
                # Если в старых логах есть "enabled": false — пропускаем, иначе — берем в опрос
                if cmd_meta.get("enabled", True) is not False:
                    queue.append({
                        "name": cmd_name,
                        "interval_ms": cmd_meta.get("interval_ms", 2000)
                    })
        return queue