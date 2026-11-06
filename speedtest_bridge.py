"""Мост для speedtest — запуск через Python 3.12 (на 3.14 несовместим)"""

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

# Версия для speedtest
SPEEDTEST_PYTHON = "3.12"

# Путь к Python 3.12
PYTHON_312 = ["py", "-3.12"]

# Таймаут
SPEEDTEST_TIMEOUT = 120

# Кэш
_cache = {
    "value": None,
    "time": 0,
}

CACHE_TTL = 300  # 5 минут

# ============================================================
# 2. ПРОВЕРКА ДОСТУПНОСТИ
# ============================================================

def is_speedtest_available():
    """Проверить, доступен ли speedtest через 3.12"""
    if CURRENT_VERSION_STR == SPEEDTEST_PYTHON:
        # Уже на 3.12 — прямой импорт
        try:
            import speedtest
            return True
        except Exception:
            return False
    
    # На 3.14 — проверяем 3.12
    try:
        result = subprocess.run(
            PYTHON_312 + ["-c", "import speedtest; print('OK')"],
            capture_output=True,
            timeout=10,
            encoding="utf-8",
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False

# ============================================================
# 3. ЗАПУСК SPEEDTEST
# ============================================================

def run_speedtest():
    """
    Запустить speedtest (через 3.12, если текущая — 3.14).
    
    Returns:
        dict: {download_mbps, upload_mbps, ping_ms, server, server_country}
        или None
    """
    import time
    
    # Кэш
    now = time.time()
    if _cache["value"] and (now - _cache["time"]) < CACHE_TTL:
        return _cache["value"]
    
    # Если текущая версия — 3.12, прямой вызов
    if CURRENT_VERSION_STR == SPEEDTEST_PYTHON:
        return _run_speedtest_direct()
    
    # Иначе — через subprocess 3.12
    return _run_speedtest_via_312()

# ============================================================
# 4. ПРЯМОЙ ВЫЗОВ (НА 3.12)
# ============================================================

def _run_speedtest_direct():
    """Запустить speedtest напрямую (на 3.12)"""
    try:
        import speedtest
        
        st = speedtest.Speedtest()
        st.get_best_server()
        
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        results = st.results.dict()
        
        result = {
            "download_mbps": round(download, 2),
            "upload_mbps": round(upload, 2),
            "ping_ms": round(results.get("ping", 0), 1),
            "server": results.get("server", {}).get("name", "Unknown"),
            "server_country": results.get("server", {}).get("country", "Unknown"),
        }
        
        import time
        _cache["value"] = result
        _cache["time"] = time.time()
        
        return result
    except Exception as e:
        print(f"⚠️ speedtest ошибка: {e}")
        return None

# ============================================================
# 5. ВЫЗОВ ЧЕРЕЗ 3.12 (SUBEPROCESS)
# ============================================================

def _run_speedtest_via_312():
    """Запустить speedtest через Python 3.12 (subprocess)"""
    # Скрипт для 3.12
    script = """
import json
import sys
try:
    import speedtest
    st = speedtest.Speedtest()
    st.get_best_server()
    download = st.download() / 1_000_000
    upload = st.upload() / 1_000_000
    results = st.results.dict()
    
    result = {
        "download_mbps": round(download, 2),
        "upload_mbps": round(upload, 2),
        "ping_ms": round(results.get("ping", 0), 1),
        "server": results.get("server", {}).get("name", "Unknown"),
        "server_country": results.get("server", {}).get("country", "Unknown"),
    }
    print(json.dumps(result))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
"""
    
    try:
        print("🔄 Запускаю speedtest через Python 3.12...")
        
        result = subprocess.run(
            PYTHON_312 + ["-c", script],
            capture_output=True,
            timeout=SPEEDTEST_TIMEOUT,
            encoding="utf-8",
        )
        
        if result.returncode != 0:
            print(f"⚠️ speedtest 3.12 ошибка: {(result.stderr or '')[:200]}")
            return None
        
        output = (result.stdout or "").strip()
        if not output:
            return None
        
        data = json.loads(output)
        
        import time
        _cache["value"] = data
        _cache["time"] = time.time()
        
        print(f"✅ speedtest 3.12: {data['download_mbps']} Mbps down, {data['upload_mbps']} Mbps up")
        
        return data
    
    except subprocess.TimeoutExpired:
        print(f"⚠️ speedtest 3.12 таймаут ({SPEEDTEST_TIMEOUT}с)")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ speedtest 3.12 неверный JSON: {e}")
        return None
    except Exception as e:
        print(f"⚠️ speedtest 3.12 ошибка: {e}")
        return None

# ============================================================
# 6. ТЕСТ
# ============================================================

def test_speedtest_bridge():
    """Тест моста"""
    print(f"🐍 Текущая версия: {CURRENT_VERSION_STR}")
    print(f"🎯 speedtest версия: {SPEEDTEST_PYTHON}")
    
    available = is_speedtest_available()
    print(f"✅ speedtest доступен: {available}")
    
    if not available:
        return False
    
    print("🧪 Запускаю тест...")
    result = run_speedtest()
    
    if result:
        print(f"✅ Результат: {result}")
        return True
    else:
        print("❌ Не удалось")
        return False

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🌉 speedtest_bridge загружен")
print(f"🐍 Текущая версия: {CURRENT_VERSION_STR}")

if CURRENT_VERSION_STR == SPEEDTEST_PYTHON:
    print(f"✅ speedtest: прямой вызов (уже на {SPEEDTEST_PYTHON})")
else:
    print(f"🔄 speedtest: через Python {SPEEDTEST_PYTHON} (subprocess)")
    if is_speedtest_available():
        print(f"✅ Python {SPEEDTEST_PYTHON}: доступен")
    else:
        print(f"⚠️ Python {SPEEDTEST_PYTHON}: недоступен")