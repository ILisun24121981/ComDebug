# === ФАЙЛ: app/controllers/SetCmdDataViewController.py (ЧАСТЬ 1 ИЗ 2) ===
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QDialog, QMessageBox
from app.views.CmdDataSettingView import CmdDataSettingView
from app.models.CmdViewManager import CmdViewManager
from app.views.ManageAutoPollingPatternsView import ManageAutoPollingPatternsView
from app.controllers.ManageAutoPollingPatternsController import ManageAutoPollingPatternsController


class SetCmdDataViewController(QObject):
    """
    Контроллер управления комплексными конфигурациями соответствия View КНБК (Gels/Aps MVC).
    """

    def __init__(self, view, config_manager, patterns_manager, main_controller):
        super().__init__()
        self.view = view
        self.config_manager = config_manager
        self.patterns_manager = patterns_manager
        self.main_controller = main_controller

        self.cmd_view_manager = CmdViewManager()
        self.active_protocol = "Gels"

        self.temp_in_memory_config = {}
        self._block_radio_handler = False

        from app.controllers.StructuresDisplayController import StructuresDisplayController
        self.display_math_controller = StructuresDisplayController(
            cmd_view_manager=self.cmd_view_manager,
            patterns_manager=self.patterns_manager
        )

        self.view.mode_radio_changed.connect(self.handle_mode_radio_changed)
        self.view.btn_initial_config.clicked.connect(self._handle_config_clicked)
        self.view.btn_config.clicked.connect(self._handle_config_clicked)
        self.view.btn_save_pattern.clicked.connect(self._handle_save_clicked)
        self.view.btn_edit_patterns.clicked.connect(self.open_manage_mappings_dialog)
        self.view.combo_patterns.currentTextChanged.connect(self._handle_combo_changed)

        self.view.open_requested.connect(self.open_telemetry_display_window)
        self.live_display_dialog = None

    def configure_for_protocol(self, protocol_name: str):
        self._block_radio_handler = True
        self.active_protocol = protocol_name
        self.refresh_patterns_list()
        self._block_radio_handler = False

    def refresh_patterns_list(self):
        names = self.cmd_view_manager.load_pattern_names(self.active_protocol)

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

# === ФАЙЛ: app/controllers/SetCmdDataViewController.py (ЧАСТЬ 2 ИЗ 2) ===

    def handle_mode_radio_changed(self, is_saved_mode: bool):
        if self._block_radio_handler:
            return

        if is_saved_mode:
            if self.temp_in_memory_config and self.view.input_pattern_name.isVisible():
                res = QMessageBox.warning(
                    self.view, "Предупреждение",
                    "Текущая конфигурация отображения не сохранена.\nПереход на вкладку "
                    "'Сохраненные' сбросит текущие настройки.",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )
                if res == QMessageBox.StandardButton.Cancel:
                    self._block_radio_handler = True
                    self.view.radio_new.setChecked(True)
                    self._block_radio_handler = False
                    return
                else:
                    self.temp_in_memory_config = {}

            self.view.set_saved_mode_view()
            self._handle_combo_changed(self.view.combo_patterns.currentText())
        else:
            is_accepted = self._execute_mapping_dialog()
            if is_accepted:
                self.view.set_new_mode_view()
                default_name = self.cmd_view_manager.generate_next_default_name(self.active_protocol)
                self.view.input_pattern_name.setText(default_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
            else:
                self._block_radio_handler = True
                self.view.radio_saved.setChecked(True)
                self.view.set_saved_mode_view()
                self._block_radio_handler = False
                self.refresh_patterns_list()

    def _handle_config_clicked(self):
        is_accepted = self._execute_mapping_dialog()
        if is_accepted:
            names = self.cmd_view_manager.load_pattern_names(self.active_protocol)
            if not names:
                self.view.set_initial_capture_name_view()
                default_name = self.cmd_view_manager.generate_next_default_name(self.active_protocol)
                self.view.input_pattern_name.setText(default_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
            else:
                self.refresh_patterns_list()

    def _execute_mapping_dialog(self) -> bool:
        saved_commands = self.patterns_manager.load_patterns_names(self.active_protocol)
        available_views = self.cmd_view_manager.load_available_view_structures()

        dialog = CmdDataSettingView(
            saved_commands=saved_commands,
            available_structures=available_views,
            current_config=self.temp_in_memory_config,
            parent=self.view.parent()
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.temp_in_memory_config = dialog.get_user_configuration()
            return True
        return False

    def _handle_combo_changed(self, name: str):
        if self._block_radio_handler or not name or name.strip() == "":
            return
        config = self.cmd_view_manager.load_pattern_config(self.active_protocol, name)
        if config:
            self.temp_in_memory_config = config

    def _handle_save_clicked(self):
        name = self.view.input_pattern_name.text().strip()
        if not name:
            QMessageBox.warning(self.view, "Предупреждение", "Введите имя шаблона отображения данных.")
            return

        if self.cmd_view_manager.save_pattern(self.active_protocol, name, self.temp_in_memory_config):
            self.temp_in_memory_config = {}
            self._block_radio_handler = True
            self.view.radio_saved.setChecked(True)
            self._block_radio_handler = False
            self.refresh_patterns_list()
            self.view.combo_patterns.setCurrentText(name)

    def open_manage_mappings_dialog(self):
        names = self.cmd_view_manager.load_pattern_names(self.active_protocol)
        dialog = ManageAutoPollingPatternsView(names, parent=self.view)
        dialog.setWindowTitle("Редактирование конфигураций отображения")

        controller = ManageAutoPollingPatternsController(
            dialog, self.cmd_view_manager, self.active_protocol
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_patterns_list()

    def open_telemetry_display_window(self):
        current_pattern_name = self.view.combo_patterns.currentText()
        if not current_pattern_name:
            QMessageBox.warning(self.view, "Предупреждение", "Не выбран рабочий шаблон отображения данных.")
            return

        config = self.cmd_view_manager.load_pattern_config(self.active_protocol, current_pattern_name)
        active_mappings = config.get("mappings", {})
        available_views = self.cmd_view_manager.load_available_view_structures()

        from app.views.StructuresDisplayView import StructuresDisplayView

        self.live_display_dialog = StructuresDisplayView(
            active_mappings=active_mappings,
            structures_definitions=available_views,
            parent=self.view.parent()
        )

        self.display_math_controller.set_active_display_dialog(self.live_display_dialog)
        self.live_display_dialog.show()
