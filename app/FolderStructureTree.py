import os

def generate_tree(path, indent="", lines=None):
    if lines is None:
        lines = []
        
    # Пропускаем служебные папки
    if "__pycache__" in path or ".idea" in path or ".git" in path:
        return lines
        
    try:
        items = os.listdir(path)
    except PermissionError:
        return lines

    # Сортируем: сначала папки, затем файлы
    items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    
    # Исключаем __pycache__ и сам скрипт
    items = [item for item in items if item != "__pycache__" and item != "tree_clean.py"]

    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        is_last = (i == len(items) - 1)
        
        marker = "└── " if is_last else "├── "
        lines.append(f"{indent}{marker}{item}")
        
        if os.path.isdir(full_path):
            next_indent = indent + ("    " if is_last else "│   ")
            generate_tree(full_path, next_indent, lines)
            
    return lines

# Формируем структуру
output_lines = ["app"]
generate_tree(".", lines=output_lines)

# Записываем всё в файл structure.txt с кодировкой UTF-8
output_file = "structure.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print(f"[Успешно] Структура проекта сохранена в файл: {os.path.abspath(output_file)}")
