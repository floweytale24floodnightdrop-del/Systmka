"""Управление Wi-Fi — Windows-версия (замена Android cmd/svc/dumpsys)"""

import os
import re
import subprocess
import platform
import time
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

# Кэш сетей (сканирование медленное)
_networks_cache = {"data": [], "time": 0}
CACHE_TTL = 30  # 30 секунд

# ============================================================
# 2. ОСНОВНОЙ КЛАСС
# ============================================================

class WifiManager:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.has_netsh = self._check_netsh()
    
    def _check_netsh(self):
        """Проверить, доступен ли netsh"""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_netsh(self, *args, timeout=15):
        """
        Запустить netsh с аргументами.
        
        Args:
            *args: аргументы netsh (например, "wlan", "show", "interfaces")
        
        Returns:
            str: stdout или None
        """
        if not self.has_netsh:
            return None
        
        try:
            result = subprocess.run(
                ["netsh"] + list(args),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="cp866",  # кодировка консоли Windows
                errors="ignore"
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            print(f"⚠️ netsh timeout: {' '.join(args)}")
            return None
        except Exception as e:
            print(f"⚠️ Ошибка netsh: {e}")
            return None
    
    # ============================================================
    # 3. СТАТУС WI-FI
    # ============================================================
    
    def is_wifi_enabled(self):
        """
        Проверить, включён ли Wi-Fi адаптер.
        
        Returns:
            bool
        """
        output = self._run_netsh("wlan", "show", "interfaces")
        if not output:
            return False
        
        # Ищем "State : connected" или "State : disconnected"
        # Если адаптер отключён — "State : disconnected" и нет строки "SSID"
        if "State" in output or "Состояние" in output:
            if "connected" in output.lower() or "подключен" in output.lower():
                return True
            # Если Wi-Fi включён, но не подключён — тоже enabled
            if "disconnected" in output.lower() or "отключен" in output.lower():
                return True
            if "hardware off" in output.lower() or "аппаратное отключение" in output.lower():
                return False
        
        return False
    
    def is_wifi_connected(self):
        """Проверить, подключён ли Wi-Fi к сети"""
        output = self._run_netsh("wlan", "show", "interfaces")
        if not output:
            return False
        
        output_lower = output.lower()
        return ("state" in output_lower and "connected" in output_lower) or \
               ("состояние" in output_lower and "подключен" in output_lower)
    
    def get_wifi_status(self):
        """
        Получить полный статус Wi-Fi.
        
        Returns:
            dict: {enabled, connected, ssid, signal, bssid, channel, speed}
        """
        output = self._run_netsh("wlan", "show", "interfaces")
        if not output:
            return {"enabled": False, "connected": False}
        
        status = {
            "enabled": self.is_wifi_enabled(),
            "connected": self.is_wifi_connected(),
            "ssid": None,
            "bssid": None,
            "signal": None,
            "channel": None,
            "speed": None,
        }
        
        # Парсим SSID
        ssid_match = re.search(r'^\s*SSID\s*:\s*(.+?)$', output, re.MULTILINE)
        if ssid_match:
            status["ssid"] = ssid_match.group(1).strip()
        
        # BSSID
        bssid_match = re.search(r'BSSID\s*:\s*(.+?)$', output, re.MULTILINE)
        if bssid_match:
            status["bssid"] = bssid_match.group(1).strip()
        
        # Сигнал
        signal_match = re.search(r'(?:Signal|Сигнал)\s*:\s*(\d+)%', output)
        if signal_match:
            status["signal"] = int(signal_match.group(1))
        
        # Канал
        channel_match = re.search(r'(?:Channel|Канал)\s*:\s*(\d+)', output)
        if channel_match:
            status["channel"] = int(channel_match.group(1))
        
        # Скорость
        speed_match = re.search(r'(?:Receive rate|Скорость приема)\s*:\s*([\d.]+)', output)
        if speed_match:
            status["speed"] = speed_match.group(1)
        
        return status
    
    # ============================================================
    # 4. ВКЛЮЧЕНИЕ / ОТКЛЮЧЕНИЕ WI-FI
    # ============================================================
    
    def _get_wifi_interface_name(self):
        """
        Получить имя Wi-Fi интерфейса в Windows.
        
        Returns:
            str: имя интерфейса (например, "Wi-Fi") или None
        """
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="cp866",
                errors="ignore"
            )
            
            if result.returncode != 0:
                return None
            
            # Ищем строку с "Wi-Fi" или "Беспроводная сеть"
            for line in result.stdout.split("\n"):
                line_lower = line.lower()
                if "wi-fi" in line_lower or "беспроводн" in line_lower or "wlan" in line_lower:
                    # Формат: "Enabled   Connected   Wi-Fi   Wi-Fi"
                    parts = line.split()
                    if len(parts) >= 4:
                        return parts[3]
                    elif len(parts) >= 3:
                        return parts[2]
            
            return "Wi-Fi"  # fallback
        except Exception:
            return "Wi-Fi"
    
    def enable_wifi(self):
        """
        Включить Wi-Fi адаптер.
        
        ВНИМАНИЕ: требует прав администратора!
        
        Returns:
            bool: успех
        """
        interface = self._get_wifi_interface_name()
        
        try:
            result = subprocess.run(
                ["netsh", "interface", "set", "interface", interface, "enabled"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print(f"✅ Wi-Fi включён: {interface}")
                return True
            else:
                print(f"⚠️ Не удалось включить Wi-Fi. Нужны права администратора?")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка включения Wi-Fi: {e}")
            return False
    
    def disable_wifi(self):
        """
        Выключить Wi-Fi адаптер.
        
        ВНИМАНИЕ: требует прав администратора!
        
        Returns:
            bool: успех
        """
        interface = self._get_wifi_interface_name()
        
        try:
            result = subprocess.run(
                ["netsh", "interface", "set", "interface", interface, "disabled"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print(f"✅ Wi-Fi выключен: {interface}")
                return True
            else:
                print(f"⚠️ Не удалось выключить Wi-Fi. Нужны права администратора?")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка выключения Wi-Fi: {e}")
            return False
    
    # ============================================================
    # 5. СКАНИРОВАНИЕ СЕТЕЙ
    # ============================================================
    
    def scan_networks(self, force=False):
        """
        Сканировать доступные Wi-Fi сети.
        
        Args:
            force: игнорировать кэш
        
        Returns:
            list: [{ssid, signal, auth, encryption, channel}, ...]
        """
        # Проверяем кэш
        now = time.time()
        if not force and (now - _networks_cache["time"]) < CACHE_TTL:
            return _networks_cache["data"]
        
        # Запускаем сканирование (на Windows не всегда нужно, но полезно)
        self._run_netsh("wlan", "show", "networks", "mode=bssid", timeout=10)
        time.sleep(1)
        
        output = self._run_netsh("wlan", "show", "networks", timeout=15)
        if not output:
            return []
        
        networks = []
        current = {}
        
        for line in output.split("\n"):
            line = line.strip()
            
            # SSID
            ssid_match = re.match(r'^SSID\s+\d+\s*:\s*(.*)$', line)
            if ssid_match:
                # Сохраняем предыдущую сеть
                if current.get("ssid"):
                    networks.append(current)
                
                current = {"ssid": ssid_match.group(1).strip()}
                continue
            
            # Signal
            if current:
                signal_match = re.match(r'^(?:Signal|Сигнал)\s*:\s*(\d+)%', line)
                if signal_match:
                    current["signal"] = int(signal_match.group(1))
                    continue
                
                # Authentication
                auth_match = re.match(r'^(?:Authentication|Проверка подлинности)\s*:\s*(.+)$', line)
                if auth_match:
                    current["auth"] = auth_match.group(1).strip()
                    continue
                
                # Encryption
                enc_match = re.match(r'^(?:Encryption|Шифрование)\s*:\s*(.+)$', line)
                if enc_match:
                    current["encryption"] = enc_match.group(1).strip()
                    continue
                
                # Channel
                chan_match = re.match(r'^(?:Channel|Канал)\s*:\s*(\d+)', line)
                if chan_match:
                    current["channel"] = int(chan_match.group(1))
                    continue
        
        # Добавляем последнюю сеть
        if current.get("ssid"):
            networks.append(current)
        
        # Кэшируем
        _networks_cache["data"] = networks
        _networks_cache["time"] = now
        
        return networks
    
    def get_best_network(self):
        """
        Найти сеть с лучшим сигналом.
        
        Returns:
            dict или None: {ssid, signal, ...}
        """
        networks = self.scan_networks()
        if not networks:
            return None
        
        # Только сети с известным сигналом
        with_signal = [n for n in networks if n.get("signal") is not None]
        if not with_signal:
            return None
        
        return max(with_signal, key=lambda n: n.get("signal", 0))
    
    # ============================================================
    # 6. ПОДКЛЮЧЕНИЕ К СЕТИ
    # ============================================================
    
    def connect_to_network(self, ssid, password=None):
        """
        Подключиться к Wi-Fi сети.
        
        Args:
            ssid: имя сети
            password: пароль (если None — сеть открыта или профиль уже сохранён)
        
        Returns:
            bool: успех
        """
        # Если пароль не указан — пробуем подключиться через существующий профиль
        if password is None:
            output = self._run_netsh("wlan", "connect", f"name={ssid}", f"ssid={ssid}", timeout=30)
            if output and ("successfully" in output.lower() or "успешно" in output.lower()):
                return True
            
            # Проверяем, подключились ли
            time.sleep(3)
            return self.is_wifi_connected() and self.get_wifi_status().get("ssid") == ssid
        
        # Если пароль указан — создаём профиль через XML
        return self._connect_with_password(ssid, password)
    
    def _connect_with_password(self, ssid, password):
        """
        Создать профиль с паролем и подключиться.
        
        Args:
            ssid: имя сети
            password: пароль
        
        Returns:
            bool: успех
        """
        # XML-шаблон профиля WPA2-PSK
        profile_xml = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>'''
        
        # Сохраняем XML во временный файл
        temp_xml = os.path.join(os.environ.get("TEMP", "."), f"wifi_profile_{ssid}.xml")
        
        try:
            with open(temp_xml, "w", encoding="utf-8") as f:
                f.write(profile_xml)
            
            # Добавляем профиль
            result = subprocess.run(
                ["netsh", "wlan", "add", "profile", f"filename={temp_xml}", "user=current"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Удаляем временный файл
            try:
                os.remove(temp_xml)
            except Exception:
                pass
            
            if result.returncode != 0:
                print(f"⚠️ Не удалось добавить профиль: {result.stderr[:100]}")
                return False
            
            # Подключаемся
            output = self._run_netsh("wlan", "connect", f"name={ssid}", f"ssid={ssid}", timeout=30)
            
            # Проверяем через 3 секунды
            time.sleep(3)
            return self.is_wifi_connected() and self.get_wifi_status().get("ssid") == ssid
            
        except Exception as e:
            print(f"⚠️ Ошибка подключения к {ssid}: {e}")
            return False
    
    def disconnect(self):
        """
        Отключиться от текущей Wi-Fi сети.
        
        Returns:
            bool: успех
        """
        # Отключаемся от всех
        output = self._run_netsh("wlan", "disconnect", timeout=15)
        
        time.sleep(2)
        return not self.is_wifi_connected()
    
    # ============================================================
    # 7. ПРОФИЛИ
    # ============================================================
    
    def list_profiles(self):
        """
        Список сохранённых Wi-Fi профилей.
        
        Returns:
            list: список имён профилей
        """
        output = self._run_netsh("wlan", "show", "profiles", timeout=10)
        if not output:
            return []
        
        profiles = []
        for line in output.split("\n"):
            # Формат: "    All User Profile     : MyNetwork"
            match = re.search(r':\s*(.+)$', line)
            if match and ("profile" in line.lower() or "профиль" in line.lower()):
                profile_name = match.group(1).strip()
                if profile_name and profile_name not in profiles:
                    profiles.append(profile_name)
        
        return profiles
    
    def delete_profile(self, ssid):
        """Удалить сохранённый профиль"""
        result = subprocess.run(
            ["netsh", "wlan", "delete", "profile", f"name={ssid}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    
    # ============================================================
    # 8. ФОРМАТИРОВАНИЕ
    # ============================================================
    
    def format_networks(self, limit=15):
        """
        Форматировать список доступных сетей.
        
        Returns:
            str
        """
        networks = self.scan_networks()
        
        if not networks:
            return "📶 Wi-Fi: Нет доступных сетей"
        
        # Сортируем по сигналу
        networks_sorted = sorted(
            networks,
            key=lambda n: n.get("signal", 0),
            reverse=True
        )
        
        lines = [f"📶 ДОСТУПНЫЕ СЕТИ Wi-Fi ({len(networks_sorted)}):"]
        lines.append("")
        
        for network in networks_sorted[:limit]:
            signal = network.get("signal", 0)
            
            # Иконка по силе
            if signal >= 80:
                icon = "🟢"
            elif signal >= 60:
                icon = "🟡"
            elif signal >= 40:
                icon = "🟠"
            else:
                icon = "🔴"
            
            ssid = network.get("ssid", "?")
            auth = network.get("auth", "?")
            
            lines.append(f"  {icon} {ssid}")
            lines.append(f"      Сигнал: {signal}% | Защита: {auth}")
        
        if len(networks_sorted) > limit:
            lines.append(f"\n... и ещё {len(networks_sorted) - limit}")
        
        return "\n".join(lines)
    
    def format_status(self):
        """
        Форматировать статус Wi-Fi.
        
        Returns:
            str
        """
        status = self.get_wifi_status()
        
        lines = ["📡 СТАТУС Wi-Fi:"]
        lines.append("")
        
        if not status.get("enabled"):
            lines.append("❌ Wi-Fi выключен")
            return "\n".join(lines)
        
        if not status.get("connected"):
            lines.append("⚠️ Wi-Fi включён, но не подключён")
            return "\n".join(lines)
        
        lines.append("✅ Подключён")
        lines.append(f"  SSID: {status.get('ssid', '?')}")
        
        if status.get("signal"):
            lines.append(f"  Сигнал: {status['signal']}%")
        
        if status.get("channel"):
            lines.append(f"  Канал: {status['channel']}")
        
        if status.get("bssid"):
            lines.append(f"  BSSID: {status['bssid']}")
        
        if status.get("speed"):
            lines.append(f"  Скорость: {status['speed']} Mbps")
        
        return "\n".join(lines)
    
    def format_profiles(self):
        """Форматировать список сохранённых профилей"""
        profiles = self.list_profiles()
        
        if not profiles:
            return "📋 Нет сохранённых Wi-Fi профилей"
        
        lines = [f"📋 СОХРАНЁННЫЕ ПРОФИЛИ ({len(profiles)}):"]
        for p in profiles:
            lines.append(f"  • {p}")
        
        return "\n".join(lines)
    
    def auto_connect_best(self):
        """
        Автоматически подключиться к сети с лучшим сигналом
        (только если у неё есть сохранённый профиль).
        
        Returns:
            tuple: (success, ssid)
        """
        best = self.get_best_network()
        if not best:
            return False, None
        
        ssid = best.get("ssid")
        if not ssid:
            return False, None
        
        # Проверяем, есть ли профиль
        profiles = self.list_profiles()
        if ssid not in profiles:
            print(f"⚠️ Нет профиля для {ssid}")
            return False, ssid
        
        success = self.connect_to_network(ssid)
        return success, ssid

# ============================================================
# 9. ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================

wifi_manager = WifiManager()

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("📶 Управление Wi-Fi загружено (PC / Windows)")
print(f"💻 ОС: {platform.system()} {platform.release()}")
print(f"🔧 netsh: {'✅' if wifi_manager.has_netsh else '❌'}")

if wifi_manager.has_netsh:
    status = wifi_manager.get_wifi_status()
    if status.get("connected"):
        print(f"✅ Wi-Fi подключён: {status.get('ssid')}")
    elif status.get("enabled"):
        print("⚠️ Wi-Fi включён, но не подключён")
    else:
        print("❌ Wi-Fi выключен")