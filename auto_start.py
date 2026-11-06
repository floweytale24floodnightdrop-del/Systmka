"""Автозапуск Систмки — точка входа (PC-версия)"""

import subprocess
import time
import os
import sys
import importlib
import requests
import threading
import json
import io
from datetime import datetime

# ============================================================
# 0. ПРИНУДИТЕЛЬНЫЙ ЗАПУСК ЧЕРЕЗ 3.14 (С FALLBACK НА 3.12)
# ============================================================

CURRENT = sys.version_info[:2]
TARGET = (3, 14)
FALLBACK = (3, 12)

_RELAUNCH_FLAG = "_SYSTMKA_RELAUNCHED"

if CURRENT != TARGET and not os.environ.get(_RELAUNCH_FLAG):
    print(f"🔄 Перезапуск через Python {TARGET[0]}.{TARGET[1]}...")
    print(f"   (текущая: {CURRENT[0]}.{CURRENT[1]})")
    
    try:
        env = os.environ.copy()
        env[_RELAUNCH_FLAG] = "1"
        
        result = subprocess.run(
            ["py", f"-{TARGET[0]}.{TARGET[1]}", os.path.abspath(__file__)] + sys.argv[1:],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"⚠️ Не удалось перезапустить через 3.14: {e}")
        print(f"   Пробую 3.12...")
        
        try:
            env = os.environ.copy()
            env[_RELAUNCH_FLAG] = "1"
            
            result = subprocess.run(
                ["py", f"-{FALLBACK[0]}.{FALLBACK[1]}", os.path.abspath(__file__)] + sys.argv[1:],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
            )
            sys.exit(result.returncode)
        except Exception as e2:
            print(f"⚠️ Не удалось перезапустить через 3.12: {e2}")
            print(f"   Продолжаю на {CURRENT[0]}.{CURRENT[1]}")

# ============================================================
# 1. ФОРСИРУЕМ UTF-8 ДЛЯ WINDOWS CMD
# ============================================================

if sys.platform == "win32":
    try:
        _original_stdout = sys.stdout
        _original_stderr = sys.stderr
        
        if hasattr(_original_stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(
                _original_stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stdout._original = _original_stdout
        
        if hasattr(_original_stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(
                _original_stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stderr._original = _original_stderr
    except Exception:
        pass

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_PID_FILE = "bot.pid"
LOG_FILE = "bot.log"

# ============================================================
# 3. DNS_CONFIG (ПЕРВЫМ!)
# ============================================================

try:
    import dns_config
    print("✅ dns_config загружен")
except Exception as e:
    print(f"⚠️ Ошибка dns_config: {e}")

# ============================================================
# 4. ERROR_GUARDIAN
# ============================================================

print("=" * 70)
print("🛡️ ЗАГРУЗКА СТРАЖА ОШИБОК...")
print("=" * 70)

try:
    import error_guardian
    print("✅ error_guardian загружен")
except Exception as e:
    print(f"❌ Ошибка загрузки error_guardian: {e}")
    print("⚠️ Бот будет работать без стража ошибок")

# ============================================================
# 5. ИМПОРТЫ ИЗ ПОДМОДУЛЕЙ
# ============================================================

from auto_start_modules import (
    print_status,
    print_header,
    print_separator,
    force_load_imports,
)

from auto_start_process import (
    check_internet,
    kill_old_process,
    check_bot_running,
    start_bot,
    monitor_logs,
)

# ============================================================
# 6. ОСНОВНОЙ ЦИКЛ
# ============================================================

def main():
    """Основная функция автозапуска"""
    print_header("АВТОЗАПУСК СИСТМКИ", "🤖")
    print_status(f"Директория: {BOT_DIR}", "FILE")
    print_status(f"Python: {sys.version.split()[0]}", "SYSTEM")
    print_separator()
    
    internet, ping = check_internet()
    print_status(
        f"🌐 Интернет: {'✅' if internet else '❌'} (пинг: {ping}мс)",
        "NETWORK"
    )
    
    # Проверка Telegram
    try:
        from auto_start_process import check_telegram
        tg_ok, tg_ping, tg_err = check_telegram()
        if tg_ok:
            print_status(f"📱 Telegram: ✅ (пинг: {tg_ping}мс)", "NETWORK")
        else:
            print_status(f"📱 Telegram: ❌ ({tg_err})", "ERROR")
    except Exception:
        pass
    
    print_separator()
    
    loaded, failed = force_load_imports()
    
    if failed:
        print_status(f"⚠️ Не загружено модулей: {len(failed)}", "WARN")
        print_status("Продолжаю работу с доступными модулями...", "WARN")
        print_separator()
    
    if not check_bot_running():
        start_bot()
    else:
        print_status("✅ Бот уже запущен", "OK")
    
    print_separator()
    print_header("ЗАПУЩЕН МОНИТОРИНГ", "📋")
    print_separator()
    
    log_thread = threading.Thread(target=monitor_logs, daemon=True)
    log_thread.start()
    
    print_header("СИСТЕМА РАБОТАЕТ", "🚀")
    print_status("Нажми Ctrl+C для остановки", "INFO")
    print_separator()
    print_status("📋 ДОСТУПНЫЕ КОМАНДЫ:", "CONSOLE")
    print_status("  /status  — статус бота", "CONSOLE")
    print_status("  /restart — перезапустить бота", "CONSOLE")
    print_status("  /stop    — остановить бота", "CONSOLE")
    print_separator()
    
    try:
        while True:
            time.sleep(30)
            
            internet, ping = check_internet()
            if int(time.time()) % 60 < 5:
                print_status(
                    f"📊 Пинг: {ping}мс {'✅' if internet else '❌'}",
                    "PING"
                )
            
            if not check_bot_running():
                print_status("⚠️ Бот упал! Перезапускаю...", "WARN")
                start_bot()
                
    except KeyboardInterrupt:
        print("\n👋 Остановлено пользователем")
        kill_old_process()
        print_status("✅ Бот остановлен", "OK")
    except Exception as e:
        print_status(f"❌ Критическая ошибка: {e}", "ERROR")
        time.sleep(5)

# ============================================================
# 7. ЗАПУСК
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Остановлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)