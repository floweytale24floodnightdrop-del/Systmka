"""Организация файлов — Систмка сама придумывает структуру"""

import os
import re
import json
from datetime import datetime

def analyze_file_content(filename):
    """Проанализировать содержимое файла"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        functions = re.findall(r'def\s+(\w+)', content)
        classes = re.findall(r'class\s+(\w+)', content)
        imports = re.findall(r'(?:from\s+(\w+)|import\s+(\w+))', content)
        
        keywords = {
            "bot": ["bot", "telebot", "polling", "message_handler"],
            "config": ["token", "config", "settings", "key"],
            "handler": ["handler", "message", "command", "callback"],
            "game": ["game", "play", "игр"],
            "music": ["music", "audio", "song", "музык"],
            "voice": ["voice", "speech", "audio", "голос"],
            "image": ["image", "photo", "picture", "картин"],
            "network": ["network", "vpn", "wifi", "proxy", "internet", "ping"],
            "ai": ["ai", "agent", "learn", "conscious", "emotion", "desire", "dream", "personality"],
            "security": ["security", "moderation", "error", "trash", "frozen", "protect"],
            "utils": ["utils", "progress", "format", "helper"],
            "database": ["database", "json", "save", "load", "data"],
            "creativity": ["creativ", "poem", "story", "aphorism"],
            "sleep": ["sleep", "fatigue", "tired", "сон"],
            "weather": ["weather", "погод"],
            "holiday": ["holiday", "праздн"],
        }
        
        found_keywords = {}
        content_lower = content.lower()
        
        for category, words in keywords.items():
            count = sum(1 for word in words if word in content_lower)
            if count > 0:
                found_keywords[category] = count
        
        return {
            "filename": filename,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines": len(content.split("\n")),
            "keywords": found_keywords,
        }
    except Exception:
        return None


def decide_folder_name(file_info):
    """Систмка сама решает в какую папку положить файл"""
    if not file_info or not file_info.get("keywords"):
        return None
    
    sorted_keywords = sorted(
        file_info["keywords"].items(), key=lambda x: x[1], reverse=True
    )
    
    if sorted_keywords:
        return sorted_keywords[0][0]
    
    return None


def decide_folder_structure():
    """Систмка придумывает структуру папок"""
    folders = {}
    
    for filename in os.listdir("."):
        if (
            filename.endswith(".py")
            and not filename.startswith("_")
            and filename != "bot.py"
        ):
            file_info = analyze_file_content(filename)
            if file_info:
                folder = decide_folder_name(file_info)
                if folder:
                    if folder not in folders:
                        folders[folder] = []
                    folders[folder].append(filename)
    
    return folders


def create_folders_and_move():
    """Создать папки и переместить файлы"""
    folders = decide_folder_structure()
    results = {"moved": [], "created_folders": []}
    
    for folder, files in folders.items():
        if not os.path.exists(folder):
            os.makedirs(folder)
            results["created_folders"].append(folder)
        
        init_file = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(f'"""{folder} модули"""\n')
        
        for filename in files:
            target = os.path.join(folder, filename)
            if not os.path.exists(target):
                try:
                    os.rename(filename, target)
                    results["moved"].append(f"{filename} → {folder}/")
                except Exception:
                    pass
    
    return results


def update_imports_for_new_structure():
    """Обновить импорты после перемещения"""
    updates = []
    
    try:
        with open("bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        folders = []
        for item in os.listdir("."):
            if os.path.isdir(item) and item != "trash" and item != "personality_notes":
                if os.path.exists(os.path.join(item, "__init__.py")):
                    folders.append(item)
        
        if folders and "sys.path.insert" not in content:
            folders_list = str(folders)
            path_code = f"""
import sys
# Автоматически добавленные папки
for folder in {folders_list}:
    if os.path.exists(folder):
        sys.path.insert(0, folder)
"""
            if "import os" in content:
                content = content.replace("import os", "import os\n" + path_code, 1)
            else:
                content = path_code + content
            
            with open("bot.py", "w", encoding="utf-8") as f:
                f.write(content)
            updates.append("bot.py обновлён с путями к папкам")
    except Exception:
        pass
    
    try:
        with open("auto_import.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        folders = []
        for item in os.listdir("."):
            if os.path.isdir(item) and item != "trash" and item != "personality_notes":
                if os.path.exists(os.path.join(item, "__init__.py")):
                    folders.append(item)
        
        if folders and "FOLDERS = " not in content:
            folders_list = str(folders)
            folders_code = f"\nFOLDERS = {folders_list}\n"
            content = content.replace("MODULES_FILE", folders_code + "MODULES_FILE", 1)
            
            with open("auto_import.py", "w", encoding="utf-8") as f:
                f.write(content)
            updates.append("auto_import.py обновлён с папками")
    except Exception:
        pass
    
    return updates


def auto_organize():
    """Автоматическая организация — полный цикл"""
    results = {
        "moved": [],
        "created_folders": [],
        "import_updates": [],
    }
    
    move_results = create_folders_and_move()
    results["moved"] = move_results["moved"]
    results["created_folders"] = move_results["created_folders"]
    
    results["import_updates"] = update_imports_for_new_structure()
    
    return results


def find_large_files(max_size_kb=100):
    """Найти большие файлы"""
    large = []
    
    for root, dirs, files in os.walk("."):
        if "trash" in root or "personality_notes" in root:
            continue
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                try:
                    size = os.path.getsize(filepath)
                    if size > max_size_kb * 1024:
                        large.append({
                            "file": filename,
                            "path": filepath,
                            "size_kb": size // 1024,
                        })
                except Exception:
                    pass
    
    return large


def format_organization_report():
    """Форматировать отчёт об организации"""
    lines = []
    
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk("."):
        if "trash" in root or "personality_notes" in root:
            continue
        for filename in files:
            if filename.endswith(".py"):
                total_files += 1
                try:
                    total_size += os.path.getsize(os.path.join(root, filename))
                except Exception:
                    pass
    
    lines.append(f"📁 Всего файлов: {total_files}")
    lines.append(f"💾 Общий размер: {total_size // 1024}KB")
    
    folders = []
    for item in os.listdir("."):
        if os.path.isdir(item) and item != "trash" and item != "personality_notes":
            if os.path.exists(os.path.join(item, "__init__.py")):
                count = len([f for f in os.listdir(item) if f.endswith(".py")])
                folders.append(f"  📂 {item}: {count} файлов")
    
    if folders:
        lines.append("\nПапки:")
        lines.extend(folders)
    
    large = find_large_files(100)
    if large:
        lines.append("\n⚠️ Большие файлы:")
        for lf in large:
            lines.append(f"  • {lf['file']} ({lf['size_kb']}KB)")
    
    return "\n".join(lines)