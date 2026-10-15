# === ФАЙЛ: app/controllers/ManageAutoPollingPatternsController.py (ЦЕЛИКОМ) ===
from PyQt6.QtWidgets import QMessageBox


class ManageAutoPollingPatternsController:
    """Контроллер модального диалога удаления конфигураций автоопроса (MVC)."""

    def __init__(self, view, manager, protocol_name):
        self.view = view
        self.manager = manager
        self.protocol_name = protocol_name

        self.view.delete_button.clicked.connect(self.handle_delete_action)

    def handle_delete_action(self):
        selected_names = self.view.get_selected_patterns()

        if not selected_names:
            QMessageBox.warning(
                self.view, "Предупреждение",
                "Не выбрано ни одной конфигурации для удаления."
            )
            return

        confirm = QMessageBox.question(
            self.view, "Подтверждение",
            f"Удалить выбранные конфигурации ({len(selected_names)} шт.)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            if self.manager.delete_patterns(self.protocol_name, selected_names):
                QMessageBox.information(
                    self.view, "Успех", "Конфигурации успешно удалены."
                )
                self.view.accept()
