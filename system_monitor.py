"""Мониторинг системы — реальные показатели на PC через psutil + speedtest (через 3.12)"""

import os
import sys
import time
import json
import platform
import subprocess
import threading
from datetime import datetime, timedelta

# ============================================================
# 1. ИМПОРТЫ (С ЗАЩИТОЙ)
# ============================================================

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil не установлен — мониторинг работает в ограниченном режиме")

# speedtest через отдельный мост (Python 3.12)
try:
    from speedtest_bridge import (
        run_speedtest as _run_speedtest,
        is_speedtest_available as _speedtest_available,
    )
    SPEEDTEST_AVAILABLE = _speedtest_available()
    if not SPEEDTEST_AVAILABLE:
        print("⚠️ speedtest недоступен")
except ImportError:
    SPEEDTEST_AVAILABLE = False
    _run_speedtest = None
    print("⚠️ speedtest_bridge не найден")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests не установлен — проверка интернета недоступна")

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

_cache = {
    "cpu": {"value": 0, "time": 0},
    "speedtest": {"value": None, "time": 0},
}

CACHE_TTL_CPU = 1
CACHE_TTL_SPEED = 300

# ============================================================
# 3. ОСНОВНЫЕ ПОКАЗАТЕЛИ
# ============================================================

def get_cpu_usage():
    """Получить загрузку CPU через psutil"""
    if not PSUTIL_AVAILABLE:
        return 0.0
    
    now = time.time()
    if now - _cache["cpu"]["time"] < CACHE_TTL_CPU:
        return _cache["cpu"]["value"]
    
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        _cache["cpu"]["value"] = cpu
        _cache["cpu"]["time"] = now
        return cpu
    except Exception as e:
        print(f"⚠️ Ошибка CPU: {e}")
        return 0.0


def get_cpu_count():
    """Количество ядер CPU"""
    if not PSUTIL_AVAILABLE:
        return 0
    try:
        return psutil.cpu_count(logical=True)
    except Exception:
        return 0


def get_memory_usage():
    """Получить использование RAM через psutil"""
    if not PSUTIL_AVAILABLE:
        return {"total_mb": 0, "used_mb": 0, "percent": 0}
    
    try:
        mem = psutil.virtual_memory()
        total_mb = mem.total // (1024 * 1024)
        used_mb = mem.used // (1024 * 1024)
        return {
            "total_mb": total_mb,
            "used_mb": used_mb,
            "percent": round(mem.percent, 1),
        }
    except Exception as e:
        print(f"⚠️ Ошибка памяти: {e}")
        return {"total_mb": 0, "used_mb": 0, "percent": 0}


def get_swap_usage():
    """Использование swap (файла подкачки)"""
    if not PSUTIL_AVAILABLE:
        return {"total_mb": 0, "used_mb": 0, "percent": 0}
    
    try:
        swap = psutil.swap_memory()
        return {
            "total_mb": swap.total // (1024 * 1024),
            "used_mb": swap.used // (1024 * 1024),
            "percent": round(swap.percent, 1),
        }
    except Exception:
        return {"total_mb": 0, "used_mb": 0, "percent": 0}


def get_disk_usage(path=None):
    """Получить использование диска через psutil"""
    if not PSUTIL_AVAILABLE:
        return {"total": "0", "used": "0", "free": "0", "percent": "0%"}
    
    if path is None:
        if platform.system() == "Windows":
            path = os.environ.get("SystemDrive", "C:") + "\\"
        else:
            path = "/"
    
    try:
        disk = psutil.disk_usage(path)
        
        def fmt(bytes_val):
            gb = bytes_val / (1024 ** 3)
            if gb >= 1:
                return f"{gb:.1f}GB"
            mb = bytes_val / (1024 ** 2)
            return f"{mb:.0f}MB"
        
        return {
            "total": fmt(disk.total),
            "used": fmt(disk.used),
            "free": fmt(disk.free),
            "percent": f"{disk.percent}%",
        }
    except Exception as e:
        print(f"⚠️ Ошибка диска: {e}")
        return {"total": "0", "used": "0", "free": "0", "percent": "0%"}


def get_uptime():
    """Получить время работы системы через psutil"""
    if not PSUTIL_AVAILABLE:
        return "0ч 0м"
    
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}ч {minutes}м"
    except Exception:
        return "0ч 0м"


def get_processes_count():
    """Количество процессов через psutil"""
    if not PSUTIL_AVAILABLE:
        return 0
    try:
        return len(psutil.pids())
    except Exception:
        return 0


def get_battery_info():
    """Информация о батарее через psutil"""
    if not PSUTIL_AVAILABLE:
        return {}
    
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {}
        
        info = {
            "level": int(battery.percent),
            "power_plugged": battery.power_plugged,
        }
        
        if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft > 0:
            hours = battery.secsleft // 3600
            minutes = (battery.secsleft % 3600) // 60
            info["time_left"] = f"{hours}ч {minutes}м"
        
        return info
    except Exception:
        return {}


def get_top_processes(limit=5):
    """Топ процессов по CPU/RAM"""
    if not PSUTIL_AVAILABLE:
        return []
    
    try:
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None and info['cpu_percent'] > 0:
                    processes.append({
                        "name": info['name'],
                        "cpu": round(info['cpu_percent'], 1),
                        "memory": round(info.get('memory_percent', 0), 1),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    except Exception:
        return []

# ============================================================
# 4. МОНИТОРИНГ СЕТИ
# ============================================================

def check_internet_status():
    """Проверить интернет через requests"""
    if not REQUESTS_AVAILABLE:
        return {"online": False, "ping_ms": 0}
    
    try:
        start = time.time()
        response = requests.get("https://api.telegram.org", timeout=5)
        ping = int((time.time() - start) * 1000)
        return {
            "online": response.status_code == 200,
            "ping_ms": ping,
        }
    except Exception:
        return {"online": False, "ping_ms": 0}


def check_ping_host(host="8.8.8.8", count=3):
    """Пинг до конкретного хоста"""
    try:
        system = platform.system().lower()
        
        if system == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        
        import re
        avg_match = re.search(r'(?:Average|avg)\s*[=:]\s*([\d.]+)', output, re.IGNORECASE)
        loss_match = re.search(r'(\d+)%', output)
        
        return {
            "success": result.returncode == 0,
            "avg_ms": float(avg_match.group(1)) if avg_match else 0,
            "packet_loss": int(loss_match.group(1)) if loss_match else 0,
        }
    except Exception as e:
        return {"success": False, "avg_ms": 0, "packet_loss": 100}


def run_speedtest():
    """
    Запустить speedtest (через speedtest_bridge).
    
    ИСПРАВЛЕНО: вместо прямого import speedtest — используется
    speedtest_bridge, который вызывает Python 3.12 через subprocess.
    """
    if not SPEEDTEST_AVAILABLE or _run_speedtest is None:
        return None
    
    # Кэш
    now = time.time()
    if _cache["speedtest"]["value"] and (now - _cache["speedtest"]["time"]) < CACHE_TTL_SPEED:
        return _cache["speedtest"]["value"]
    
    try:
        result = _run_speedtest()
        if result:
            _cache["speedtest"]["value"] = result
            _cache["speedtest"]["time"] = now
            return result
    except Exception as e:
        print(f"⚠️ speedtest ошибка: {e}")
    
    return None

# ============================================================
# 5. ФОРМАТИРОВАНИЕ ОТЧЁТА
# ============================================================

def get_full_report(db=None):
    """Получить полный отчёт о системе"""
    cpu = get_cpu_usage()
    mem = get_memory_usage()
    swap = get_swap_usage()
    disk = get_disk_usage()
    internet = check_internet_status()
    battery = get_battery_info()
    
    report = {
        "system": {
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu": cpu,
            "cpu_count": get_cpu_count(),
            "memory": mem,
            "swap": swap,
            "disk": disk,
            "uptime": get_uptime(),
            "processes": get_processes_count(),
            "battery": battery,
        },
        "network": internet,
        "time": datetime.now().strftime("%H:%M:%S %d.%m.%Y"),
    }
    
    if db:
        try:
            report["chats"] = {
                "total_chats": len(getattr(db, "all_chats", {})),
                "total_users": len(getattr(db, "user_profiles", {})),
                "muted": len(getattr(db, "muted_users", {})),
                "banned": len(getattr(db, "banned_users", {})),
                "premium": len(getattr(db, "premium_users", {})),
            }
        except Exception:
            pass
    
    return report


def format_report(report):
    """Форматировать отчёт для отправки в Telegram"""
    sys_info = report.get('system', {})
    lines = [
        "📊 СИСТЕМНЫЙ МОНИТОР",
        "=" * 40,
        f"⏱ {report.get('time', '?')}",
        "",
        "💻 СИСТЕМА:",
        f"  ОС: {sys_info.get('os', '?')}",
        f"  Python: {sys_info.get('python', '?')}",
        f"  CPU: {sys_info.get('cpu', 0):.1f}% ({sys_info.get('cpu_count', 0)} ядер)",
    ]
    
    mem = sys_info.get('memory', {})
    lines.append(f"  RAM: {mem.get('used_mb', 0)}/{mem.get('total_mb', 0)}MB ({mem.get('percent', 0)}%)")
    
    swap = sys_info.get('swap', {})
    if swap.get('total_mb', 0) > 0:
        lines.append(f"  Swap: {swap.get('used_mb', 0)}/{swap.get('total_mb', 0)}MB ({swap.get('percent', 0)}%)")
    
    disk = sys_info.get('disk', {})
    lines.append(f"  Disk: {disk.get('used', '0')}/{disk.get('total', '0')} ({disk.get('percent', '0%')})")
    lines.append(f"  Free: {disk.get('free', '0')}")
    
    lines.append(f"  Uptime: {sys_info.get('uptime', '0ч 0м')}")
    lines.append(f"  Процессов: {sys_info.get('processes', 0)}")
    
    battery = sys_info.get('battery', {})
    if battery:
        level = battery.get('level', '?')
        plugged = "🔌" if battery.get('power_plugged') else "🔋"
        time_left = battery.get('time_left', '')
        lines.append(f"  {plugged} Батарея: {level}%" + (f" ({time_left})" if time_left else ""))
    
    internet = report.get('network', {})
    lines.append("")
    lines.append("🌐 СЕТЬ:")
    lines.append(f"  Интернет: {'✅' if internet.get('online', False) else '❌'}")
    lines.append(f"  Пинг: {internet.get('ping_ms', 0)}мс")
    
    chats = report.get('chats', {})
    if chats:
        lines.append("")
        lines.append("💬 ЧАТЫ:")
        lines.append(f"  Всего чатов: {chats.get('total_chats', 0)}")
        lines.append(f"  Пользователей: {chats.get('total_users', 0)}")
        lines.append(f"  В муте: {chats.get('muted', 0)}")
        lines.append(f"  В бане: {chats.get('banned', 0)}")
        lines.append(f"  Премиум: {chats.get('premium', 0)}")
    
    return "\n".join(lines)


def format_speedtest_report():
    """Форматировать отчёт о скорости интернета"""
    result = run_speedtest()
    
    if not result:
        return "❌ Не удалось измерить скорость (speedtest недоступен)"
    
    lines = [
        "📡 ТЕСТ СКОРОСТИ:",
        "=" * 40,
        f"⬇️ Скачивание: {result['download_mbps']} Мбит/с",
        f"⬆️ Загрузка: {result['upload_mbps']} Мбит/с",
        f"📶 Пинг: {result['ping_ms']}мс",
        f"🖥 Сервер: {result['server']} ({result['server_country']})",
    ]
    
    return "\n".join(lines)

# ============================================================
# 6. КРАТКИЙ СТАТУС
# ============================================================

def get_quick_status():
    """Быстрый статус системы"""
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage().get("percent", 0),
        "disk": get_disk_usage().get("percent", "0%"),
        "uptime": get_uptime(),
        "internet": check_internet_status().get("online", False),
    }


def format_quick_status():
    """Форматировать краткий статус в одну строку"""
    status = get_quick_status()
    return (
        f"💻 CPU: {status['cpu']:.1f}% | "
        f"🧠 RAM: {status['memory']}% | "
        f"💾 Disk: {status['disk']} | "
        f"⏱ {status['uptime']} | "
        f"🌐 {'✅' if status['internet'] else '❌'}"
    )

# ============================================================
# 7. ФОНОВЫЙ МОНИТОРИНГ
# ============================================================

_monitor_thread = None
_monitor_stop = threading.Event()


def monitor_loop(bot, owner_ids, interval=300):
    """Фоновый цикл мониторинга"""
    while not _monitor_stop.is_set():
        if _monitor_stop.wait(interval):
            break
        
        try:
            internet = check_internet_status()
            
            if not internet.get("online"):
                for oid in owner_ids:
                    try:
                        bot.send_message(oid, "❌ Интернет пропал!")
                    except Exception:
                        pass
            
            mem = get_memory_usage()
            if mem.get("percent", 0) > 90:
                for oid in owner_ids:
                    try:
                        bot.send_message(oid, f"⚠️ RAM загружена на {mem['percent']}%!")
                    except Exception:
                        pass
            
            disk = get_disk_usage()
            try:
                disk_percent = int(disk.get("percent", "0%").replace("%", ""))
                if disk_percent > 90:
                    for oid in owner_ids:
                        try:
                            bot.send_message(oid, f"⚠️ Диск заполнен на {disk_percent}%!")
                        except Exception:
                            pass
            except Exception:
                pass
                
        except Exception as e:
            print(f"⚠️ Ошибка в monitor_loop: {e}")


def start_monitor(bot, owner_ids, interval=300):
    """Запустить фоновый мониторинг"""
    global _monitor_thread
    
    if _monitor_thread and _monitor_thread.is_alive():
        return _monitor_thread
    
    _monitor_stop.clear()
    _monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(bot, owner_ids, interval),
        daemon=True
    )
    _monitor_thread.start()
    print(f"📊 Фоновый мониторинг запущен (интервал: {interval}с)")
    return _monitor_thread


def stop_monitor():
    """Остановить фоновый мониторинг"""
    _monitor_stop.set()
    if _monitor_thread:
        _monitor_thread.join(timeout=5)
    print("📊 Фоновый мониторинг остановлен")

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("📊 Мониторинг системы загружен (PC / psutil)")
print(f"💻 ОС: {platform.system()} {platform.release()}")
print(f"🐍 Python: {platform.python_version()}")
print(f"📦 psutil: {'✅' if PSUTIL_AVAILABLE else '❌'}")
print(f"📦 speedtest (через 3.12): {'✅' if SPEEDTEST_AVAILABLE else '❌'}")
print(f"📦 requests: {'✅' if REQUESTS_AVAILABLE else '❌'}")
print(f"💻 Ядер CPU: {get_cpu_count()}")
print(f"🧠 RAM: {get_memory_usage().get('total_mb', 0)}MB")
print(f"💾 Disk: {get_disk_usage().get('total', '0')}")