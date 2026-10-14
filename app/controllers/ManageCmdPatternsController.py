from PyQt6.QtWidgets import QMessageBox
from app.views.ManageCmdPatternsView import ManageCmdPatternsView
from app.models.CmdPatternsManager import CmdPatternsManager


class ManageCmdPatternsController:
    """Контроллер модального диалога редактирования и удаления шаблонов (MVC)."""

    def __init__(self, view: ManageCmdPatternsView, patterns_manager: CmdPatternsManager, protocol_name: str):
        self.view = view
        self.manager = patterns_manager
        self.protocol_name = protocol_name

        # Подключаем клик по кнопке «Удалить» к обработчику
        self.view.delete_button.clicked.connect(self.handle_delete_action)

    def handle_delete_action(self):
        """Вызывается при нажатии кнопки 'Удалить'. Проводит зачистку выбранных элементов."""
        selected_names = self.view.get_selected_patterns()

        if not selected_names:
            QMessageBox.warning(self.view, "Предупреждение", "Не выбрано ни одной команды для удаления.")
            return

        confirm = QMessageBox.question(
            self.view,
            "Подтверждение",
            f"Вы действительно хотите удалить выбранные команды ({len(selected_names)} шт.)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            # Вызываем модель для физической перезаписи JSON на диске
            if self.manager.delete_patterns(self.protocol_name, selected_names):
                QMessageBox.information(self.view, "Успех", "Выбранные команды успешно удалены.")
                self.view.accept()  # Закрываем окно с кодом успешного завершения
