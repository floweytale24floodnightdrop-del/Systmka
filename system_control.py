"""Управление системой — PC-версия (Windows/Linux/macOS)"""

import os
import sys
import json
import time
import platform
import subprocess
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ (С ЗАЩИТОЙ)
# ============================================================

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil не установлен — часть функций недоступна")

# ============================================================
# 2. ОСНОВНОЙ КЛАСС
# ============================================================

class SystemControl:
    """
    Управление системой на PC.
    
    В отличие от Android:
    - Нет root-модели (su, Magisk)
    - Нет appops, pm grant
    - Нет dumpsys, settings put
    - Все системные данные — через platform + psutil + PowerShell
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.is_windows = self.os_type == "Windows"
        self.is_linux = self.os_type == "Linux"
        self.is_mac = self.os_type == "Darwin"
        self.is_admin = self._check_admin()
    
    # ============================================================
    # 3. ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
    # ============================================================
    
    def _check_admin(self):
        """
        Проверить, запущен ли процесс от администратора.
        
        Returns:
            bool
        """
        try:
            if self.is_windows:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Linux/macOS
                return os.geteuid() == 0
        except Exception:
            return False
    
    def check_admin(self):
        """Публичный метод проверки прав администратора"""
        return self.is_admin
    
    def request_admin_hint(self):
        """
        Подсказать, как получить права администратора.
        
        Returns:
            str: инструкция
        """
        if self.is_admin:
            return "✅ Уже с правами администратора"
        
        if self.is_windows:
            return (
                "⚠️ Нужны права администратора.\n"
                "💡 Запусти PowerShell от имени администратора:\n"
                "   Win + X → 'Windows PowerShell (администратор)'"
            )
        else:
            return "💡 Запусти через sudo: sudo python bot.py"
    
    # ============================================================
    # 4. ИНФОРМАЦИЯ О СИСТЕМЕ
    # ============================================================
    
    def get_device_info(self):
        """
        Получить информацию об устройстве.
        
        Returns:
            dict: полная информация
        """
        info = {
            "os": self.os_type,
            "os_release": platform.release(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python": platform.python_version(),
            "is_admin": self.is_admin,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Платформо-зависимая информация
        if self.is_windows:
            info["windows_edition"] = self._get_windows_edition()
            info["windows_build"] = self._get_windows_build()
        
        # CPU / RAM через psutil
        if PSUTIL_AVAILABLE:
            try:
                info["cpu_count"] = psutil.cpu_count(logical=True)
                info["cpu_physical"] = psutil.cpu_count(logical=False)
                
                mem = psutil.virtual_memory()
                info["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
                
                # Диск
                disk = psutil.disk_usage("/" if not self.is_windows else "C:\\")
                info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
                info["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
                
                # Uptime
                boot_time = psutil.boot_time()
                uptime_sec = time.time() - boot_time
                info["uptime_hours"] = round(uptime_sec / 3600, 1)
            except Exception:
                pass
        
        return info
    
    def _get_windows_edition(self):
        """Получить редакцию Windows (Home/Pro/Enterprise)"""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_OperatingSystem).Caption"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    def _get_windows_build(self):
        """Получить сборку Windows"""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "[System.Environment]::OSVersion.Version.ToString()"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    # ============================================================
    # 5. БАТАРЕЯ
    # ============================================================
    
    def get_battery_info(self):
        """
        Получить информацию о батарее.
        
        Returns:
            dict: {percent, plugged, time_left} или пустой dict
        """
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {}  # стационарный ПК
            
            info = {
                "percent": int(battery.percent),
                "plugged": battery.power_plugged,
            }
            
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft > 0:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                info["time_left"] = f"{hours}ч {minutes}м"
            
            return info
        except Exception:
            return {}
    
    # ============================================================
    # 6. ПРОЦЕССЫ
    # ============================================================
    
    def get_top_processes(self, limit=10):
        """
        Топ процессов по CPU/RAM.
        
        Returns:
            list: [{name, pid, cpu, memory_mb}, ...]
        """
        if not PSUTIL_AVAILABLE:
            return []
        
        try:
            processes = []
            for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info']):
                try:
                    info = proc.info
                    mem_info = info.get('memory_info')
                    mem_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0
                    
                    processes.append({
                        "name": info.get('name', '?'),
                        "pid": info['pid'],
                        "cpu": round(info.get('cpu_percent', 0) or 0, 1),
                        "memory_mb": mem_mb,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            return processes[:limit]
        except Exception:
            return []
    
    def kill_process(self, pid):
        """
        Убить процесс по PID.
        
        Args:
            pid: ID процесса
        
        Returns:
            bool: успех
        """
        if not PSUTIL_AVAILABLE:
            return False
        
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            time.sleep(1)
            
            # Добиваем, если не умер
            if proc.is_running():
                proc.kill()
            
            return True
        except Exception as e:
            print(f"⚠️ Ошибка kill_process: {e}")
            return False
    
    def kill_process_by_name(self, name):
        """
        Убить все процессы с указанным именем.
        
        Args:
            name: имя процесса
        
        Returns:
            int: количество убитых
        """
        if not PSUTIL_AVAILABLE:
            return 0
        
        killed = 0
        name_lower = name.lower()
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info.get('name', '')
                if proc_name and name_lower in proc_name.lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return killed
    
    # ============================================================
    # 7. ЭНЕРГОСБЕРЕЖЕНИЕ (только Windows)
    # ============================================================
    
    def prevent_sleep(self):
        """
        Запретить переход в сон (Windows).
        
        Returns:
            bool: успех
        """
        if not self.is_windows:
            return False
        
        try:
            # powercfg /change standby-timeout-ac 0
            result = subprocess.run(
                ["powercfg", "/change", "standby-timeout-ac", "0"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def allow_sleep(self):
        """Разрешить переход в сон"""
        if not self.is_windows:
            return False
        
        try:
            result = subprocess.run(
                ["powercfg", "/change", "standby-timeout-ac", "30"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def restart_computer(self, delay=60):
        """
        Перезагрузить компьютер.
        
        ВНИМАНИЕ: требует прав администратора!
        
        Args:
            delay: задержка в секундах
        """
        if not self.is_admin:
            return False
        
        try:
            if self.is_windows:
                subprocess.run(["shutdown", "/r", "/t", str(delay)], check=False)
            else:
                subprocess.run(["shutdown", "-r", f"+{delay // 60}"], check=False)
            return True
        except Exception:
            return False
    
    def shutdown_computer(self, delay=60):
        """Выключить компьютер"""
        if not self.is_admin:
            return False
        
        try:
            if self.is_windows:
                subprocess.run(["shutdown", "/s", "/t", str(delay)], check=False)
            else:
                subprocess.run(["shutdown", "-h", f"+{delay // 60}"], check=False)
            return True
        except Exception:
            return False
    
    def cancel_shutdown(self):
        """Отменить запланированное выключение"""
        try:
            if self.is_windows:
                subprocess.run(["shutdown", "/a"], check=False)
            else:
                subprocess.run(["shutdown", "-c"], check=False)
            return True
        except Exception:
            return False
    
    # ============================================================
    # 8. СЕТЬ
    # ============================================================
    
    def get_network_info(self):
        """
        Получить информацию о сети.
        
        Returns:
            dict: {hostname, ip, mac, interfaces}
        """
        info = {
            "hostname": platform.node(),
            "interfaces": [],
        }
        
        if not PSUTIL_AVAILABLE:
            return info
        
        try:
            # IP-адреса
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for iface_name, iface_addrs in addrs.items():
                iface_info = {
                    "name": iface_name,
                    "is_up": stats.get(iface_name, {}).isup if iface_name in stats else False,
                    "addresses": [],
                }
                
                for addr in iface_addrs:
                    if addr.family == 2:  # IPv4
                        iface_info["addresses"].append({
                            "type": "IPv4",
                            "address": addr.address,
                            "netmask": addr.netmask,
                        })
                    elif addr.family == 23:  # IPv6
                        iface_info["addresses"].append({
                            "type": "IPv6",
                            "address": addr.address,
                        })
                    elif addr.family == 17:  # MAC
                        iface_info["mac"] = addr.address
                
                info["interfaces"].append(iface_info)
        except Exception:
            pass
        
        return info
    
    def get_public_ip(self):
        """
        Получить публичный IP.
        
        Returns:
            str или None
        """
        try:
            import requests
            response = requests.get("https://api.ipify.org?format=json", timeout=10)
            if response.status_code == 200:
                return response.json().get("ip")
        except Exception:
            pass
        return None
    
    # ============================================================
    # 9. ФОРМАТИРОВАНИЕ
    # ============================================================
    
    def format_status(self):
        """Форматировать статус системы"""
        info = self.get_device_info()
        battery = self.get_battery_info()
        
        lines = ["🔧 СИСТЕМА:"]
        lines.append(f"  ОС: {info.get('os', '?')} {info.get('os_release', '')}")
        
        if info.get("windows_edition"):
            lines.append(f"  Редакция: {info['windows_edition']}")
        
        lines.append(f"  Машина: {info.get('machine', '?')}")
        lines.append(f"  Хост: {info.get('hostname', '?')}")
        lines.append(f"  Python: {info.get('python', '?')}")
        lines.append(f"  Админ: {'✅' if info.get('is_admin') else '❌'}")
        
        if info.get("cpu_count"):
            lines.append(f"  CPU: {info['cpu_count']} ядер")
        
        if info.get("ram_total_gb"):
            lines.append(f"  RAM: {info['ram_total_gb']}GB")
        
        if info.get("disk_total_gb"):
            lines.append(f"  Disk: {info['disk_free_gb']}/{info['disk_total_gb']}GB свободно")
        
        if info.get("uptime_hours"):
            lines.append(f"  Uptime: {info['uptime_hours']}ч")
        
        # Батарея
        if battery:
            plugged = "🔌" if battery.get("plugged") else "🔋"
            time_left = battery.get("time_left", "")
            lines.append(f"  {plugged} Батарея: {battery['percent']}%" + (f" ({time_left})" if time_left else ""))
        
        return "\n".join(lines)
    
    def format_processes(self, limit=10):
        """Форматировать топ процессов"""
        processes = self.get_top_processes(limit)
        
        if not processes:
            return "❌ Не удалось получить процессы"
        
        lines = [f"📊 ТОП {len(processes)} ПРОЦЕССОВ ПО CPU:"]
        lines.append("")
        
        for p in processes:
            lines.append(f"  • {p['name']} (PID {p['pid']})")
            lines.append(f"    CPU: {p['cpu']}% | RAM: {p['memory_mb']}MB")
        
        return "\n".join(lines)
    
    def format_network(self):
        """Форматировать информацию о сети"""
        info = self.get_network_info()
        
        lines = [f"🌐 СЕТЬ ({info.get('hostname', '?')}):"]
        lines.append("")
        
        for iface in info.get("interfaces", []):
            status = "🟢" if iface.get("is_up") else "🔴"
            lines.append(f"  {status} {iface['name']}")
            
            for addr in iface.get("addresses", []):
                lines.append(f"      {addr['type']}: {addr['address']}")
            
            if iface.get("mac"):
                lines.append(f"      MAC: {iface['mac']}")
        
        # Публичный IP
        public_ip = self.get_public_ip()
        if public_ip:
            lines.append("")
            lines.append(f"  🌍 Публичный IP: {public_ip}")
        
        return "\n".join(lines)
    
    def format_admin_status(self):
        """Форматировать статус прав администратора"""
        if self.is_admin:
            return "✅ Права администратора: есть"
        
        return self.request_admin_hint()

# ============================================================
# 10. ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================

system_control = SystemControl()

# ============================================================
# 11. ЗАГРУЗКА
# ============================================================

print("🔧 Управление системой загружено (PC)")
print(f"💻 ОС: {system_control.os_type} {platform.release()}")
print(f"👤 Админ: {'✅' if system_control.is_admin else '❌'}")
print(f"📦 psutil: {'✅' if PSUTIL_AVAILABLE else '❌'}")

if PSUTIL_AVAILABLE:
    info = system_control.get_device_info()
    print(f"🖥 Хост: {info.get('hostname', '?')}")
    print(f"💻 CPU: {info.get('cpu_count', '?')} ядер")
    print(f"🧠 RAM: {info.get('ram_total_gb', '?')}GB")