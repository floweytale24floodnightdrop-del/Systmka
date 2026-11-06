"""ЯДРО стража ошибок — перехват импорта, разморозка, оркестрация"""

import os
import sys
import json
import time
import hashlib
import threading
import traceback
import builtins
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ ПОДМОДУЛЕЙ
# ============================================================

from error_common import (
    safe_print,
    ensure_stdout,
    is_stdin_available,
    is_ignored_module,
    SKIP_UNFREEZE,
    IGNORED_MODULES,
)

from error_analyzer_ai import (
    analyze_error_with_ai,
    format_error_report,
)

from error_dialog import (
    register_telegram_bot,
    is_telegram_available,
    ask_owner_console,
    ask_owner_telegram,
    process_guardian_callback,
)

from error_fixer_ai import (
    handle_module_error,
    freeze_module,
    try_fix_via_ai,
    set_guardian_data,
    check_on_other_python,
)

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

ERROR_GUARDIAN_FILE = "error_guardian_data.json"
FROZEN_MODULES_FILE = "frozen_modules.json"

ACTIVATE_IMPORT_HOOK = True
ACTIVATE_RUNTIME_LOOP = True
RUNTIME_LOOP_INTERVAL = 60

# ============================================================
# 3. ДАННЫЕ
# ============================================================

guardian_data = {
    "errors": [],
    "frozen_modules": [],
    "fix_history": [],
    "routed_modules": [],
    "stats": {
        "total_errors": 0,
        "fixed_errors": 0,
        "failed_fixes": 0,
        "frozen_modules": 0,
        "analyzed_errors": 0,
        "auto_fixed": 0,
        "unfrozen_at_startup": 0,
        "ignored_modules": 0,
        "asked_owner": 0,
        "routed_to_other_version": 0,
    },
}

set_guardian_data(guardian_data)

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_guardian_data():
    try:
        with open(ERROR_GUARDIAN_FILE, "w", encoding="utf-8") as f:
            json.dump(guardian_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"⚠️ Ошибка сохранения стража: {e}")
        return False


def load_guardian_data():
    global guardian_data
    try:
        if os.path.exists(ERROR_GUARDIAN_FILE):
            with open(ERROR_GUARDIAN_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ["errors", "frozen_modules", "fix_history", "routed_modules"]:
                    if isinstance(loaded.get(key), list):
                        guardian_data[key] = loaded[key]
                
                if isinstance(loaded.get("stats"), dict):
                    guardian_data["stats"].update(loaded["stats"])
        return True
    except json.JSONDecodeError as e:
        safe_print(f"⚠️ Битый JSON стража: {e}")
        return False
    except Exception as e:
        safe_print(f"⚠️ Ошибка загрузки стража: {e}")
        return False


def save_shared_frozen_modules(modules):
    try:
        data = {
            "modules": modules,
            "last_update": datetime.now().isoformat(),
            "checked_at": datetime.now().isoformat(),
            "source": "error_guardian",
        }
        with open(FROZEN_MODULES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"⚠️ Ошибка сохранения frozen_modules: {e}")
        return False

# ============================================================
# 5. ПОЛНАЯ РАЗМОРОЗКА ПРИ СТАРТЕ
# ============================================================

def unfreeze_all_at_startup():
    """ПОЛНАЯ очистка списка замороженных модулей"""
    count = 0
    
    try:
        if os.path.exists(FROZEN_MODULES_FILE):
            with open(FROZEN_MODULES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    count = len(data.get("modules", []))
                elif isinstance(data, list):
                    count = len(data)
    except Exception:
        pass
    
    safe_print("\n" + "=" * 60)
    safe_print("🔄 ПОЛНАЯ РАЗМОРОЗКА МОДУЛЕЙ ПРИ СТАРТЕ")
    safe_print("=" * 60)
    safe_print(f"   Было заморожено: {count} записей")
    safe_print(f"   Очищаю список...")
    
    guardian_data["frozen_modules"] = []
    guardian_data["stats"]["frozen_modules"] = 0
    guardian_data["stats"]["unfrozen_at_startup"] = count
    save_guardian_data()
    save_shared_frozen_modules([])
    
    safe_print(f"   ✅ Разморожено: {count} записей")
    safe_print(f"   📦 frozen_modules.json теперь пуст")
    safe_print("=" * 60 + "\n")
    
    return count

# ============================================================
# 6. ПЕРЕХВАТ ОШИБОК ИМПОРТА
# ============================================================

class ImportErrorGuardian:
    """Перехватчик ошибок импорта с интерактивным диалогом и маршрутизацией"""
    
    def __init__(self):
        self.import_errors = []
        self.frozen_modules = []
        self.routed_modules = []
        self.import_hook_active = False
        self.original_import = None
        self.dialog_lock = threading.Lock()
    
    def activate(self):
        if self.import_hook_active:
            return True
        
        self.import_hook_active = True
        safe_print("🛡️ Страж ошибок (импорт) активирован")
        
        self.original_import = builtins.__import__
        original = self.original_import
        
        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            try:
                return original(name, globals, locals, fromlist, level)
            
            except (ImportError, ModuleNotFoundError) as e:
                ensure_stdout()
                error_msg = str(e)
                tb = traceback.format_exc()
                
                if is_ignored_module(name):
                    return self.create_fallback(name)
                
                if name in SKIP_UNFREEZE:
                    safe_print(f"⚠️ SKIP_UNFREEZE: {name} — {error_msg[:80]}")
                    return self.create_fallback(name)
                
                if "No module named" in error_msg:
                    return self.create_fallback(name)
                
                if "I/O operation" in error_msg or "closed file" in error_msg:
                    return self.create_fallback(name)
                
                with self.dialog_lock:
                    if name in self.frozen_modules:
                        return self.create_fallback(name)
                    
                    if name in self.routed_modules:
                        return self.create_fallback(name)
                    
                    safe_print(f"\n❌ Страж: ошибка импорта '{name}'")
                    
                    action = handle_module_error(name, error_msg, tb)
                    
                    if action == "routed_to_other_version":
                        self.routed_modules.append(name)
                        guardian_data["routed_modules"].append(name)
                        guardian_data["stats"]["routed_to_other_version"] = (
                            guardian_data["stats"].get("routed_to_other_version", 0) + 1
                        )
                        save_guardian_data()
                        safe_print(f"   🔄 Модуль '{name}' маршрутизирован на другую версию")
                    elif action == "freeze":
                        self.frozen_modules.append(name)
                    
                    return self.create_fallback(name)
            
            except SyntaxError as e:
                ensure_stdout()
                error_msg = str(e)
                tb = traceback.format_exc()
                
                if is_ignored_module(name):
                    return self.create_fallback(name)
                
                with self.dialog_lock:
                    if name in self.frozen_modules or name in self.routed_modules:
                        return self.create_fallback(name)
                    
                    safe_print(f"\n❌ Страж: SyntaxError в '{name}'")
                    
                    action = handle_module_error(name, error_msg, tb)
                    
                    if action == "routed_to_other_version":
                        self.routed_modules.append(name)
                        guardian_data["routed_modules"].append(name)
                        save_guardian_data()
                    elif action == "freeze":
                        self.frozen_modules.append(name)
                    
                    return self.create_fallback(name)
            
            except Exception as e:
                ensure_stdout()
                error_msg = str(e)
                tb = traceback.format_exc()
                
                if is_ignored_module(name):
                    return self.create_fallback(name)
                
                if name in SKIP_UNFREEZE:
                    return self.create_fallback(name)
                
                if "I/O operation" in error_msg or "closed file" in error_msg:
                    return self.create_fallback(name)
                
                with self.dialog_lock:
                    if name in self.frozen_modules or name in self.routed_modules:
                        return self.create_fallback(name)
                    
                    safe_print(f"\n❌ Страж: {type(e).__name__} в '{name}'")
                    
                    action = handle_module_error(name, error_msg, tb)
                    
                    if action == "routed_to_other_version":
                        self.routed_modules.append(name)
                        guardian_data["routed_modules"].append(name)
                        save_guardian_data()
                    elif action == "freeze":
                        self.frozen_modules.append(name)
                    
                    return self.create_fallback(name)
        
        builtins.__import__ = guarded_import
        return True
    
    def create_fallback(self, name):
        if name in sys.modules:
            existing = sys.modules[name]
            if hasattr(existing, "__class__") and existing.__class__.__name__ == "FallbackModule":
                return existing
        
        class FallbackModule:
            def __getattr__(self, attr):
                return None
        
        fallback = FallbackModule()
        sys.modules[name] = fallback
        return fallback

# ============================================================
# 7. РАНТАЙМ-ЦИКЛ
# ============================================================

IGNORED_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "trash", "personality_notes", "prompt_notes",
    "error_backups", "error_guardian_backups", "debug_logs",
    "auto_improve_backups", "temp_music", "voice_clones",
    "systmka_voice_clones", "systmka_music", "systmka_media",
    "systmka_generation", "leaks", "venv_gtts",
}


def detect_runtime_errors():
    errors = []
    log_files = ["bot.log", "boot.log", "error.log"]
    error_keywords = [
        "Error", "Exception", "Traceback", "NameError",
        "ImportError", "KeyError", "AttributeError",
        "TypeError", "ModuleNotFoundError", "FileNotFoundError",
        "SyntaxError", "ValueError", "RuntimeError", "IndexError",
    ]
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            continue
        
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-100:]
            
            for line in lines:
                if any(word in line for word in error_keywords):
                    error_hash = hashlib.md5(line.encode()).hexdigest()
                    
                    if error_hash not in [e.get("hash", "") for e in guardian_data["errors"]]:
                        errors.append({
                            "file": log_file,
                            "type": "RuntimeError",
                            "message": line.strip()[:200],
                            "hash": error_hash,
                            "timestamp": datetime.now().isoformat(),
                            "status": "detected",
                        })
        except Exception:
            pass
    
    return errors


def guardian_loop():
    while True:
        try:
            time.sleep(RUNTIME_LOOP_INTERVAL)
            ensure_stdout()
            
            errors = detect_runtime_errors()
            if not errors:
                continue
            
            new_errors = [
                e for e in errors
                if e.get("hash", "") not in [x.get("hash", "") for x in guardian_data["errors"]]
            ]
            
            if not new_errors:
                continue
            
            for err in new_errors:
                guardian_data["errors"].append(err)
                guardian_data["stats"]["total_errors"] += 1
            
            save_guardian_data()
        
        except Exception as e:
            safe_print(f"⚠️ Ошибка в guardian_loop: {e}")
            time.sleep(30)


def start_guardian():
    thread = threading.Thread(target=guardian_loop, daemon=True)
    thread.start()
    safe_print("🛡️ Страж ошибок (рантайм) запущен")
    return thread

# ============================================================
# 8. СТАТИСТИКА
# ============================================================

def get_guardian_stats():
    return {
        "total_errors": guardian_data["stats"]["total_errors"],
        "fixed_errors": guardian_data["stats"]["fixed_errors"],
        "failed_fixes": guardian_data["stats"]["failed_fixes"],
        "frozen_modules": guardian_data["stats"]["frozen_modules"],
        "analyzed_errors": guardian_data["stats"]["analyzed_errors"],
        "auto_fixed": guardian_data["stats"]["auto_fixed"],
        "unfrozen_at_startup": guardian_data["stats"].get("unfrozen_at_startup", 0),
        "routed_to_other_version": guardian_data["stats"].get("routed_to_other_version", 0),
        "frozen_list": guardian_data["frozen_modules"],
        "routed_list": guardian_data.get("routed_modules", []),
    }


def format_guardian_stats():
    stats = get_guardian_stats()
    lines = [
        "🛡️ СТАТИСТИКА СТРАЖА:",
        f"  📊 Всего ошибок: {stats['total_errors']}",
        f"  ✅ Исправлено: {stats['fixed_errors']}",
        f"  ❌ Не исправлено: {stats['failed_fixes']}",
        f"  ❄️ Заморожено модулей: {stats['frozen_modules']}",
        f"  🔄 Маршрутизировано: {stats['routed_to_other_version']}",
        f"  🔬 Проанализировано: {stats['analyzed_errors']}",
        f"  🤖 Автоисправлено: {stats['auto_fixed']}",
        f"  🔄 Разморожено при старте: {stats['unfrozen_at_startup']}",
    ]
    if stats["frozen_list"]:
        preview = stats["frozen_list"][:10]
        lines.append(f"❄️ Замороженные: {', '.join(preview)}")
    if stats["routed_list"]:
        preview = stats["routed_list"][:10]
        lines.append(f"🔄 Маршрутизированные: {', '.join(preview)}")
    return "\n".join(lines)

# ============================================================
# 9. АКТИВАЦИЯ
# ============================================================

ensure_stdout()
load_guardian_data()

safe_print("\n" + "=" * 60)
safe_print("🛡️ ЗАПУСК СТРАЖА ОШИБОК")
safe_print("=" * 60)

unfrozen_count = unfreeze_all_at_startup()

import_guardian = ImportErrorGuardian()

if ACTIVATE_IMPORT_HOOK:
    import_guardian.activate()
else:
    safe_print("🛡️ Страж: перехват импорта отключён")

if ACTIVATE_RUNTIME_LOOP:
    start_guardian()

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

safe_print("\n" + "=" * 60)
safe_print("🛡️ СТРАЖ ОШИБОК АКТИВЕН")
safe_print(f"🔄 Разморожено при старте: {unfrozen_count}")
safe_print(f"❄️ Заморожено сейчас: {len(guardian_data['frozen_modules'])}")
safe_print(f"🔄 Маршрутизировано: {len(guardian_data.get('routed_modules', []))}")
safe_print(f"📱 Telegram: {'✅' if is_telegram_available() else '❌ (не зарегистрирован)'}")
safe_print(f"💻 Консоль: {'✅' if is_stdin_available() else '❌'}")

# Проверка маршрутизации версий
try:
    from smart_import import get_available_versions, CURRENT_VERSION_STR
    _versions = get_available_versions()
    safe_print(f"🐍 Текущая версия: {CURRENT_VERSION_STR}")
    safe_print(f"🔄 Доступные версии: {', '.join(_versions)}")
    if len(_versions) >= 2:
        safe_print(f"✅ Маршрутизация: доступна")
    else:
        safe_print(f"⚠️ Маршрутизация: недоступна (нужно 2 версии)")
except ImportError:
    safe_print(f"⚠️ smart_import не найден — маршрутизация отключена")

safe_print("=" * 60 + "\n")

# ============================================================
# 11. ЭКСПОРТ
# ============================================================

__all__ = [
    "guardian_data",
    "save_guardian_data",
    "load_guardian_data",
    "unfreeze_all_at_startup",
    "get_guardian_stats",
    "format_guardian_stats",
    "register_telegram_bot",
    "is_telegram_available",
    "process_guardian_callback",
    "handle_module_error",
    "freeze_module",
    "try_fix_via_ai",
    "check_on_other_python",
    "safe_print",
    "ensure_stdout",
]