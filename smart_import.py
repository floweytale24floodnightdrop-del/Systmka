"""Умный импорт — автоматическая проверка модулей на другой версии Python"""

import os
import sys
import subprocess
import json
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

CURRENT_PYTHON = sys.version_info[:2]
CURRENT_VERSION_STR = f"{CURRENT_PYTHON[0]}.{CURRENT_PYTHON[1]}"

# Доступные версии (для fallback)
AVAILABLE_PYTHONS = {
    "3.14": ["py", "-3.14"],
    "3.12": ["py", "-3.12"],
}

SUBPROCESS_TIMEOUT = 60
CHECK_TIMEOUT = 30

# ============================================================
# 2. ПРОВЕРКА ДОСТУПНОСТИ
# ============================================================

def is_python_available(version):
    """Проверить, доступна ли версия Python"""
    cmd = AVAILABLE_PYTHONS.get(version)
    if not cmd:
        return False
    
    try:
        result = subprocess.run(
            cmd + ["-c", "print('OK')"],
            capture_output=True,
            timeout=10,
            encoding="utf-8",
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False


def get_other_version():
    """
    Получить другую версию Python (не текущую).
    
    Returns:
        str: "3.12" или "3.14"
    """
    if CURRENT_VERSION_STR == "3.14":
        return "3.12"
    elif CURRENT_VERSION_STR == "3.12":
        return "3.14"
    else:
        return "3.12"  # fallback


def get_available_versions():
    """Получить список доступных версий"""
    available = []
    for version in AVAILABLE_PYTHONS:
        if is_python_available(version):
            available.append(version)
    return available

# ============================================================
# 3. ПРОВЕРКА МОДУЛЯ НА ДРУГОЙ ВЕРСИИ
# ============================================================

def check_module_on_other_python(module_name, target_version=None):
    """
    Проверить, работает ли модуль на другой версии Python.
    
    Args:
        module_name: имя модуля
        target_version: "3.12" / "3.14" / None (авто)
    
    Returns:
        tuple: (works: bool, error: str|None)
    """
    if target_version is None:
        target_version = get_other_version()
    
    if not is_python_available(target_version):
        return False, f"{target_version} недоступен"
    
    # Безопасно сериализуем имя модуля
    code = f"""
import sys
try:
    __import__({module_name!r})
    print('OK')
except Exception as e:
    print(f'ERROR: {{type(e).__name__}}: {{e}}')
"""
    
    cmd = AVAILABLE_PYTHONS.get(target_version)
    if not cmd:
        return False, f"{target_version} не в списке"
    
    try:
        result = subprocess.run(
            cmd + ["-c", code],
            capture_output=True,
            timeout=CHECK_TIMEOUT,
            encoding="utf-8",
        )
        
        output = (result.stdout or "").strip()
        
        if output == "OK":
            return True, None
        
        if output.startswith("ERROR:"):
            return False, output[6:].strip()
        
        if result.stderr:
            return False, result.stderr[:200]
        
        return False, "Неизвестный ответ"
    
    except subprocess.TimeoutExpired:
        return False, f"Таймаут ({CHECK_TIMEOUT}с)"
    except Exception as e:
        return False, str(e)[:200]

# ============================================================
# 4. ВЫЗОВ ФУНКЦИИ НА ДРУГОЙ ВЕРСИИ
# ============================================================

def call_on_other_python(module_name, function_name, args=None, kwargs=None, target_version=None):
    """
    Вызвать функцию модуля на другой версии Python.
    
    ВАЖНО: args/kwargs должны быть JSON-сериализуемыми.
    Результат тоже должен быть JSON-сериализуемым.
    
    Returns:
        результат или None
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    if target_version is None:
        target_version = get_other_version()
    
    if not is_python_available(target_version):
        print(f"⚠️ {target_version} недоступен")
        return None
    
    try:
        args_json = json.dumps(args)
        kwargs_json = json.dumps(kwargs)
    except TypeError as e:
        print(f"⚠️ Аргументы не сериализуются: {e}")
        return None
    
    code = f"""
import json
import sys
try:
    module = __import__({module_name!r}, fromlist=[{function_name!r}])
    func = getattr(module, {function_name!r})
    args = json.loads({args_json!r})
    kwargs = json.loads({kwargs_json!r})
    result = func(*args, **kwargs)
    print(json.dumps(result))
except Exception as e:
    print(f'ERROR: {{type(e).__name__}}: {{e}}', file=sys.stderr)
    sys.exit(1)
"""
    
    cmd = AVAILABLE_PYTHONS.get(target_version)
    if not cmd:
        return None
    
    try:
        result = subprocess.run(
            cmd + ["-c", code],
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT,
            encoding="utf-8",
        )
        
        if result.returncode != 0:
            print(f"⚠️ {target_version} ошибка: {(result.stderr or '')[:200]}")
            return None
        
        output = (result.stdout or "").strip()
        if not output:
            return None
        
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output
    
    except subprocess.TimeoutExpired:
        print(f"⚠️ {target_version} таймаут ({SUBPROCESS_TIMEOUT}с)")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка вызова {target_version}: {e}")
        return None

# ============================================================
# 5. УМНЫЙ ВЫЗОВ (АВТОМАТИЧЕСКАЯ МАРШРУТИЗАЦИЯ)
# ============================================================

def smart_call(module_name, function_name, args=None, kwargs=None):
    """
    Вызвать функцию модуля с автоматической маршрутизацией.
    
    Логика:
    1. Пробуем на текущей версии
    2. Если не работает — пробуем на другой
    3. Возвращаем результат или None
    
    Returns:
        результат или None
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    # 1. Пробуем на текущей версии
    try:
        module = __import__(module_name, fromlist=[function_name])
        func = getattr(module, function_name)
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        print(f"⚠️ {module_name}.{function_name} на текущей: {e}")
    
    # 2. Пробуем на другой версии
    other_version = get_other_version()
    print(f"🔄 Пробую на {other_version}...")
    
    result = call_on_other_python(
        module_name, function_name, args, kwargs, other_version
    )
    
    if result is not None:
        print(f"✅ {module_name}.{function_name} сработал на {other_version}")
    
    return result

# ============================================================
# 6. ТЕСТ
# ============================================================

def test_smart_import():
    """Тест"""
    print(f"🐍 Текущая версия: {CURRENT_VERSION_STR}")
    print(f"🔄 Другая версия: {get_other_version()}")
    print(f"📋 Доступные: {get_available_versions()}")
    
    # Тест speedtest
    print("\n🧪 Тест speedtest...")
    works, err = check_module_on_other_python("speedtest")
    print(f"  {get_other_version()}: {'✅' if works else '❌'} {err or ''}")

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🧠 smart_import загружен")
print(f"🐍 Текущая версия: {CURRENT_VERSION_STR}")
print(f"🔄 Другая версия: {get_other_version()}")

_available = get_available_versions()
print(f"📋 Доступные версии: {_available}")

if len(_available) >= 2:
    print(f"✅ Маршрутизация доступна: {' ↔ '.join(_available)}")
else:
    print(f"⚠️ Маршрутизация недоступна (нужно 2 версии, есть {len(_available)})")