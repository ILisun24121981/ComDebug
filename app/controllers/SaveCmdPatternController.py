from PyQt6.QtWidgets import QDialog, QMessageBox
from app.views.SaveCmdPatternView import SaveCmdPatternView
from app.models.CmdPatternsManager import CmdPatternsManager


class SaveCmdPatternController:
    """Контроллер модального диалога сохранения шаблонов (MVC)."""

    def __init__(self, view: SaveCmdPatternView, patterns_manager: CmdPatternsManager):
        self.view = view
        self.manager = patterns_manager

    def execute_save(self, protocol_name: str, raw_packet: bytes) -> bool:
        """Запускает модальный диалог и передает данные на сохранение в менеджер."""
        if self.view.exec() == QDialog.DialogCode.Accepted:
            pattern_name = self.view.get_pattern_name()

            if not pattern_name:
                QMessageBox.warning(self.view, "Предупреждение", "Шаблон не сохранен: введите название.")
                return False

            # Вызываем модель для физической записи на диск
            return self.manager.save_pattern(protocol_name, pattern_name, raw_packet)
        return False