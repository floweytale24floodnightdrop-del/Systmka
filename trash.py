"""Корзина для файлов — сохраняет СТАРУЮ версию ДО изменения"""

import os
import json
import shutil
import hashlib
import threading
import time
import ast
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

TRASH_DIR = "trash"
TRASH_INFO_FILE = "trash_info.json"
MAX_TRASH_SIZE_MB = 100
MAX_TRASH_FILES = 200
AUTO_CLEANUP_INTERVAL = 3600

# Системные файлы — НЕ трогаем, НЕ бэкапим
SYSTEM_FILES = {
    # Ядро
    "bot.py", "config.py", "config_network.py", "database.py",
    "system_prompt.py", "auto_import.py", "import_core.py",
    "import_modules.py", "import_loader.py",
    
    # Ошибки и защита
    "error_fixer.py", "error_analyzer.py", "error_analyzer_advanced.py",
    "error_reporter.py", "error_guardian.py", "module_fixer.py",
    "trash.py", "log_manager.py", "debug_changes.py",
    
    # Бот-обвязка
    "bot_handlers.py", "bot_loops.py", "bot_startup.py",
    "message_processor.py", "auto_start.py",
    
    # ИИ-ключи (чтобы не сломать)
    "ai_key_rotator.py", "ai_model_manager.py",
    "ai_request_handler.py", "ai_router.py",
    
    # Промты
    "prompt_notes_manager.py",
    
    # Самоулучшение
    "auto_improve.py", "auto_install.py",
}

# ============================================================
# 2. ИНИЦИАЛИЗАЦИЯ
# ============================================================

trash_info = {}
file_versions = {}


def init_trash():
    try:
        if not os.path.exists(TRASH_DIR):
            os.makedirs(TRASH_DIR)
            print(f"🗑 Папка корзины создана: {TRASH_DIR}")
        
        load_trash_info()
        start_cleanup_thread()
        start_watchdog()
        cleanup_expired()
        
        print(f"🗑 Корзина инициализирована (макс: {MAX_TRASH_SIZE_MB}MB, {MAX_TRASH_FILES} файлов)")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации корзины: {e}")
        return False

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_trash_info():
    try:
        with open(TRASH_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(trash_info, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_trash_info():
    global trash_info
    try:
        if os.path.exists(TRASH_INFO_FILE):
            with open(TRASH_INFO_FILE, "r", encoding="utf-8") as f:
                trash_info = json.load(f)
        return True
    except Exception:
        trash_info = {}
        return False

# ============================================================
# 4. ПРОВЕРКА РАБОТОСПОСОБНОСТИ
# ============================================================

def validate_file(file_path):
    if not os.path.exists(file_path):
        return False, "Файл не существует"
    
    if file_path.endswith('.py'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return True, "OK"
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e}"
        except Exception as e:
            return False, f"Ошибка: {e}"
    
    if file_path.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, "OK"
        except json.JSONDecodeError as e:
            return False, f"Некорректный JSON: {e}"
    
    return True, "OK"

# ============================================================
# 5. БЭКАП СТАРОЙ ВЕРСИИ (ДО ИЗМЕНЕНИЯ!)
# ============================================================

def backup_file(file_path, description=None, source="system"):
    """
    Сохранить СТАРУЮ версию файла ДО изменения.
    """
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ Файл не существует: {file_path}")
            return None
        
        # Системные файлы не бэкапим
        if is_system_file(file_path):
            print(f"⚠️ Системный файл не сохраняется: {file_path}")
            return None
        
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        ext = os.path.splitext(file_name)[1]
        
        version = file_versions.get(file_path, 0) + 1
        file_versions[file_path] = version
        
        # Имя бэкапа: original_v1_20260101_120000.py
        backup_name = (
            f"{name_without_ext}_v{version}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        )
        backup_path = os.path.join(TRASH_DIR, backup_name)
        
        # КОПИРУЕМ СТАРУЮ ВЕРСИЮ ДО ИЗМЕНЕНИЯ!
        shutil.copy2(file_path, backup_path)
        
        if not os.path.exists(backup_path):
            print(f"⚠️ Бэкап не создан: {backup_path}")
            return None
        
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        trash_info[backup_name] = {
            'original_file': file_path,
            'backup_time': datetime.now().isoformat(),
            'version': version,
            'source': source,
            'description': description or f"Версия {version} (ДО ИЗМЕНЕНИЯ!)",
            'size': os.path.getsize(backup_path),
            'hash': file_hash,
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
        }
        
        save_trash_info()
        print(f"📂 Бэкап СТАРОЙ версии создан: {backup_name}")
        return backup_path
    
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return None


def backup_file_before_change(file_path, description=None):
    """Сохранить СТАРУЮ версию ДО изменения"""
    return backup_file(file_path, description, source="system")

# ============================================================
# 6. ВОССТАНОВЛЕНИЕ ИЗ БЭКАПА
# ============================================================

def restore_from_backup(file_path):
    """Восстановить СТАРУЮ версию из бэкапа"""
    latest_backup = None
    latest_time = None
    
    for name, info in trash_info.items():
        if info.get('original_file') == file_path:
            backup_time = info.get('backup_time')
            if backup_time:
                try:
                    t = datetime.fromisoformat(backup_time)
                    if latest_time is None or t > latest_time:
                        latest_time = t
                        latest_backup = name
                except Exception:
                    pass
    
    if latest_backup:
        backup_path = os.path.join(TRASH_DIR, latest_backup)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"🔄 Восстановлена СТАРАЯ версия: {latest_backup}")
            return True
    
    print(f"⚠️ Не найден бэкап для {file_path}")
    return False

# ============================================================
# 7. БЕЗОПАСНОЕ ИЗМЕНЕНИЕ
# ============================================================

def safe_change_file(file_path, new_content, description=None, require_permission=True):
    """
    Безопасно изменить файл:
    1. Создать бэкап СТАРОЙ версии
    2. Сохранить новое содержимое
    3. Проверить работоспособность
    4. Если ошибка — откат к СТАРОЙ версии
    """
    if not os.path.exists(file_path):
        return False, "Файл не существует"
    
    # 1. СОХРАНЯЕМ СТАРУЮ ВЕРСИЮ!
    backup_path = backup_file(file_path, description or "Перед изменением", source="system")
    if not backup_path:
        return False, "Не удалось создать бэкап старой версии"
    
    # 2. Сохраняем новое содержимое
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        restore_from_backup(file_path)
        return False, f"Ошибка записи: {e}"
    
    # 3. Проверяем работоспособность
    is_valid, error = validate_file(file_path)
    
    if is_valid:
        print(f"✅ Файл {file_path} успешно изменён")
        return True, "OK"
    else:
        print(f"❌ Файл {file_path} не работает: {error}")
        restore_from_backup(file_path)
        return False, f"Файл не работает: {error}"

# ============================================================
# 8. СИСТЕМНЫЕ ФАЙЛЫ
# ============================================================

def is_system_file(file_path):
    """Проверить, системный ли файл"""
    file_name = os.path.basename(file_path)
    return file_name in SYSTEM_FILES

# ============================================================
# 9. ОЧИСТКА ЛОГОВ
# ============================================================

def clean_logs_now():
    log_files = ["bot.log", "boot.log"]
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                with open(log_file, "r", encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                if len(lines) > 200:
                    with open(log_file, "w", encoding='utf-8') as f:
                        f.writelines(lines[-200:])
                    print(f"✂️ {log_file} обрезан до 200 строк")
        except Exception:
            pass

# ============================================================
# 10. АВТООЧИСТКА
# ============================================================

def cleanup_expired():
    now = datetime.now()
    deleted = []
    
    for name, info in list(trash_info.items()):
        backup_path = os.path.join(TRASH_DIR, name)
        
        if not os.path.exists(backup_path):
            del trash_info[name]
            deleted.append(name)
            continue
        
        expires_at = info.get('expires_at')
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                if now > expires:
                    try:
                        os.remove(backup_path)
                        del trash_info[name]
                        deleted.append(name)
                    except Exception:
                        pass
                    continue
            except Exception:
                pass
    
    if deleted:
        save_trash_info()
        print(f"🗑 Очищено файлов: {len(deleted)}")
    
    return deleted


def cleanup_expired_loop():
    while True:
        time.sleep(AUTO_CLEANUP_INTERVAL)
        try:
            cleanup_expired()
        except Exception:
            pass


def start_cleanup_thread():
    thread = threading.Thread(target=cleanup_expired_loop, daemon=True)
    thread.start()

# ============================================================
# 11. ВАТЧДОГ
# ============================================================

file_watch_history = {}


def watch_files():
    while True:
        time.sleep(10)
        try:
            for root, dirs, files in os.walk("."):
                if any(skip in root for skip in [
                    TRASH_DIR, 'trash', '__pycache__', 'personality_notes'
                ]):
                    continue
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('_'):
                        file_path = os.path.join(root, file)
                        try:
                            if not os.path.exists(file_path):
                                continue
                            
                            with open(file_path, 'rb') as f:
                                current_hash = hashlib.md5(f.read()).hexdigest()
                            
                            if file_path in file_watch_history:
                                if file_watch_history[file_path] != current_hash:
                                    print(f"📝 Обнаружено изменение: {file_path}")
                                    if not is_system_file(file_path):
                                        backup_file(
                                            file_path,
                                            "Автоматический бэкап (ДО ИЗМЕНЕНИЯ)",
                                            source="user"
                                        )
                                    file_watch_history[file_path] = current_hash
                            else:
                                file_watch_history[file_path] = current_hash
                        except Exception:
                            if file_path in file_watch_history:
                                del file_watch_history[file_path]
        except Exception:
            pass


def start_watchdog():
    thread = threading.Thread(target=watch_files, daemon=True)
    thread.start()
    print("👁 Ватчдог файлов запущен")

# ============================================================
# 12. ИНФОРМАЦИЯ О КОРЗИНЕ
# ============================================================

def get_trash_list():
    files = []
    for name, info in trash_info.items():
        files.append({
            'name': name,
            'original': info.get('original_file', '?'),
            'version': info.get('version', 0),
            'source': info.get('source', 'unknown'),
            'description': info.get('description', ''),
            'size': info.get('size', 0),
            'backup_time': info.get('backup_time', ''),
            'expires_at': info.get('expires_at', ''),
        })
    return sorted(files, key=lambda x: x.get('backup_time', ''), reverse=True)


def get_trash_stats():
    total_size = sum(info.get('size', 0) for info in trash_info.values())
    return {
        'total_files': len(trash_info),
        'dir_size': total_size,
        'dir_size_mb': round(total_size / (1024 * 1024), 2),
        'max_files': MAX_TRASH_FILES,
        'max_size_mb': MAX_TRASH_SIZE_MB,
        'versions': len(file_versions)
    }


def format_trash_stats():
    stats = get_trash_stats()
    lines = [
        "🗑 СТАТИСТИКА КОРЗИНЫ:",
        f"📁 Файлов: {stats['total_files']} / {stats['max_files']}",
        f"💾 Размер: {stats['dir_size_mb']}MB / {stats['max_size_mb']}MB",
        f"📦 Версий: {stats['versions']}",
    ]
    usage = stats['total_files'] / stats['max_files'] if stats['max_files'] > 0 else 0
    if usage > 0.8:
        lines.append("⚠️ Корзина почти полна!")
    return "\n".join(lines)


def clear_trash():
    try:
        if os.path.exists(TRASH_DIR):
            for f in os.listdir(TRASH_DIR):
                fp = os.path.join(TRASH_DIR, f)
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
        trash_info.clear()
        save_trash_info()
        return True, "🗑 Корзина полностью очищена"
    except Exception as e:
        return False, f"❌ Ошибка очистки: {e}"

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

init_trash()
print(f"📁 Файлов в корзине: {len(trash_info)}")