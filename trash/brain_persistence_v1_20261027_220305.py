"""
brain_persistence.py — Сохранение и загрузка состояния мозга.

ИСПРАВЛЕНО:
- Первое сохранение — сразу (без дебаунса)
- Гарантированное сохранение при старте
- Диагностика ошибок
- Проверка размера файла
"""

import os
import json
import time
import random
import threading
from datetime import datetime

from brain_core import brain


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

BRAIN_STATE_FILE = "brain_state.json"
BRAIN_BACKUP_FILE = "brain_state.backup.json"

AUTO_SAVE_INTERVAL = 60
MAX_BACKUPS = 5

BACKUP_DIR = "brain_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)


# ============================================================
# 2. СОХРАНЕНИЕ
# ============================================================

def save_brain_state(filename=None):
    """
    Сохранить состояние мозга в JSON.
    
    Returns:
        bool: успех
    """
    if filename is None:
        filename = BRAIN_STATE_FILE
    
    try:
        data = brain.to_dict()
        data["saved_at"] = datetime.now().isoformat()
        data["version"] = "1.0"
        
        temp_file = filename + ".tmp"
        
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Проверяем, что файл создан и не пустой
        if not os.path.exists(temp_file):
            print(f"❌ Временный файл не создан: {temp_file}")
            return False
        
        size = os.path.getsize(temp_file)
        if size < 100:
            print(f"❌ Временный файл слишком маленький: {size} байт")
            try:
                os.remove(temp_file)
            except Exception:
                pass
            return False
        
        # Атомарная замена
        os.replace(temp_file, filename)
        
        # Проверяем результат
        if os.path.exists(filename):
            final_size = os.path.getsize(filename)
            print(f"💾 Мозг сохранён: {final_size} байт ({len(brain.variables)} переменных)")
            return True
        else:
            print(f"❌ Файл не создан после replace: {filename}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка сохранения мозга: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_backup():
    """Создать бэкап текущего состояния."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"brain_{timestamp}.json")
        
        data = brain.to_dict()
        data["saved_at"] = datetime.now().isoformat()
        data["backup"] = True
        
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        _cleanup_old_backups()
        return backup_file
    except Exception as e:
        print(f"⚠️ Ошибка бэкапа: {e}")
        return None


def _cleanup_old_backups():
    """Удалить старые бэкапы."""
    try:
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith("brain_") and f.endswith(".json")],
            reverse=True
        )
        for old in backups[MAX_BACKUPS:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except Exception:
                pass
    except Exception:
        pass


# ============================================================
# 3. ЗАГРУЗКА
# ============================================================

def load_brain_state(filename=None):
    """
    Загрузить состояние мозга из JSON.
    
    Returns:
        bool: успех
    """
    if filename is None:
        filename = BRAIN_STATE_FILE
    
    print(f"🔍 Загрузка мозга: {filename}")
    
    # Пробуем основной файл
    if os.path.exists(filename):
        print(f"📁 Файл существует: {filename} ({os.path.getsize(filename)} байт)")
        if _try_load(filename):
            return True
    else:
        print(f"📁 Файл не существует: {filename}")
    
    # Пробуем бэкап
    if os.path.exists(BRAIN_BACKUP_FILE):
        print(f"🔄 Пробую бэкап: {BRAIN_BACKUP_FILE}")
        if _try_load(BRAIN_BACKUP_FILE):
            return True
    
    # Пробуем последний бэкап из папки
    try:
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")],
            reverse=True
        )
        for backup in backups[:3]:
            backup_path = os.path.join(BACKUP_DIR, backup)
            print(f"🔄 Пробую бэкап: {backup}")
            if _try_load(backup_path):
                print(f"✅ Восстановлено из бэкапа: {backup}")
                return True
    except Exception:
        pass
    
    print("⚠️ Не удалось загрузить состояние мозга — начинаем с нуля")
    return False


def _try_load(filename):
    """Попытаться загрузить файл."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            print(f"⚠️ {filename}: не словарь")
            return False
        
        brain.load_from_dict(data)
        print(f"✅ Мозг загружен из {filename}")
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON {filename}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {filename}: {e}")
        return False


# ============================================================
# 4. АВТОСОХРАНЕНИЕ
# ============================================================

_save_lock = threading.Lock()
_last_save_time = 0.0
_pending_save = False
_saver_running = False
_first_save_done = False


def schedule_save():
    """Запланировать сохранение."""
    global _pending_save
    _pending_save = True


def _flush_save():
    """
    Сохранить, если нужно.
    
    ИСПРАВЛЕНО: первое сохранение — сразу, без дебаунса.
    """
    global _last_save_time, _pending_save, _first_save_done
    
    if not _pending_save:
        return False
    
    now = time.time()
    
    # === ПЕРВОЕ СОХРАНЕНИЕ — СРАЗУ ===
    if not _first_save_done:
        with _save_lock:
            _pending_save = False
            _last_save_time = now
            _first_save_done = True
        
        print("💾 Первое сохранение мозга (принудительное)...")
        success = save_brain_state()
        
        if success:
            print(f"✅ Мозг сохранён: {len(brain.variables)} переменных")
        else:
            print("❌ Не удалось сохранить мозг при первом сохранении")
        
        return success
    
    # === ОСТАЛЬНЫЕ — С ДЕБАУНСОМ ===
    if now - _last_save_time < AUTO_SAVE_INTERVAL:
        return False
    
    with _save_lock:
        _pending_save = False
        _last_save_time = now
        
        save_brain_state()
        
        if random.random() < 0.1:
            save_backup()
        
        return True


def _saver_loop():
    """Фоновый цикл сохранения."""
    global _saver_running
    
    print("💾 Фоновый цикл сохранения запущен")
    
    while _saver_running:
        time.sleep(10)
        try:
            _flush_save()
        except Exception as e:
            print(f"⚠️ Ошибка в saver_loop: {e}")
    
    print("💾 Фоновый цикл сохранения остановлен")


def start_auto_save():
    """Запустить автосохранение."""
    global _saver_running
    
    if _saver_running:
        return
    
    _saver_running = True
    thread = threading.Thread(target=_saver_loop, daemon=True, name="brain_saver")
    thread.start()
    print(f"💾 Автосохранение мозга запущено (дебаунс {AUTO_SAVE_INTERVAL}с)")


def stop_auto_save():
    """Остановить автосохранение."""
    global _saver_running
    _saver_running = False


# ============================================================
# 5. ПОЛНЫЙ ЦИКЛ
# ============================================================

def init_brain_persistence():
    """
    Инициализировать persistence.
    
    ИСПРАВЛЕНО: после загрузки — принудительное первое сохранение.
    """
    print("💾 Инициализация сохранения мозга...")
    
    # Загружаем
    loaded = load_brain_state()
    
    if loaded:
        print(f"✅ Мозг восстановлен: {len(brain.variables)} переменных")
    else:
        print(f"🆕 Новый мозг: {len(brain.variables)} переменных")
    
    # Запускаем автосохранение
    start_auto_save()
    
    # ИСПРАВЛЕНО: принудительное первое сохранение
    print("💾 Принудительное первое сохранение...")
    global _first_save_done
    _first_save_done = True
    success = save_brain_state()
    
    if success:
        print(f"✅ Первое сохранение успешно: {len(brain.variables)} переменных")
    else:
        print("❌ Первое сохранение не удалось!")
    
    return loaded


# ============================================================
# 6. ПРИНУДИТЕЛЬНОЕ СОХРАНЕНИЕ
# ============================================================

def force_save():
    """Принудительно сохранить мозг."""
    print("💾 Принудительное сохранение мозга...")
    
    success = save_brain_state()
    
    if success:
        print(f"✅ Мозг сохранён: {len(brain.variables)} переменных")
    else:
        print("❌ Не удалось сохранить мозг")
    
    return success


# ============================================================
# 7. СТАТИСТИКА
# ============================================================

def get_persistence_stats():
    """Статистика сохранения."""
    stats = {
        "main_file_exists": os.path.exists(BRAIN_STATE_FILE),
        "main_file_size_kb": 0,
        "main_file_path": os.path.abspath(BRAIN_STATE_FILE),
        "backup_count": 0,
        "last_save": None,
    }
    
    if os.path.exists(BRAIN_STATE_FILE):
        try:
            stats["main_file_size_kb"] = round(
                os.path.getsize(BRAIN_STATE_FILE) / 1024, 2
            )
            with open(BRAIN_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["last_save"] = data.get("saved_at")
        except Exception:
            pass
    
    try:
        stats["backup_count"] = len([
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("brain_") and f.endswith(".json")
        ])
    except Exception:
        pass
    
    return stats


def format_persistence_stats():
    """Форматировать статистику."""
    stats = get_persistence_stats()
    
    lines = [
        "💾 СТАТИСТИКА СОХРАНЕНИЯ МОЗГА:",
        f"  📁 Основной файл: {'✅' if stats['main_file_exists'] else '❌'}",
        f"  📂 Путь: {stats['main_file_path']}",
        f"  💾 Размер: {stats['main_file_size_kb']}KB",
        f"  📦 Бэкапов: {stats['backup_count']}",
    ]
    
    if stats["last_save"]:
        lines.append(f"  🕐 Последнее: {stats['last_save'][:16]}")
    
    return "\n".join(lines)


# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("💾 brain_persistence загружен")
print(f"📁 Файл: {os.path.abspath(BRAIN_STATE_FILE)}")
print(f"📦 Папка бэкапов: {os.path.abspath(BACKUP_DIR)}")
print(f"⏱ Дебаунс: {AUTO_SAVE_INTERVAL}с")
print(f"💡 Первое сохранение — сразу при старте")