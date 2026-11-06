"""
brain_persistence.py — Сохранение/загрузка мозга с шифрованием.

ИСПРАВЛЕНО:
- Первое сохранение — сразу
- Шифрование через file_cipher (если включено)
- Гарантированное сохранение при старте
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
BRAIN_STATE_ENCRYPTED = "brain_state.dat"
BRAIN_BACKUP_FILE = "brain_state.backup.json"

AUTO_SAVE_INTERVAL = 60
MAX_BACKUPS = 5

BACKUP_DIR = "brain_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Шифрование (включить/выключить)
USE_ENCRYPTION = True  # ← поменяй на False, если не нужно


# ============================================================
# 2. ШИФРОВАНИЕ
# ============================================================

def _get_cipher():
    """Получить модуль шифрования (если включено)."""
    if not USE_ENCRYPTION:
        return None
    
    try:
        import file_cipher
        return file_cipher
    except ImportError:
        print("⚠️ file_cipher не найден — сохранение без шифрования")
        return None


# ============================================================
# 3. СОХРАНЕНИЕ
# ============================================================

def save_brain_state(filename=None):
    """Сохранить состояние мозга."""
    if filename is None:
        filename = BRAIN_STATE_FILE
    
    try:
        data = brain.to_dict()
        data["saved_at"] = datetime.now().isoformat()
        data["version"] = "1.0"
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        cipher = _get_cipher()
        
        if cipher:
            # Шифруем
            encrypted = cipher.encrypt_text(json_str)
            
            with open(BRAIN_STATE_ENCRYPTED, "w", encoding="utf-8") as f:
                f.write(encrypted)
            
            if os.path.exists(BRAIN_STATE_ENCRYPTED):
                size = os.path.getsize(BRAIN_STATE_ENCRYPTED)
                print(f"💾 Мозг сохранён (зашифрован): {size} байт")
                return True
        else:
            # Без шифрования
            temp_file = filename + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(json_str)
            
            if os.path.exists(temp_file):
                os.replace(temp_file, filename)
                size = os.path.getsize(filename)
                print(f"💾 Мозг сохранён: {size} байт")
                return True
        
        return False
    
    except Exception as e:
        print(f"❌ Ошибка сохранения мозга: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 4. ЗАГРУЗКА
# ============================================================

def load_brain_state(filename=None):
    """Загрузить состояние мозга."""
    if filename is None:
        filename = BRAIN_STATE_FILE
    
    print(f"🔍 Загрузка мозга...")
    
    cipher = _get_cipher()
    
    # Пробуем зашифрованный
    if cipher and os.path.exists(BRAIN_STATE_ENCRYPTED):
        try:
            with open(BRAIN_STATE_ENCRYPTED, "r", encoding="utf-8") as f:
                encrypted = f.read()
            
            decrypted = cipher.decrypt_text(encrypted)
            data = json.loads(decrypted)
            
            if isinstance(data, dict):
                brain.load_from_dict(data)
                print(f"✅ Мозг загружен (расшифрован): {len(brain.variables)} переменных")
                return True
        except Exception as e:
            print(f"⚠️ Ошибка расшифровки: {e}")
    
    # Пробуем обычный
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                brain.load_from_dict(data)
                print(f"✅ Мозг загружен: {len(brain.variables)} переменных")
                return True
        except Exception as e:
            print(f"⚠️ Ошибка загрузки: {e}")
    
    # Бэкапы
    try:
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")],
            reverse=True
        )
        for backup in backups[:3]:
            backup_path = os.path.join(BACKUP_DIR, backup)
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    brain.load_from_dict(data)
                    print(f"✅ Восстановлено из бэкапа: {backup}")
                    return True
            except Exception:
                pass
    except Exception:
        pass
    
    print("⚠️ Не удалось загрузить — начинаем с нуля")
    return False


# ============================================================
# 5. АВТОСОХРАНЕНИЕ
# ============================================================

_save_lock = threading.Lock()
_last_save_time = 0.0
_pending_save = False
_saver_running = False
_first_save_done = False


def schedule_save():
    global _pending_save
    _pending_save = True


def _flush_save():
    global _last_save_time, _pending_save, _first_save_done
    
    if not _pending_save:
        return False
    
    now = time.time()
    
    if not _first_save_done:
        with _save_lock:
            _pending_save = False
            _last_save_time = now
            _first_save_done = True
        
        print("💾 Первое сохранение...")
        return save_brain_state()
    
    if now - _last_save_time < AUTO_SAVE_INTERVAL:
        return False
    
    with _save_lock:
        _pending_save = False
        _last_save_time = now
        return save_brain_state()


def _saver_loop():
    global _saver_running
    
    print("💾 Фоновый цикл сохранения запущен")
    
    while _saver_running:
        time.sleep(10)
        try:
            _flush_save()
        except Exception as e:
            print(f"⚠️ Ошибка в saver_loop: {e}")


def start_auto_save():
    global _saver_running
    
    if _saver_running:
        return
    
    _saver_running = True
    thread = threading.Thread(target=_saver_loop, daemon=True, name="brain_saver")
    thread.start()
    print(f"💾 Автосохранение запущено")


def stop_auto_save():
    global _saver_running
    _saver_running = False


# ============================================================
# 6. ИНИЦИАЛИЗАЦИЯ
# ============================================================

def init_brain_persistence():
    """Инициализировать persistence."""
    print("💾 Инициализация сохранения мозга...")
    
    loaded = load_brain_state()
    
    start_auto_save()
    
    # Принудительное первое сохранение
    global _first_save_done
    _first_save_done = True
    save_brain_state()
    
    return loaded


# ============================================================
# 7. ПРИНУДИТЕЛЬНОЕ СОХРАНЕНИЕ
# ============================================================

def force_save():
    """Принудительно сохранить."""
    print("💾 Принудительное сохранение...")
    return save_brain_state()


# ============================================================
# 8. СТАТИСТИКА
# ============================================================

def get_persistence_stats():
    """Статистика."""
    stats = {
        "encrypted_exists": os.path.exists(BRAIN_STATE_ENCRYPTED),
        "encrypted_size_kb": 0,
        "plain_exists": os.path.exists(BRAIN_STATE_FILE),
        "plain_size_kb": 0,
        "backup_count": 0,
        "encryption": USE_ENCRYPTION,
    }
    
    if stats["encrypted_exists"]:
        stats["encrypted_size_kb"] = round(
            os.path.getsize(BRAIN_STATE_ENCRYPTED) / 1024, 2
        )
    
    if stats["plain_exists"]:
        stats["plain_size_kb"] = round(
            os.path.getsize(BRAIN_STATE_FILE) / 1024, 2
        )
    
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
        "💾 СТАТИСТИКА СОХРАНЕНИЯ:",
        f"  🔐 Шифрование: {'✅' if stats['encryption'] else '❌'}",
        f"  📁 Зашифрованный: {'✅' if stats['encrypted_exists'] else '❌'} ({stats['encrypted_size_kb']}KB)",
        f"  📁 Обычный: {'✅' if stats['plain_exists'] else '❌'} ({stats['plain_size_kb']}KB)",
        f"  📦 Бэкапов: {stats['backup_count']}",
    ]
    
    return "\n".join(lines)


# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("💾 brain_persistence загружен")
print(f"🔐 Шифрование: {'✅' if USE_ENCRYPTION else '❌'}")