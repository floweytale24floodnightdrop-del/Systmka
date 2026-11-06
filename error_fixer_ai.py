"""Автоисправление модулей через ИИ — анализ, генерация фикса, бэкап, откат"""

import os
import re
import sys
import ast
import json
import time
import shutil
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from error_common import (
    safe_print,
    is_ignored_module,
    is_stdin_available,
    SKIP_UNFREEZE,
    IGNORED_MODULES,
)

from error_analyzer_ai import (
    analyze_error_with_ai,
    format_error_report,
)

from error_dialog import (
    ask_owner_console,
    ask_owner_telegram,
    is_telegram_available,
)

try:
    from config import OPENROUTER_KEY, OPENROUTER_KEYS
except ImportError:
    OPENROUTER_KEY = None
    OPENROUTER_KEYS = []

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

BACKUP_DIR = "error_guardian_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

ERROR_GUARDIAN_FILE = "error_guardian_data.json"
FROZEN_MODULES_FILE = "frozen_modules.json"

MAX_AI_FIX_ATTEMPTS = 3
REQUEST_TIMEOUT = 60

# ============================================================
# 3. ДАННЫЕ
# ============================================================

_guardian_data = None

def set_guardian_data(data):
    """Установить ссылку на guardian_data"""
    global _guardian_data
    _guardian_data = data


def _get_guardian_data():
    """Получить guardian_data"""
    if _guardian_data is not None:
        return _guardian_data
    
    try:
        if os.path.exists(ERROR_GUARDIAN_FILE):
            with open(ERROR_GUARDIAN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    
    return {
        "errors": [],
        "frozen_modules": [],
        "fix_history": [],
        "stats": {},
    }


def _save_guardian_data(data):
    """Сохранить guardian_data"""
    try:
        with open(ERROR_GUARDIAN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"⚠️ Ошибка сохранения: {e}")
        return False

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def _get_openrouter_key():
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 5. ЗАМОРОЗКА
# ============================================================

def freeze_module(module_name):
    """Заморозить модуль"""
    data = _get_guardian_data()
    
    if "frozen_modules" not in data:
        data["frozen_modules"] = []
    
    if module_name not in data["frozen_modules"]:
        data["frozen_modules"].append(module_name)
        
        if "stats" not in data:
            data["stats"] = {}
        data["stats"]["frozen_modules"] = len(data["frozen_modules"])
        
        try:
            save_data = {
                "modules": data["frozen_modules"],
                "last_update": datetime.now().isoformat(),
                "source": "error_fixer_ai",
            }
            with open(FROZEN_MODULES_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        _save_guardian_data(data)
        safe_print(f"   ❄️ Модуль '{module_name}' заморожен")

# ============================================================
# 6. АВТОИСПРАВЛЕНИЕ ЧЕРЕЗ ИИ
# ============================================================

def try_fix_via_ai(module_name, error_text, traceback_text):
    """Попытаться исправить модуль через ИИ"""
    key = _get_openrouter_key()
    if not key:
        safe_print("❌ Нет ключа OpenRouter")
        return False
    
    module_file = f"{module_name.replace('.', '/')}.py"
    if not os.path.exists(module_file):
        module_file = f"{module_name}.py"
    
    if not os.path.exists(module_file):
        safe_print(f"❌ Файл модуля не найден: {module_name}")
        return False
    
    try:
        with open(module_file, "r", encoding="utf-8") as f:
            original_code = f.read()
    except Exception as e:
        safe_print(f"❌ Не удалось прочитать файл: {e}")
        return False
    
    backup_name = (
        f"{os.path.basename(module_file)}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    )
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    try:
        shutil.copy2(module_file, backup_path)
    except Exception:
        pass
    
    try:
        prompt = f"""Модуль '{module_name}' падает при импорте.

ОШИБКА:
{error_text}

TRACEBACK:
{traceback_text[:2000]}

КОД ФАЙЛА (первые 4000 символов):
{original_code[:4000]}

Задача: исправить код так, чтобы он импортировался без ошибок.
Если проблема в отсутствующем модуле — добавь try/except.
Если проблема в синтаксисе — исправь синтаксис.

Верни ПОЛНЫЙ исправленный код файла, без пояснений, без markdown-обёртки.
Только код."""
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по Python. Возвращай только код."
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8000,
                "temperature": 0.2,
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            safe_print(f"❌ ИИ вернул HTTP {response.status_code}")
            return False
        
        data = response.json()
        if 'choices' not in data:
            safe_print("❌ ИИ не вернул ответ")
            return False
        
        fixed_code = data['choices'][0]['message']['content']
        
        fixed_code = fixed_code.strip()
        if fixed_code.startswith("```"):
            lines = fixed_code.split("\n")
            fixed_code = "\n".join(lines[1:])
        if fixed_code.endswith("```"):
            fixed_code = fixed_code[:-3]
        fixed_code = fixed_code.strip()
        
        try:
            ast.parse(fixed_code)
        except SyntaxError as e:
            safe_print(f"❌ ИИ вернул битый код: {e}")
            return False
        
        with open(module_file, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        
        safe_print(f"✅ ИИ исправил файл: {module_file}")
        safe_print(f"   📁 Бэкап: {backup_path}")
        
        data = _get_guardian_data()
        if "stats" not in data:
            data["stats"] = {}
        data["stats"]["auto_fixed"] = data["stats"].get("auto_fixed", 0) + 1
        
        if "fix_history" not in data:
            data["fix_history"] = []
        data["fix_history"].append({
            "module": module_name,
            "file": module_file,
            "backup": backup_path,
            "time": datetime.now().isoformat(),
        })
        
        _save_guardian_data(data)
        return True
    
    except Exception as e:
        safe_print(f"❌ Ошибка автоисправления: {e}")
        return False

# ============================================================
# 7. ПРОВЕРКА НА ДРУГОЙ ВЕРСИИ PYTHON
# ============================================================

def check_on_other_python(module_name):
    """
    Проверить, работает ли модуль на другой версии Python.
    
    Returns:
        tuple: (works: bool, other_version: str, error: str|None)
    """
    try:
        from smart_import import (
            check_module_on_other_python,
            get_other_version,
            is_python_available,
        )
    except ImportError:
        return False, None, "smart_import недоступен"
    
    other_version = get_other_version()
    
    if not is_python_available(other_version):
        return False, other_version, f"{other_version} недоступен"
    
    works, error = check_module_on_other_python(module_name, other_version)
    
    return works, other_version, error

# ============================================================
# 8. ОБРАБОТКА ОШИБКИ МОДУЛЯ (ГЛАВНАЯ)
# ============================================================

def handle_module_error(module_name, error_text, traceback_text="", max_ai_attempts=None):
    """
    Обработать ошибку модуля.
    
    Логика:
    0. НОВОЕ: проверить на другой версии Python
       - Если работает → "routed_to_other_version" (без диалога)
       - Если не работает → диалог
    
    Returns:
        str: "freeze" | "fix" | "stop" | "skip" | "fixed" | "routed_to_other_version"
    """
    if max_ai_attempts is None:
        max_ai_attempts = MAX_AI_FIX_ATTEMPTS
    
    # ============================================================
    # ШАГ 0: ПРОВЕРКА НА ДРУГОЙ ВЕРСИИ
    # ============================================================
    
    safe_print(f"\n🔄 Проверяю '{module_name}' на другой версии Python...")
    
    works_on_other, other_version, other_error = check_on_other_python(module_name)
    
    if works_on_other:
        safe_print(f"✅ Модуль '{module_name}' работает на {other_version}!")
        safe_print(f"   💡 Маршрутизация: {other_version} (не текущая)")
        safe_print(f"   ⚠️ Систмка НЕ может использовать его напрямую")
        safe_print(f"   💡 Только через smart_call() в subprocess")
        return "routed_to_other_version"
    
    if other_error:
        safe_print(f"⚠️ На {other_version} тоже не работает: {other_error}")
    else:
        safe_print(f"⚠️ На {other_version} тоже не работает")
    
    # ============================================================
    # ШАГ 1: АНАЛИЗ ЧЕРЕЗ ИИ
    # ============================================================
    
    safe_print(f"\n🔍 Анализирую ошибку модуля '{module_name}'...")
    analysis = analyze_error_with_ai(module_name, error_text, traceback_text)
    
    report = format_error_report(module_name, error_text, traceback_text, analysis)
    safe_print(report)
    
    # ============================================================
    # ШАГ 2: АВТОИСПРАВЛЕНИЕ ЧЕРЕЗ ИИ
    # ============================================================
    
    safe_print("🔧 Пробую автоисправление через ИИ...")
    if try_fix_via_ai(module_name, error_text, traceback_text):
        safe_print(f"✅ Модуль '{module_name}' исправлен автоматически!")
        
        import builtins
        try:
            original_import = builtins.__import__
            original_import(module_name)
            safe_print(f"✅ Модуль '{module_name}' успешно импортирован")
            return "fixed"
        except Exception as e:
            safe_print(f"⚠️ После исправления всё ещё падает: {e}")
    
    # ============================================================
    # ШАГ 3: ДИАЛОГ С ВЛАДЕЛЬЦЕМ
    # ============================================================
    
    action = None
    
    if is_stdin_available():
        action = ask_owner_console(module_name)
    
    if action is None and is_telegram_available():
        safe_print("📱 Спрашиваю владельца в Telegram...")
        action = ask_owner_telegram(module_name, report)
    
    if action is None:
        safe_print("⚠️ Владелец недоступен — автоматически замораживаю")
        action = "freeze"
    
    # ============================================================
    # ШАГ 4: ВЫПОЛНЕНИЕ
    # ============================================================
    
    if action == "freeze":
        freeze_module(module_name)
        return "freeze"
    
    elif action == "fix":
        safe_print("🔧 Владелец выбрал: исправить через ИИ")
        if try_fix_via_ai(module_name, error_text, traceback_text):
            import builtins
            try:
                original_import = builtins.__import__
                original_import(module_name)
                safe_print("✅ Исправлено! Модуль импортируется")
                return "fixed"
            except Exception as e:
                safe_print(f"❌ Всё ещё падает: {e}")
                freeze_module(module_name)
                return "freeze"
        else:
            freeze_module(module_name)
            return "freeze"
    
    elif action == "stop":
        safe_print("🛑 Владелец выбрал: остановить программу")
        safe_print("💾 Сохраняю данные...")
        data = _get_guardian_data()
        _save_guardian_data(data)
        sys.exit(1)
    
    elif action == "skip":
        safe_print(f"⏭ Модуль '{module_name}' пропущен (не заморожен)")
        return "skip"
    
    return action

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("🛡️ error_fixer_ai загружен")
print(f"🔑 OpenRouter: {'✅' if _get_openrouter_key() else '❌'}")
print(f"📁 Бэкапы: {BACKUP_DIR}/")
print(f"🔄 Маршрутизация версий: ✅")