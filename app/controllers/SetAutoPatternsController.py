# === ФАЙЛ: app/controllers/SetAutoPatternsController.py (ЧАСТЬ 1 ИЗ 3) ===
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QDialog, QMessageBox
from app.views.ManageAutoPollingPatternsView import ManageAutoPollingPatternsView
from app.controllers.ManageAutoPollingPatternsController import (
    ManageAutoPollingPatternsController
)


class SetAutoPatternsController(QObject):
    """
    Контроллер панели управления автоматическим опросом КНБК (MVC Controller).
    Синхронизирует дисковые шаблоны, модель AutoPollingModel и интерфейс.
    """

    def __init__(self, view, auto_polling_controller):
        super().__init__()
        print("[TRACE-AutoPatterns] Инициализация конструктора SetAutoPatternsController...")
        self.view = view
        self.auto_ctrl = auto_polling_controller
        self.active_protocol = "Gels"
        self._block_radio_handler = False

        # Связываем сигналы графических элементов с обработчиками
        self.view.mode_radio_changed.connect(self.handle_mode_radio_changed)
        self.view.btn_initial_config.clicked.connect(self._handle_config_clicked)
        self.view.btn_config.clicked.connect(self._handle_config_clicked)
        self.view.btn_start.clicked.connect(self._handle_start_clicked)
        self.view.btn_stop.clicked.connect(self.auto_ctrl.handle_stop_execution)
        self.view.btn_edit_patterns.clicked.connect(self.open_manage_auto_patterns_dialog)
        self.view.btn_save_pattern.clicked.connect(self._handle_save_clicked)

        # Сигнал изменения выбора в выпадающем списке шаблонов
        self.view.combo_patterns.currentTextChanged.connect(self._handle_combo_changed)

    def configure_for_protocol(self, protocol_name: str):
        """Вызывается автоматически в момент нажатия кнопки 'Подключить' на COM-порту."""
        print(f"\n[TRACE-AutoPatterns] === ПОДКЛЮЧЕНИЕ: Инициализация протокола '{protocol_name}' ===")
        self._block_radio_handler = True
        self.active_protocol = protocol_name

        # Выгружаем список сохраненных наборов с диска и инициализируем модель дефолтным элементом
        self.refresh_patterns_list()
        self._block_radio_handler = False

    # === ФАЙЛ: app/controllers/SetAutoPatternsController.py (ЧАСТЬ 2 ИЗ 3) ===

    def refresh_patterns_list(self):
        """
        Выгружает названия шаблонов из JSON и загружает DefaultPattern или строго последний набор.
        СИНХРОНИЗИРОВАНО: Применяется при каждом переключении протоколов на физическом COM-порту.
        """
        print(f"\n[TRACE-AutoPatterns] Сброс и обновление списков для активного протокола: '{self.active_protocol}'")
        manager = self.auto_ctrl.auto_patterns_manager

        # Вычитываем сырой корневой словарь JSON-файла для нового протокола
        raw_file_data = manager._read_file(self.active_protocol)

        # Получаем чистый список имен шаблонов (исключая служебные поля метаданных)
        names = [k for l in [manager.load_pattern_names(self.active_protocol)] for k in l if k != "DefaultPattern"]
        print(f"[TRACE-AutoPatterns] Шаблоны, найденные на диске для {self.active_protocol}: {names}")

        # Блокируем шторм графических сигналов на время полной перестройки комбобокса
        self.view.combo_patterns.blockSignals(True)
        self.view.combo_patterns.clear()
        if names:
            self.view.combo_patterns.addItems(names)
        self.view.combo_patterns.blockSignals(False)

        if not names:
            print(f"[TRACE-AutoPatterns] Шаблоны для протокола {self.active_protocol} отсутствуют. Очистка модели.")
            self.view.show_initial_empty_state()
            self.auto_ctrl.model.current_pattern_name = ""
            # Очищаем модель, чтобы старый протокол не оставался в памяти
            self.auto_ctrl.model.update_configuration(mode="fixed", global_int=2000, chain_del=5000, config={})
        else:
            if self.view.radio_saved.isChecked():
                print("[TRACE-AutoPatterns] Режим 'Сохраненный' активен. Переходим к сквозной инициализации...")
                self.view.set_saved_mode_view()

                # Принудительно затираем старое имя в модели, чтобы запустить чистый поиск по новому файлу
                self.auto_ctrl.model.current_pattern_name = ""

                # 1. Сначала проверяем наличие сохраненной переменной DefaultPattern в метаданных файла нового протокола
                default_from_file = raw_file_data.get("DefaultPattern", "")
                if default_from_file and default_from_file in names:
                    target_name = default_from_file
                    print(
                        f"[TRACE-AutoPatterns] Найдена переменная DefaultPattern для {self.active_protocol}. Выбор: '{target_name}'")
                else:
                    # 2. Если переменной нет, берем СТРОГО самый последний шаблон из списка на диске нового протокола
                    target_name = names[-1]
                    print(
                        f"[TRACE-AutoPatterns] DefaultPattern отсутствует. Авто-выбор ПОСЛЕДНЕГО набора: '{target_name}'")

                # Синхронизируем текст выпадающего списка в интерфейсе
                self.view.combo_patterns.blockSignals(True)
                self.view.combo_patterns.setCurrentText(target_name)
                self.view.combo_patterns.blockSignals(False)

                # СКВОЗНОЙ ХУК: Временно открываем блокировщик радио-хэндлеров, чтобы гарантированно
                # прописать параметры выбранного шаблона нового протокола в модель AutoPollingModel
                old_block_state = self._block_radio_handler
                self._block_radio_handler = False
                try:
                    self._handle_combo_changed(target_name)
                finally:
                    self._block_radio_handler = old_block_state
            else:
                self.view.set_new_mode_view()

    def _handle_combo_changed(self, name: str):
        """Вызывается при выборе другого шаблона из выпадающего списка."""
        if self._block_radio_handler or not name or name.strip() == "" or name == "DefaultPattern":
            return

        print(f"[TRACE-AutoPatterns] Изменен выбор в QComboBox. Чтение параметров для шаблона: '{name}'")
        config = self.auto_ctrl.auto_patterns_manager.load_pattern_config(self.active_protocol, name)
        print(f"[TRACE-AutoPatterns] Данные прочитаны с диска для модели: {config}")

        if config:
            # Напрямую передаем чистый JSON-конфиг в обновленную модель
            self.auto_ctrl.model.update_configuration(
                mode=config.get("mode", "fixed"),
                global_int=config.get("global_interval_ms", 2000),
                chain_del=config.get("chain_delay_ms", 5000),
                config=config.get("patterns", {})
            )
            self.auto_ctrl.model.current_pattern_name = name
            print(
                f"[TRACE-AutoPatterns] Модель AutoPollingModel синхронизирована. Рабочий шаблон: '{self.auto_ctrl.model.current_pattern_name}'")

    def _handle_config_clicked(self):
        """Вызывается при нажатии кнопки 'Настроить'. Загружает параметры и имя ИЗ МОДЕЛИ."""
        print("\n[TRACE-AutoPatterns] === КЛИК: НАСТРОЙКА АВТООПРОСА ===")

        try:
            p_manager = self.auto_ctrl.main_controller.patterns_manager
            saved_patterns = p_manager.load_patterns_names(self.active_protocol)
        except Exception as e:
            print(f"[TRACE-AutoPatterns] Ошибка выгрузки команд пульта: {e}")
            saved_patterns = []

        manager = self.auto_ctrl.auto_patterns_manager
        names = [k for l in [manager.load_pattern_names(self.active_protocol)] for k in l if k != "DefaultPattern"]

        active_pattern_name = getattr(self.auto_ctrl.model, "current_pattern_name", "")

        if not names:
            active_pattern_name = manager.generate_next_default_name(self.active_protocol)
            self.auto_ctrl.model.current_pattern_name = active_pattern_name
            print(f"[TRACE-AutoPatterns] Пустой диск. Сгенерировано дефолтное имя: '{active_pattern_name}'")

        current_config = {
            "mode": self.auto_ctrl.model.current_mode,
            "global_interval_ms": self.auto_ctrl.model.global_interval_ms,
            "chain_delay_ms": self.auto_ctrl.model.chain_delay_ms,
            "patterns": self.auto_ctrl.model.patterns_config,
            "name": active_pattern_name
        }
        print(
            f"[TRACE-AutoPatterns] Параметры извлечены из модели. Имя: '{active_pattern_name}', Config: {current_config}")

        from app.views.AutoPollingSettingView import AutoPollingSettingView
        dialog = AutoPollingSettingView(
            saved_patterns=saved_patterns,
            current_config=current_config,
            parent=self.view.window()
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_user_configuration()
            print(f"[TRACE-AutoPatterns] Окно настроек закрыто кнопкой 'Сохранить'. Новый конфиг: {new_config}")

            self.auto_ctrl.model.update_configuration(
                mode=new_config["mode"],
                global_int=new_config["global_interval_ms"],
                chain_del=new_config["chain_delay_ms"],
                config=new_config["patterns"]
            )
            print("[TRACE-AutoPatterns] Параметры в AutoPollingModel обновлены. Переходим к перезаписи файла...")

            if not names:
                print("[TRACE-AutoPatterns] Первый запуск. Переключение в set_initial_capture_name_view")
                self.view.set_initial_capture_name_view()
                self.view.input_pattern_name.setText(active_pattern_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
                self.auto_ctrl.model.patterns_config = new_config["patterns"]
            else:
                self._execute_save_to_disk(active_pattern_name)

    # === ФАЙЛ: app/controllers/SetAutoPatternsController.py (ЧАСТЬ 3 ИЗ 3) ===

    def _handle_save_clicked(self):
        """Вызывается при ручном сохранении (в режиме Новый)."""
        name = self.view.input_pattern_name.text().strip()
        if not name or name == "DefaultPattern":
            main_window = self.view.window()
            if hasattr(main_window, "send_cmd_view"):
                main_window.send_cmd_view.show_error("Предупреждение", "Введите имя шаблона для автоопроса.")
            return

        self.auto_ctrl.model.current_pattern_name = name
        self._execute_save_to_disk(name)

    def _execute_save_to_disk(self, target_name: str):
        """Внутренний метод записи текущей конфигурации модели на диск и принудительного обновления UI."""
        if target_name == "DefaultPattern": return
        print(f"[TRACE-AutoPatterns] Запуск записи на диск для шаблона: '{target_name}'")

        raw_patterns = self.auto_ctrl.model.patterns_config
        filtered_patterns = {}

        if isinstance(raw_patterns, dict):
            for cmd_name, cmd_meta in raw_patterns.items():
                if isinstance(cmd_meta, dict):
                    if cmd_meta.get("enabled", True) is not False:
                        filtered_patterns[cmd_name] = {
                            "interval_ms": cmd_meta.get("interval_ms", 2000)
                        }

        current_config = {
            "mode": self.auto_ctrl.model.current_mode,
            "global_interval_ms": self.auto_ctrl.model.global_interval_ms,
            "chain_delay_ms": self.auto_ctrl.model.chain_delay_ms,
            "patterns": filtered_patterns
        }

        # ЖЕСТКАЯ БЛОКИРОВКА СИГНАЛОВ НА ВРЕМЯ ВСЕГО ЦИКЛА ПЕРЕРИСОВКИ
        self.view.blockSignals(True)
        self._block_radio_handler = True

        try:
            manager = self.auto_ctrl.auto_patterns_manager
            if manager.save_pattern(self.active_protocol, target_name, current_config):
                print(f"[TRACE-AutoPatterns] Шаблон '{target_name}' успешно перезаписан на диске.")

                self.view.radio_saved.setChecked(True)
                self.view.set_saved_mode_view()

                names = [k for l in [manager.load_pattern_names(self.active_protocol)] for k in l if
                         k != "DefaultPattern"]

                self.view.combo_patterns.blockSignals(True)
                self.view.combo_patterns.clear()
                if names:
                    self.view.combo_patterns.addItems(names)
                    self.view.combo_patterns.setCurrentText(target_name)
                self.view.combo_patterns.blockSignals(False)

                self.auto_ctrl.model.current_pattern_name = target_name
        except Exception as e:
            print(f"[TRACE-AutoPatterns] Ошибка перезаписи шаблона: {e}")
        finally:
            self.view.blockSignals(False)
            self._block_radio_handler = False
            print(
                f"[TRACE-AutoPatterns] Цикл сохранения завершен. Активные команды в модели: {self.auto_ctrl.model.patterns_config}")

    def handle_mode_radio_changed(self, is_saved_mode: bool):
        if self._block_radio_handler:
            return

        if is_saved_mode:
            self.view.set_saved_mode_view()
            self._handle_combo_changed(self.view.combo_patterns.currentText())
        else:
            is_accepted = self.auto_ctrl.execute_polling_configuration_dialog()
            if is_accepted:
                self.view.set_new_mode_view()
                manager = self.auto_ctrl.auto_patterns_manager
                default_name = manager.generate_next_default_name(self.active_protocol)
                self.view.input_pattern_name.setText(default_name)
                self.view.input_pattern_name.selectAll()
                self.view.input_pattern_name.setFocus()
            else:
                self._block_radio_handler = True
                self.view.radio_saved.setChecked(True)
                self.view.set_saved_mode_view()
                self._block_radio_handler = False
                self.refresh_patterns_list()

    def open_manage_auto_patterns_dialog(self):
        manager = self.auto_ctrl.auto_patterns_manager
        names = [k for l in [manager.load_pattern_names(self.active_protocol)] for k in l if k != "DefaultPattern"]
        dialog = ManageAutoPollingPatternsView(names, parent=self.view)
        controller = ManageAutoPollingPatternsController(
            dialog, manager, self.active_protocol
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_patterns_list()

    def _handle_start_clicked(self):
        """Вызывается при клике по кнопке 'Запустить'. Запоминает DefaultPattern на диске."""
        print("[TRACE-AutoPatterns] Нажата кнопка СТАРТ автоопроса.")

        # Фиксируем имя активного запущенного шаблона из модели
        active_template_name = getattr(self.auto_ctrl.model, "current_pattern_name", "")
        print(f"[TRACE-AutoPatterns] Запускаемый в работу рабочий шаблон: '{active_template_name}'")

        if active_template_name and active_template_name != "DefaultPattern":
            try:
                manager = self.auto_ctrl.auto_patterns_manager
                # Читаем файл целиком, записываем мета-поле DefaultPattern и сохраняем обратно на диск
                file_data = manager._read_file(self.active_protocol)
                file_data["DefaultPattern"] = active_template_name
                manager._write_file(self.active_protocol, file_data)
                print(
                    f"[TRACE-AutoPatterns] Переменная 'DefaultPattern': '{active_template_name}' успешно зафиксирована.")
            except Exception as e:
                print(f"[TRACE-AutoPatterns] Не удалось сохранить DefaultPattern в метаданные: {e}")

        # Вызываем оригинальный метод запуска фоновой сессии
        is_saved = self.view.radio_saved.isChecked()
        self.auto_ctrl.handle_start_by_ui_context(is_saved)
