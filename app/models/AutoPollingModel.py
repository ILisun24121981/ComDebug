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

    def get_active_polling_queue(self) -> List[Dict[str, Any]]:
        """
        Возвращает отфильтрованный список активных команд для оркестратора циклов.
        """
        queue = []
        # ИСПРАВЛЕНО: Безопасный проход по конфигурации с жесткой фильтрацией булевых типов (is True)
        if not self.patterns_config:
            return queue

        for name, meta in self.patterns_config.items():
            if meta and meta.get("enabled", False) is True:
                queue.append({
                    "name": name,
                    "interval_ms": meta.get("interval_ms", self.global_interval_ms)
                })
        return queue
