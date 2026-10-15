# === ФАЙЛ: app/controllers/SetAutoPatternsController.py (ЧАСТЬ 1 ИЗ 2) ===
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QDialog, QMessageBox
from app.views.ManageAutoPollingPatternsView import ManageAutoPollingPatternsView
from app.controllers.ManageAutoPollingPatternsController import (
    ManageAutoPollingPatternsController
)


class SetAutoPatternsController(QObject):
    """
    Контроллер панели автоопроса (PyQt6 Controller).
    Очищен от лишних таймеров, работает синхронно и стабильно.
    """

    def __init__(self, view, auto_polling_controller):
        super().__init__()
        self.view = view
        self.auto_ctrl = auto_polling_controller
        self.active_protocol = "Gels"

        # Главный флаг защиты: блокирует шторм событий при закрытии сессий
        self._block_radio_handler = False

        self.view.mode_radio_changed.connect(self.handle_mode_radio_changed)

        self.view.btn_initial_config.clicked.connect(self._handle_config_clicked)
        self.view.btn_config.clicked.connect(self._handle_config_clicked)

        self.view.btn_start.clicked.connect(self._handle_start_clicked)
        self.view.btn_stop.clicked.connect(self.auto_ctrl.handle_stop_execution)

        self.view.btn_edit_patterns.clicked.connect(
            self.open_manage_auto_patterns_dialog
        )
        self.view.btn_save_pattern.clicked.connect(self._handle_save_clicked)
        self.view.combo_patterns.currentTextChanged.connect(self._handle_combo_changed)

    def configure_for_protocol(self, protocol_name: str):
        """Вызывается при старте/остановке сессий связи."""
        self._block_radio_handler = True
        self.active_protocol = protocol_name

        # ОЧИЩЕНО: Убран QTimer.singleShot, обновление списка идет синхронно
        self.refresh_patterns_list()
        self._block_radio_handler = False

    def refresh_patterns_list(self):
        """Определяет стартовое или рабочее состояние панели КНБК."""
        names = self.auto_ctrl.auto_patterns_manager.load_pattern_names(
            self.active_protocol
        )

        self.view.combo_patterns.blockSignals(True)
        self.view.combo_patterns.clear()
        if names:
            self.view.combo_patterns.addItems(names)
        self.view.combo_patterns.blockSignals(False)

        if not names:
            self.view.show_initial_empty_state()
        else:
            if self.view.radio_saved.isChecked():
                self.view.set_saved_mode_view()
                if names:
                    self._handle_combo_changed(self.view.combo_patterns.currentText())
            else:
                self.view.set_new_mode_view()

    def handle_mode_radio_changed(self, is_saved_mode: bool):
        if self._block_radio_handler:
            return

        if is_saved_mode:
            if (
                    self.auto_ctrl.model.patterns_config
                    and self.view.input_pattern_name.isVisible()
            ):
                res = QMessageBox.warning(
                    self.view, "Предупреждение",
                    "Текущий шаблон не сохранен.\nПереход на вкладку "
                    "'Сохраненные' сбросит настройки текущего шаблона.",
                    QMessageBox.StandardButton.Ok |
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )

                if res == QMessageBox.StandardButton.Cancel:
                    self._block_radio_handler = True
                    self.view.radio_new.setChecked(True)
                    self._block_radio_handler = False
                    return
                else:
                    self.auto_ctrl.model.patterns_config = {}

            self.view.set_saved_mode_view()
            self._handle_combo_changed(self.view.combo_patterns.currentText())
        else:
            is_accepted = self.auto_ctrl.execute_polling_configuration_dialog()
            if is_accepted:
                # ОЧИЩЕНО: Переключение макета выполняется мгновенно и линейно
                self.view.set_new_mode_view()
                default_name = (
                    self.auto_ctrl.auto_patterns_manager.generate_next_default_name(
                        self.active_protocol
                    )
                )
                self.view.input_pattern_name.setText(default_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
            else:
                self._block_radio_handler = True
                self.view.radio_saved.setChecked(True)
                self.view.set_saved_mode_view()
                self._block_radio_handler = False
                self.refresh_patterns_list()
# === ФАЙЛ: app/controllers/SetAutoPatternsController.py (ЧАСТЬ 2 ИЗ 2) ===

    def _handle_config_clicked(self):
        is_accepted = self.auto_ctrl.execute_polling_configuration_dialog()
        if is_accepted:
            names = self.auto_ctrl.auto_patterns_manager.load_pattern_names(
                self.active_protocol
            )
            # ОЧИЩЕНО: Убраны отложенные singleShot вызовы, код стал линейным
            if not names:
                self.view.set_initial_capture_name_view()
                default_name = (
                    self.auto_ctrl.auto_patterns_manager.generate_next_default_name(
                        self.active_protocol
                    )
                )
                self.view.input_pattern_name.setText(default_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
            else:
                self.refresh_patterns_list()

    def _handle_combo_changed(self, name: str):
        # Монументальный барьер от пустых строк .clear() при отключении порта
        if self._block_radio_handler or not name or name.strip() == "":
            return

        config = self.auto_ctrl.auto_patterns_manager.load_pattern_config(
            self.active_protocol, name
        )
        if config:
            self.auto_ctrl.model.update_configuration(
                mode=config.get("mode", "fixed"),
                global_int=config.get("global_interval_ms", 2000),
                chain_del=config.get("chain_delay_ms", 5000),
                config=config.get("patterns", {})
            )

    def _handle_save_clicked(self):
        name = self.view.input_pattern_name.text().strip()
        if not name:
            self.auto_ctrl.view.send_cmd_view.show_error(
                "Предупреждение", "Введите имя шаблона для автоопроса."
            )
            return

        current_config = {
            "mode": self.auto_ctrl.model.current_mode,
            "global_interval_ms": self.auto_ctrl.model.global_interval_ms,
            "chain_delay_ms": self.auto_ctrl.model.chain_delay_ms,
            "patterns": self.auto_ctrl.model.patterns_config
        }

        if self.auto_ctrl.auto_patterns_manager.save_pattern(
                self.active_protocol, name, current_config
        ):
            self.auto_ctrl.model.patterns_config = {}
            self._block_radio_handler = True
            self.view.radio_saved.setChecked(True)
            self._block_radio_handler = False
            self.refresh_patterns_list()
            self.view.combo_patterns.setCurrentText(name)

    def open_manage_auto_patterns_dialog(self):
        names = self.auto_ctrl.auto_patterns_manager.load_pattern_names(
            self.active_protocol
        )
        dialog = ManageAutoPollingPatternsView(names, parent=self.view)
        controller = ManageAutoPollingPatternsController(
            dialog, self.auto_ctrl.auto_patterns_manager, self.active_protocol
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_patterns_list()

    def _handle_start_clicked(self):
        is_saved = self.view.radio_saved.isChecked()
        self.auto_ctrl.handle_start_by_ui_context(is_saved)
