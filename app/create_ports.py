import subprocess
import json
import os
import sys
import ctypes
import serial.tools.list_ports

INFO_FILE = "ports_info.json"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def find_setupc():
    possible_paths = [
        r"C:\Program Files (x86)\com0com\setupc.exe",
        r"C:\Program Files\com0com\setupc.exe"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def get_free_com_ports(count=2):
    used_ports = {p.device.upper() for p in serial.tools.list_ports.comports()}
    free_ports = []
    num = 10
    while len(free_ports) < count:
        candidate = f"COM{num}"
        if candidate not in used_ports:
            free_ports.append(candidate)
        num += 1
    return free_ports

def create_pair():
    setupc_path = find_setupc()
    if not setupc_path:
        print("Ошибка: Не найден файл setupc.exe. Проверьте установку com0com.")
        input("Нажмите Enter для выхода...")
        return

    # Если нет прав администратора — перезапускаем скрипт с запросом UAC
    if not is_admin():
        script_path = os.path.abspath(__file__)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
        return

    # Переходим в папку со скриптом, чтобы файл сохранился рядом с ним
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if os.path.exists(INFO_FILE):
        print(f"Файл {INFO_FILE} уже существует! Сначала удалите старую пару.")
        input("Нажмите Enter для выхода...")
        return

    port1, port2 = get_free_com_ports(2)
    print(f"Создание пары портов: {port1} <-> {port2}...")

    cmd = [setupc_path, "install", f"PortName={port1}", f"PortName={port2}"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(setupc_path))

    if result.returncode != 0:
        print("Ошибка при создании портов:")
        print(result.stderr or result.stdout)
        input("Нажмите Enter для выхода...")
        return

    # Получаем ID пары (например, 0 из CNCA0)
    pair_id = None
    for line in result.stdout.splitlines():
        if "CNCA" in line:
            pair_id = line.strip().split()[0].replace("CNCA", "")
            break

    data = {
        "pair_id": pair_id,
        "port1": port1,
        "port2": port2
    }
    with open(INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Успешно! Созданы порты {port1} и {port2}.")
    print(f"Информация сохранена в: {os.path.abspath(INFO_FILE)}")
    input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    create_pair()
