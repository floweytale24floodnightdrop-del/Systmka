"""Интеграция с Maigret — реальный поиск информации о пользователе по username"""

import os
import re
import json
import time
import tempfile
import subprocess
import requests
from datetime import datetime
from urllib.parse import quote

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

SHERLOCK_FILE = "sherlock_results.json"

TEMP_DIR = os.path.join(tempfile.gettempdir(), "systmka_maigret")
os.makedirs(TEMP_DIR, exist_ok=True)

# Проверка доступности maigret
try:
    result = subprocess.run(
        ["maigret", "--version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    MAIGRET_AVAILABLE = result.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired):
    MAIGRET_AVAILABLE = False
    print("⚠️ maigret не установлен — поиск по username недоступен")

# ============================================================
# 2. ДАННЫЕ
# ============================================================

sherlock_data = {
    "users": {},  # {username: {"platforms": {}, "phone": None, "email": None, "found_at": str}}
    "searches": [],
    "stats": {
        "total_searches": 0,
        "found_phones": 0,
        "found_emails": 0,
    },
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_sherlock_data():
    """Сохранить данные поиска"""
    try:
        with open(SHERLOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(sherlock_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения: {e}")
        return False

def load_sherlock_data():
    """Загрузить данные поиска"""
    global sherlock_data
    try:
        if os.path.exists(SHERLOCK_FILE):
            with open(SHERLOCK_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    sherlock_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки: {e}")
        return False

load_sherlock_data()

# ============================================================
# 4. ПОИСК ЧЕРЕЗ MAIGRET
# ============================================================

def search_maigret(username, timeout=120):
    """
    Поиск через Maigret.
    
    Args:
        username: ник для поиска
        timeout: таймаут в секундах
    
    Returns:
        dict: {username, platforms, found, errors}
    """
    results = {
        "username": username,
        "platforms": {},
        "found": [],
        "errors": [],
    }
    
    if not MAIGRET_AVAILABLE:
        results["errors"].append("maigret не установлен")
        # Fallback — простой HTTP-скан
        return search_fallback(username)
    
    try:
        # Папка для результатов этого запуска
        output_dir = os.path.join(TEMP_DIR, f"maigret_{username}_{int(time.time())}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Команда maigret с JSON-выводом
        cmd = [
            "maigret", username,
            "--json", "simple",
            "--folderoutput", output_dir,
            "--no-progressbar",
            "--no-color",
            "--timeout", "10",
            "--max-connections", "20",
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore"
            )
        except subprocess.TimeoutExpired:
            results["errors"].append(f"Таймаут поиска ({timeout}с)")
            return results
        
        # Ищем JSON-файл в output_dir
        json_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".json"):
                    json_files.append(os.path.join(root, f))
        
        if not json_files:
            results["errors"].append("Maigret не создал JSON-отчёт")
            return results
        
        # Читаем первый JSON
        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Парсим результаты
        # Формат maigret simple JSON:
        # {username: {site_name: {url_user: "...", status: {...}, ...}}}
        if username in data:
            sites = data[username]
        else:
            # Может быть один ключ — берём первый
            first_key = list(data.keys())[0] if data else None
            sites = data.get(first_key, {}) if first_key else {}
        
        for site_name, site_data in sites.items():
            if not isinstance(site_data, dict):
                continue
            
            status = site_data.get("status", {})
            if isinstance(status, dict):
                status_str = status.get("status", "unknown")
            else:
                status_str = str(status)
            
            exists = status_str in ("claimed", "Found", "found") or site_data.get("url_user")
            
            results["platforms"][site_name] = {
                "url": site_data.get("url_user") or site_data.get("url_main", ""),
                "exists": exists,
                "status": status_str,
            }
            
            if exists:
                results["found"].append(site_name)
        
        # Удаляем временную папку
        try:
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        except Exception:
            pass
    
    except Exception as e:
        results["errors"].append(f"Ошибка maigret: {str(e)[:100]}")
        return search_fallback(username)
    
    return results

def search_fallback(username):
    """
    Fallback — прямой HTTP-скан основных платформ.
    
    Returns:
        dict: {username, platforms, found, errors}
    """
    results = {
        "username": username,
        "platforms": {},
        "found": [],
        "errors": ["Использован fallback"],
    }
    
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "VK": f"https://vk.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "Twitter": f"https://twitter.com/{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Tumblr": f"https://{username}.tumblr.com",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "Telegram": f"https://t.me/{username}",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for platform, url in platforms.items():
        try:
            response = requests.get(url, headers=headers, timeout=5)
            exists = response.status_code == 200
            
            # Проверяем "not found"
            if platform in ("Instagram", "TikTok") and exists:
                text_lower = response.text.lower()
                if "not found" in text_lower or "page not found" in text_lower:
                    exists = False
            
            results["platforms"][platform] = {
                "url": url,
                "exists": exists,
                "status": f"HTTP {response.status_code}",
            }
            
            if exists:
                results["found"].append(platform)
        except requests.exceptions.Timeout:
            results["platforms"][platform] = {
                "url": url,
                "exists": False,
                "status": "timeout",
            }
        except Exception:
            results["platforms"][platform] = {
                "url": url,
                "exists": False,
                "status": "error",
            }
        
        time.sleep(0.3)
    
    return results

def search_sherlock(username, timeout=120):
    """
    Главная функция поиска (совместимость с прежним API).
    Использует Maigret.
    """
    results = search_maigret(username, timeout)
    
    # Сохраняем в БД
    if username not in sherlock_data["users"]:
        sherlock_data["users"][username] = {
            "platforms": {},
            "phone": None,
            "email": None,
            "found_at": datetime.now().isoformat(),
        }
    
    sherlock_data["users"][username]["platforms"] = results["platforms"]
    sherlock_data["users"][username]["found_at"] = datetime.now().isoformat()
    
    sherlock_data["searches"].append({
        "username": username,
        "platforms": len(results["platforms"]),
        "found": len(results["found"]),
        "time": datetime.now().isoformat(),
    })
    sherlock_data["stats"]["total_searches"] += 1
    
    save_sherlock_data()
    return results

# ============================================================
# 5. ПОИСК НОМЕРА ТЕЛЕФОНА
# ============================================================

def search_phone_number(phone):
    """
    Поиск по номеру телефона.
    
    Работает только с публичными источниками:
    - phonenumbers (базовая инфо)
    - Telegram (проверка)
    """
    results = {
        "phone": phone,
        "found": False,
        "data": {},
        "sources": [],
    }
    
    phone_clean = re.sub(r'[^0-9+]', '', phone)
    
    # 1. phonenumbers
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone
        
        parsed = phonenumbers.parse(phone_clean, "RU")
        if phonenumbers.is_valid_number(parsed):
            results["found"] = True
            results["data"]["valid"] = True
            results["data"]["country"] = geocoder.description_for_number(parsed, "ru")
            results["data"]["carrier"] = carrier.name_for_number(parsed, "ru")
            tz = list(timezone.time_zones_for_number(parsed))
            results["data"]["timezone"] = tz[0] if tz else None
            results["sources"].append("phonenumbers")
    except Exception as e:
        print(f"⚠️ phonenumbers: {e}")
    
    # 2. Telegram
    try:
        response = requests.get(
            f"https://t.me/{phone_clean}",
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if response.status_code == 200:
            results["data"]["telegram"] = f"https://t.me/{phone_clean}"
            results["sources"].append("telegram")
    except Exception:
        pass
    
    # Обновляем статистику
    if results["found"]:
        sherlock_data["stats"]["found_phones"] += 1
        save_sherlock_data()
    
    return results

# ============================================================
# 6. ПОИСК EMAIL
# ============================================================

def search_email(email):
    """
    Поиск по email.
    
    Работает с:
    - Gravatar (публичный)
    - Have I Been Pwned (базовый запрос)
    """
    results = {
        "email": email,
        "found": False,
        "data": {},
        "sources": [],
    }
    
    if not email or "@" not in email:
        return results
    
    # 1. Gravatar
    try:
        import hashlib
        hash_md5 = hashlib.md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/{hash_md5}.json"
        
        response = requests.get(
            gravatar_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code == 200:
            data = response.json()
            results["found"] = True
            results["data"]["gravatar"] = data.get("entry", [])
            results["sources"].append("gravatar")
    except Exception as e:
        print(f"⚠️ Gravatar: {e}")
    
    # 2. Have I Been Pwned
    try:
        response = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            timeout=10,
            headers={"User-Agent": "Systmka-OSINT"}
        )
        
        if response.status_code == 200:
            results["found"] = True
            results["data"]["breaches"] = response.json()
            results["sources"].append("hibp")
        elif response.status_code == 429:
            print("⚠️ HIBP: лимит запросов")
        # 401 = нужен API-ключ, 404 = нет утечек
    except Exception:
        pass
    
    # Обновляем статистику
    if results["found"]:
        sherlock_data["stats"]["found_emails"] += 1
        save_sherlock_data()
    
    return results

# ============================================================
# 7. КОМПЛЕКСНЫЙ ПОИСК
# ============================================================

def full_sherlock_search(username, search_phone=True, search_email=True):
    """
    Полный поиск по username: платформы + телефон + email.
    
    Returns:
        dict: {username, platforms, found, phone, email, timestamp}
    """
    results = {
        "username": username,
        "platforms": {},
        "found": [],
        "phone": None,
        "email": None,
        "timestamp": datetime.now().isoformat(),
    }
    
    # 1. Поиск по платформам
    sherlock_results = search_sherlock(username)
    results["platforms"] = sherlock_results["platforms"]
    results["found"] = sherlock_results["found"]
    
    # 2. Поиск телефона (если найдены платформы)
    if search_phone and results["platforms"]:
        for platform, data in results["platforms"].items():
            if data.get("exists") and data.get("url"):
                try:
                    response = requests.get(
                        data["url"],
                        timeout=5,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    phone_match = re.search(
                        r'\+?\d[\d\s\-()]{8,15}\d',
                        response.text
                    )
                    if phone_match:
                        phone = phone_match.group()
                        results["phone"] = search_phone_number(phone)
                        break
                except Exception:
                    pass
    
    # 3. Поиск email (по username)
    if search_email:
        possible_emails = [
            f"{username}@gmail.com",
            f"{username}@mail.ru",
            f"{username}@yandex.ru",
            f"{username}@outlook.com",
            f"{username}@icloud.com",
        ]
        
        for email in possible_emails:
            email_data = search_email(email)
            if email_data.get("found"):
                results["email"] = email_data
                break
    
    # Сохраняем в БД
    if username not in sherlock_data["users"]:
        sherlock_data["users"][username] = {
            "platforms": {},
            "phone": None,
            "email": None,
            "found_at": datetime.now().isoformat(),
        }
    
    sherlock_data["users"][username]["platforms"] = results["platforms"]
    if results.get("phone"):
        sherlock_data["users"][username]["phone"] = results["phone"]
    if results.get("email"):
        sherlock_data["users"][username]["email"] = results["email"]
    
    save_sherlock_data()
    return results

# ============================================================
# 8. ФОРМАТИРОВАНИЕ
# ============================================================

def format_sherlock_results(results):
    """Форматировать результаты поиска"""
    if not results:
        return "❌ Нет результатов"
    
    lines = [
        f"🔍 ПОИСК ПО: {results.get('username', '?')}",
        "─" * 40,
        f"📊 Найдено платформ: {len(results.get('found', []))}",
    ]
    
    # Платформы
    if results.get("found"):
        lines.append("\n🌍 НАЙДЕНО НА:")
        for platform in results.get("found", [])[:10]:
            url = results.get("platforms", {}).get(platform, {}).get("url", "")
            lines.append(f"  • {platform}: {url}")
        
        if len(results["found"]) > 10:
            lines.append(f"  ... и ещё {len(results['found']) - 10}")
    
    # Телефон
    if results.get("phone"):
        phone_data = results.get("phone", {})
        lines.append("\n📞 ТЕЛЕФОН:")
        lines.append(f"  Номер: {phone_data.get('phone', '?')}")
        if phone_data.get("data", {}).get("carrier"):
            lines.append(f"  Оператор: {phone_data['data']['carrier']}")
        if phone_data.get("data", {}).get("location"):
            lines.append(f"  Локация: {phone_data['data']['location']}")
    
    # Email
    if results.get("email"):
        email_data = results.get("email", {})
        lines.append("\n📧 EMAIL:")
        lines.append(f"  {email_data.get('email', '?')}")
    
    # Ошибки
    if results.get("errors"):
        lines.append("\n⚠️ ОШИБКИ:")
        for err in results["errors"][:3]:
            lines.append(f"  • {err}")
    
    lines.append(f"\n🕐 Найдено: {results.get('timestamp', '?')[:16]}")
    
    return "\n".join(lines)

def get_user_phone(username):
    """Получить телефон пользователя из БД"""
    if username in sherlock_data["users"]:
        return sherlock_data["users"][username].get("phone")
    return None

def get_user_platforms(username):
    """Получить все платформы пользователя"""
    if username in sherlock_data["users"]:
        return sherlock_data["users"][username].get("platforms", {})
    return {}

def get_sherlock_stats():
    """Получить статистику поиска"""
    return {
        "total_searches": sherlock_data["stats"]["total_searches"],
        "found_phones": sherlock_data["stats"]["found_phones"],
        "found_emails": sherlock_data["stats"]["found_emails"],
        "users_in_db": len(sherlock_data["users"]),
    }

def format_sherlock_stats():
    """Форматировать статистику"""
    stats = get_sherlock_stats()
    lines = [
        "🔍 СТАТИСТИКА ПОИСКА:",
        f"📊 Всего поисков: {stats['total_searches']}",
        f"📞 Найдено телефонов: {stats['found_phones']}",
        f"📧 Найдено email: {stats['found_emails']}",
        f"👤 Пользователей в БД: {stats['users_in_db']}",
    ]
    return "\n".join(lines)

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("🔍 Модуль поиска по username загружен")
print(f"📦 maigret: {'✅' if MAIGRET_AVAILABLE else '❌ (использую fallback)'}")
print(f"📊 Поисков: {sherlock_data['stats']['total_searches']}")