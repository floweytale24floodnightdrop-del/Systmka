"""Управление процессом бота для автозапуска Систмки"""

import subprocess
import time
import os
import sys
import requests

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_PID_FILE = "bot.pid"
LOG_FILE = "bot.log"

# ============================================================
# 2. ПРОВЕРКА ИНТЕРНЕТА
# ============================================================

def check_internet():
    """
    Проверить интернет.
    
    Returns:
        tuple: (online, ping_ms)
    """
    hosts = [
        ("https://api.telegram.org", 200),
        ("https://www.google.com", 200),
        ("https://1.1.1.1", None),
    ]
    
    for host, expected_status in hosts:
        try:
            start = time.time()
            response = requests.get(host, timeout=30)
            ping = int((time.time() - start) * 1000)
            
            if expected_status is None:
                return True, ping
            
            if response.status_code == expected_status:
                return True, ping
        except Exception:
            continue
    
    return False, 9999


def check_telegram():
    """
    Проверить доступность Telegram API.
    
    Returns:
        tuple: (available, ping_ms, error)
    """
    try:
        start = time.time()
        response = requests.get(
            "https://api.telegram.org",
            timeout=10,
        )
        ping = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            return True, ping, None
        
        return False, ping, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, 0, "ConnectionError"
    except Exception as e:
        return False, 0, str(e)[:100]

# ============================================================
# 3. УПРАВЛЕНИЕ ПРОЦЕССОМ
# ============================================================

def kill_old_process():
    """Убить старый процесс бота (если был)"""
    pid_file = os.path.join(BOT_DIR, BOT_PID_FILE)
    
    if not os.path.exists(pid_file):
        return
    
    try:
        with open(pid_file, "r") as f:
            old_pid = int(f.read().strip())
        
        try:
            import psutil
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                proc.terminate()
                time.sleep(1)
                if proc.is_running():
                    proc.kill()
                print(f"⚠️ Старый процесс {old_pid} убит")
        except ImportError:
            subprocess.run(
                ["taskkill", "/PID", str(old_pid), "/F"],
                capture_output=True
            )
            print(f"⚠️ Старый процесс {old_pid} убит")
        
        os.remove(pid_file)
    except Exception as e:
        print(f"⚠️ Ошибка удаления старого процесса: {e}")


def check_bot_running():
    """Проверить, работает ли бот"""
    pid_file = os.path.join(BOT_DIR, BOT_PID_FILE)
    
    if not os.path.exists(pid_file):
        return False
    
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return str(pid) in result.stdout
    except Exception:
        return False


def start_bot():
    """Запустить бота в фоне"""
    os.chdir(BOT_DIR)
    
    try:
        if not os.path.exists("bot.py"):
            print("❌ bot.py не найден!")
            return False
        
        kill_old_process()
        
        log_path = os.path.join(BOT_DIR, LOG_FILE)
        
        log_file = open(log_path, "a", encoding="utf-8")
        
        if sys.platform == "win32":
            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.DETACHED_PROCESS
            )
        else:
            creationflags = 0
        
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        
        process = subprocess.Popen(
            [sys.executable, "bot.py"],
            cwd=BOT_DIR,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            start_new_session=(sys.platform != "win32"),
            env=env,
        )
        
        with open(os.path.join(BOT_DIR, BOT_PID_FILE), "w") as f:
            f.write(str(process.pid))
        
        print(f"✅ bot.py запущен (PID: {process.pid})")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

# ============================================================
# 4. МОНИТОРИНГ ЛОГОВ
# ============================================================

def monitor_logs():
    """Мониторинг логов в реальном времени"""
    log_path = os.path.join(BOT_DIR, LOG_FILE)
    last_position = 0
    
    wait_count = 0
    while not os.path.exists(log_path) and wait_count < 30:
        time.sleep(1)
        wait_count += 1
    
    if not os.path.exists(log_path):
        print("⚠️ Файл логов не найден, мониторинг отключён")
        return
    
    print("📋 Мониторинг логов...")
    
    while True:
        try:
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                if current_size < last_position:
                    last_position = 0
                
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                
                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if any(word in line for word in [
                        "Error", "Exception", "Traceback", "NameError",
                        "ImportError", "KeyError", "AttributeError",
                        "TypeError", "ModuleNotFoundError", "FileNotFoundError"
                    ]):
                        print(f"❌ {line[:150]}")
                    elif "✅" in line or "загружен" in line or "готов" in line:
                        print(f"✅ {line[:150]}")
                    elif "⚠️" in line:
                        print(f"⚠️ {line[:150]}")
            
            time.sleep(2)
        except Exception:
            time.sleep(5)