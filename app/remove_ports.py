import subprocess
import json
import os
import sys
import ctypes

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

def remove_pair():
    setupc_path = find_setupc()
    if not setupc_path:
        print("Ошибка: Не найден файл setupc.exe.")
        input("Нажмите Enter для выхода...")
        return

    if not is_admin():
        script_path = os.path.abspath(__file__)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
        return

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if not os.path.exists(INFO_FILE):
        print(f"Файл {INFO_FILE} не найден. Нечего удалять.")
        input("Нажмите Enter для выхода...")
        return

    with open(INFO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    pair_id = data.get("pair_id")
    port1 = data.get("port1")
    port2 = data.get("port2")

    if pair_id is None:
        print("Ошибка: в файле конфигурации отсутствует ID пары портов.")
        input("Нажмите Enter для выхода...")
        return

    print(f"Удаление пары портов {port1} <-> {port2} (ID: {pair_id})...")

    cmd = [setupc_path, "remove", str(pair_id)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(setupc_path))

    if result.returncode != 0:
        print("Ошибка при удалении портов:")
        print(result.stderr or result.stdout)
        input("Нажмите Enter для выхода...")
        return

    os.remove(INFO_FILE)
    print(f"Порты {port1} и {port2} успешно удалены, файл {INFO_FILE} очищен.")
    input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    remove_pair()
