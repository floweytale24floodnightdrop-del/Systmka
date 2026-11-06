"""Запись изменений при отладке"""

import os
import json
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DEBUG_FILE = "debug_changes.json"
MAX_CHANGES = 500

# ============================================================
# 2. ДАННЫЕ
# ============================================================

debug_changes = []

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_changes():
    """Сохранить изменения"""
    try:
        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            json.dump(debug_changes, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения изменений: {e}")
        return False


def load_changes():
    """Загрузить изменения"""
    global debug_changes
    try:
        if os.path.exists(DEBUG_FILE):
            with open(DEBUG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    debug_changes = loaded
        return debug_changes
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON изменений: {e}")
        debug_changes = []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки изменений: {e}")
        debug_changes = []
    return debug_changes

# ============================================================
# 4. ДОБАВЛЕНИЕ ИЗМЕНЕНИЯ
# ============================================================

def add_change(change_type, description, old_value=None, new_value=None, file=None):
    """
    Добавить изменение.
    
    Args:
        change_type: тип ("file_edit", "file_create", "file_delete", "setting_change")
        description: описание
        old_value: старое значение
        new_value: новое значение
        file: путь к файлу
    
    Returns:
        dict: запись об изменении
    """
    if not change_type:
        return None
    
    change = {
        "id": len(debug_changes) + 1,
        "type": change_type,
        "description": (description or "")[:500],
        "old_value": old_value,
        "new_value": new_value,
        "file": file,
        "time": datetime.now().isoformat(),
    }
    
    debug_changes.append(change)
    
    # Ограничиваем
    if len(debug_changes) > MAX_CHANGES:
        debug_changes = debug_changes[-MAX_CHANGES:]
    
    save_changes()
    return change

# ============================================================
# 5. ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ
# ============================================================

def apply_change(change):
    """
    Применить одно изменение.
    
    Returns:
        bool: успех
    """
    if not isinstance(change, dict):
        return False
    
    change_type = change.get("type")
    
    if change_type == "file_edit" or change_type == "file_create":
        file_path = change.get("file")
        content = change.get("new_value")
        
        if not file_path or content is None:
            return False
        
        try:
            # Создаём директорию
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка применения изменения: {e}")
            return False
    
    elif change_type == "file_delete":
        file_path = change.get("file")
        
        if not file_path:
            return False
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка удаления файла: {e}")
            return False
    
    return False


def apply_all_changes():
    """Применить все изменения"""
    applied = 0
    failed = 0
    
    for change in debug_changes:
        if apply_change(change):
            applied += 1
        else:
            failed += 1
    
    return {
        "applied": applied,
        "failed": failed,
        "total": len(debug_changes),
    }

# ============================================================
# 6. УПРАВЛЕНИЕ
# ============================================================

def clear_changes():
    """Очистить все изменения"""
    global debug_changes
    debug_changes = []
    save_changes()
    return True


def get_changes_list():
    """Получить список изменений"""
    return debug_changes


def get_change_by_id(change_id):
    """Найти изменение по ID"""
    if change_id is None:
        return None
    
    for change in debug_changes:
        if change.get("id") == change_id:
            return change
    return None


def remove_change(change_id):
    """Удалить изменение по ID"""
    global debug_changes
    
    if change_id is None:
        return False
    
    for i, change in enumerate(debug_changes):
        if change.get("id") == change_id:
            debug_changes.pop(i)
            save_changes()
            return True
    
    return False

# ============================================================
# 7. СТАТИСТИКА
# ============================================================

def get_changes_stats():
    """Получить статистику изменений"""
    by_type = {}
    
    for change in debug_changes:
        ctype = change.get("type", "unknown")
        by_type[ctype] = by_type.get(ctype, 0) + 1
    
    return {
        "total": len(debug_changes),
        "by_type": by_type,
    }


def format_changes():
    """Форматировать изменения"""
    if not debug_changes:
        return "📝 Нет изменений"
    
    lines = [f"📝 ИЗМЕНЕНИЙ: {len(debug_changes)}", ""]
    
    for change in debug_changes[-20:]:
        cid = change.get("id", "?")
        ctype = change.get("type", "?")
        desc = change.get("description", "")[:60]
        cfile = change.get("file", "")
        
        lines.append(f"#{cid} {ctype}: {desc}")
        if cfile:
            lines.append(f"    📁 {cfile}")
    
    return "\n".join(lines)


def format_changes_stats():
    """Форматировать статистику изменений"""
    stats = get_changes_stats()
    
    lines = [
        "📊 СТАТИСТИКА ИЗМЕНЕНИЙ:",
        f"  📝 Всего: {stats['total']}",
    ]
    
    if stats["by_type"]:
        lines.append("")
        lines.append("  📋 ПО ТИПАМ:")
        for ctype, count in sorted(
            stats["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"    • {ctype}: {count}")
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

load_changes()

print("📝 Модуль изменений загружен (PC)")
print(f"📊 Всего изменений: {len(debug_changes)}")