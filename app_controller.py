"""Управление приложениями — Windows-версия (замена Android am/pm/dumpsys)"""

import os
import sys
import platform
import subprocess
import time
from pathlib import Path

# ============================================================
# 1. ИМПОРТЫ (С ЗАЩИТОЙ)
# ============================================================

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil не установлен — список процессов недоступен")

# ============================================================
# 2. КАРТА ПРИЛОЖЕНИЙ (Windows)
# ============================================================

# Соответствие: понятное имя → путь/команда запуска
APP_PACKAGES = {
    # Браузеры
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "opera": "opera",
    "brave": "brave",
    
    # Мессенджеры
    "telegram": "telegram",
    "whatsapp": "whatsapp",
    "discord": "discord",
    "skype": "skype",
    "zoom": "zoom",
    
    # Медиа
    "youtube": "https://www.youtube.com",
    "spotify": "spotify",
    "vlc": "vlc",
    "media player": "wmplayer",
    
    # Игры
    "steam": "steam",
    "epic games": "epicgameslauncher",
    
    # Системные
    "notepad": "notepad",
    "блокнот": "notepad",
    "calculator": "calc",
    "калькулятор": "calc",
    "paint": "mspaint",
    "пэйнт": "mspaint",
    "explorer": "explorer",
    "проводник": "explorer",
    "cmd": "cmd",
    "командная строка": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "диспетчер задач": "taskmgr",
    "control panel": "control",
    "панель управления": "control",
    "settings": "ms-settings:",
    "настройки": "ms-settings:",
    
    # Офис
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "onenote": "onenote",
    
    # Разработка
    "vscode": "code",
    "visual studio code": "code",
    "pycharm": "pycharm",
    "sublime": "sublime_text",
    "git bash": "git-bash",
    
    # Архиваторы
    "winrar": "winrar",
    "7zip": "7zFM",
    "7-zip": "7zFM",
}

# Расширения для поиска .exe в стандартных папках
APP_PATHS = [
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    os.path.expanduser(r"~\AppData\Local"),
    os.path.expanduser(r"~\AppData\Roaming"),
]

# Кэш найденных путей
_app_cache = {}

# ============================================================
# 3. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def find_app_executable(app_name):
    """
    Найти .exe приложения в стандартных папках Windows.
    
    Args:
        app_name: имя приложения
    
    Returns:
        str или None: путь к .exe
    """
    # Проверяем кэш
    if app_name in _app_cache:
        return _app_cache[app_name]
    
    app_lower = app_name.lower().strip()
    
    # 1. Проверяем карту APP_PACKAGES
    if app_lower in APP_PACKAGES:
        target = APP_PACKAGES[app_lower]
        
        # Если это URL — возвращаем как есть
        if target.startswith(("http://", "https://", "ms-settings:")):
            _app_cache[app_name] = target
            return target
        
        # Проверяем, есть ли exe в PATH
        exe_path = _which(target)
        if exe_path:
            _app_cache[app_name] = exe_path
            return exe_path
    
    # 2. Ищем .exe в стандартных папках
    for base_path in APP_PATHS:
        if not os.path.exists(base_path):
            continue
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Ограничиваем глубину
                depth = root[len(base_path):].count(os.sep)
                if depth > 3:
                    dirs[:] = []
                    continue
                
                for file in files:
                    if file.endswith(".exe"):
                        if app_lower in file.lower() or app_lower in root.lower():
                            full_path = os.path.join(root, file)
                            _app_cache[app_name] = full_path
                            return full_path
        except PermissionError:
            continue
        except Exception:
            continue
    
    return None

def _which(cmd):
    """Аналог Unix-команды `which` для Windows"""
    try:
        result = subprocess.run(
            ["where", cmd],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="cp866",
            errors="ignore"
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None

def open_app(app_name):
    """
    Открыть приложение.
    
    Args:
        app_name: имя приложения
    
    Returns:
        bool: успех
    """
    app_lower = app_name.lower().strip()
    
    # 1. Специальные Windows-команды (ms-settings: и т.д.)
    if app_lower in APP_PACKAGES:
        target = APP_PACKAGES[app_lower]
        
        # URL или ms-settings:
        if target.startswith(("http://", "https://", "ms-settings:")):
            try:
                os.startfile(target)
                return True
            except Exception as e:
                print(f"⚠️ Ошибка открытия {target}: {e}")
                return False
        
        # Обычная команда — пробуем через start
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            
            subprocess.Popen(
                ["cmd", "/c", "start", "", target],
                shell=False,
                creationflags=creationflags
            )
            return True
        except Exception:
            pass
    
    # 2. Ищем .exe и открываем
    exe_path = find_app_executable(app_name)
    if exe_path:
        try:
            if exe_path.startswith(("http://", "https://", "ms-settings:")):
                os.startfile(exe_path)
            else:
                subprocess.Popen([exe_path])
            return True
        except Exception as e:
            print(f"⚠️ Ошибка открытия {exe_path}: {e}")
            return False
    
    # 3. Последняя попытка — через cmd start
    try:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        
        subprocess.Popen(
            ["cmd", "/c", "start", "", app_name],
            creationflags=creationflags
        )
        return True
    except Exception as e:
        print(f"⚠️ Не удалось открыть {app_name}: {e}")
        return False

def close_app(app_name):
    """
    Закрыть приложение по имени процесса.
    
    Args:
        app_name: имя приложения (или процесса)
    
    Returns:
        int: количество закрытых процессов
    """
    if not PSUTIL_AVAILABLE:
        # Fallback: taskkill по имени
        try:
            result = subprocess.run(
                ["taskkill", "/IM", f"{app_name}.exe", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="cp866",
                errors="ignore"
            )
            return 1 if result.returncode == 0 else 0
        except Exception:
            return 0
    
    app_lower = app_name.lower().strip()
    closed = 0
    
    try:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info['name']
                if not proc_name:
                    continue
                
                if app_lower in proc_name.lower():
                    proc.terminate()
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if closed > 0:
            time.sleep(1)
            # Добиваем упрямых
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and app_lower in proc_name.lower():
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        return closed
    except Exception as e:
        print(f"⚠️ Ошибка закрытия {app_name}: {e}")
        return 0

def install_app(installer_path):
    """
    Установить приложение (запустить установщик).
    
    Args:
        installer_path: путь к .exe / .msi установщику
    
    Returns:
        bool: успех
    """
    if not os.path.exists(installer_path):
        print(f"⚠️ Установщик не найден: {installer_path}")
        return False
    
    try:
        if installer_path.endswith(".msi"):
            subprocess.Popen(["msiexec", "/i", installer_path])
        else:
            subprocess.Popen([installer_path])
        return True
    except Exception as e:
        print(f"⚠️ Ошибка запуска установщика: {e}")
        return False

def uninstall_app(app_name):
    """
    Удалить приложение через winget.
    
    Args:
        app_name: имя приложения
    
    Returns:
        bool: успех
    """
    try:
        result = subprocess.run(
            ["winget", "uninstall", app_name, "--silent"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="ignore"
        )
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️ Ошибка удаления {app_name}: {e}")
        return False

def list_installed_apps():
    """
    Список установленных приложений.
    
    Returns:
        list: список имён процессов (уникальные)
    """
    if not PSUTIL_AVAILABLE:
        return []
    
    try:
        apps = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and name.endswith(".exe"):
                    apps.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(apps)
    except Exception:
        return []

def get_running_apps():
    """
    Список запущенных приложений (без системных).
    
    Returns:
        list: [{name, pid, memory_mb, cpu}, ...]
    """
    if not PSUTIL_AVAILABLE:
        return []
    
    try:
        apps = []
        for proc in psutil.process_iter(['name', 'pid', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                name = info.get('name', '')
                
                # Пропускаем системные
                if not name or name.lower().startswith(
                    ("system", "svchost", "csrss", "wininit", "winlogon")
                ):
                    continue
                
                mem_info = info.get('memory_info')
                mem_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0
                
                apps.append({
                    "name": name,
                    "pid": info['pid'],
                    "memory_mb": mem_mb,
                    "cpu": round(info.get('cpu_percent', 0) or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        apps.sort(key=lambda x: x['memory_mb'], reverse=True)
        return apps
    except Exception:
        return []

def get_current_app():
    """
    Получить активное окно (приложение на переднем плане).
    
    Returns:
        str или None: имя процесса
    """
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        
        # Получаем PID
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        if pid.value == 0:
            return None
        
        # Получаем имя процесса
        if PSUTIL_AVAILABLE:
            try:
                proc = psutil.Process(pid.value)
                return proc.name()
            except Exception:
                pass
        
        return f"PID: {pid.value}"
    except Exception as e:
        print(f"⚠️ Ошибка получения активного окна: {e}")
        return None

def get_app_path(app_name):
    """Получить путь к .exe приложения"""
    return find_app_executable(app_name)

def is_app_running(app_name):
    """Проверить, запущено ли приложение"""
    if not PSUTIL_AVAILABLE:
        return False
    
    app_lower = app_name.lower()
    try:
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info.get('name', '')
                if name and app_lower in name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return False

# ============================================================
# 4. ФОРМАТИРОВАНИЕ
# ============================================================

def format_installed_apps(limit=30):
    """Форматировать список установленных приложений"""
    apps = list_installed_apps()
    
    if not apps:
        return "❌ Не удалось получить список приложений"
    
    lines = [f"📱 Установленных процессов: {len(apps)}"]
    for app in apps[:limit]:
        lines.append(f"  • {app}")
    
    if len(apps) > limit:
        lines.append(f"  ... и ещё {len(apps) - limit}")
    
    return "\n".join(lines)

def format_running_apps(limit=15):
    """Форматировать список запущенных приложений"""
    apps = get_running_apps()
    
    if not apps:
        return "❌ Нет запущенных приложений"
    
    lines = [f"🟢 Запущенных приложений: {len(apps)}", ""]
    
    for app in apps[:limit]:
        lines.append(f"  • {app['name']}")
        lines.append(f"    PID: {app['pid']} | RAM: {app['memory_mb']}MB | CPU: {app['cpu']}%")
    
    if len(apps) > limit:
        lines.append(f"\n... и ещё {len(apps) - limit}")
    
    return "\n".join(lines)

def format_current_app():
    """Форматировать активное приложение"""
    current = get_current_app()
    if current:
        return f"🖥 Активное окно: {current}"
    return "🖥 Не удалось определить активное окно"

def format_app_info(app_name):
    """Форматировать информацию о приложении"""
    path = get_app_path(app_name)
    running = is_app_running(app_name)
    
    lines = [f"📱 Приложение: {app_name}"]
    lines.append(f"  Путь: {path or 'не найден'}")
    lines.append(f"  Запущено: {'✅' if running else '❌'}")
    
    return "\n".join(lines)

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("📱 Управление приложениями загружено (PC / Windows)")
print(f"💻 ОС: {platform.system()} {platform.release()}")
print(f"📦 psutil: {'✅' if PSUTIL_AVAILABLE else '❌'}")
print(f"📋 Известных приложений: {len(APP_PACKAGES)}")