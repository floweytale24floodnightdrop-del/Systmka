"""OSINT Engine — 50+ методов сбора данных: телефоны, email, username, ФИО"""

import os
import re
import json
import time
import random
import hashlib
import requests
from datetime import datetime
from urllib.parse import quote

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ
# ============================================================

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    print("⚠️ phonenumbers не установлен")

# ============================================================
# 3. ИМПОРТЫ ИЗ ДРУГИХ OSINT МОДУЛЕЙ
# ============================================================

try:
    from osint_phone_email import search_phone_methods, search_email_methods
except ImportError:
    def search_phone_methods(phone):
        return {"found": False, "data": {}, "sources": []}
    def search_email_methods(email):
        return {"found": False, "data": {}, "sources": []}

try:
    from osint_username_fio import (
        search_username_methods, search_fio_methods, search_breach_methods
    )
except ImportError:
    def search_username_methods(username):
        return {"found": False, "data": {}, "sources": []}
    def search_fio_methods(fio):
        return {"found": False, "data": {}, "sources": []}
    def search_breach_methods(query):
        return {"found": False, "data": {}, "sources": []}

# ============================================================
# 4. НАСТРОЙКИ
# ============================================================

OSINT_FILE = "osint_data.json"
DEEP_OSINT_FILE = "deep_osint_data.json"
ACCOUNTS_FILE = "generated_accounts.json"

# Папка для ликов
LEAK_DIR = "leaks"
os.makedirs(LEAK_DIR, exist_ok=True)

# Заголовки для запросов
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

# Таймауты
TIMEOUT_SHORT = 5
TIMEOUT_MEDIUM = 10
TIMEOUT_LONG = 30

# ============================================================
# 5. ДАННЫЕ
# ============================================================

osint_data = {
    "people": {},
    "searches": [],
    "reports": [],
}

deep_osint_data = {
    "people": {},
    "last_update": None,
    "total_people": 0,
}

accounts = []

# ============================================================
# 6. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def _load_json(file_path, default):
    """Безопасно загрузить JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and isinstance(default, dict):
                    default.update(loaded)
                    return default
                elif isinstance(loaded, list) and isinstance(default, list):
                    return loaded
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {file_path}: {e}")
    return default


def _save_json(file_path, data):
    """Безопасно сохранить JSON"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения {file_path}: {e}")
        return False


def save_osint_data():
    """Сохранить OSINT данные"""
    return _save_json(OSINT_FILE, osint_data)


def load_osint_data():
    """Загрузить OSINT данные"""
    global osint_data
    osint_data = _load_json(OSINT_FILE, osint_data)
    return True


def save_deep_osint_data():
    """Сохранить Deep OSINT данные"""
    return _save_json(DEEP_OSINT_FILE, deep_osint_data)


def load_deep_osint_data():
    """Загрузить Deep OSINT данные"""
    global deep_osint_data
    deep_osint_data = _load_json(DEEP_OSINT_FILE, deep_osint_data)
    return True


def save_accounts():
    """Сохранить аккаунты"""
    return _save_json(ACCOUNTS_FILE, accounts)


def load_accounts():
    """Загрузить аккаунты"""
    global accounts
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    accounts = loaded
    except Exception as e:
        print(f"⚠️ Ошибка загрузки аккаунтов: {e}")
        accounts = []
    return accounts

# ============================================================
# 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def _safe_get(url, headers=None, timeout=TIMEOUT_MEDIUM):
    """
    Безопасный GET-запрос.
    
    Returns:
        Response или None
    """
    try:
        h = headers if headers else DEFAULT_HEADERS
        response = requests.get(url, headers=h, timeout=timeout)
        if response.status_code == 200:
            return response
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass
    except Exception:
        pass
    return None

# ============================================================
# 8. ПОИСК ПО USERNAME (ОСНОВНЫЕ МЕТОДЫ)
# ============================================================

def search_username_real(username):
    """
    Реальный поиск по username через публичные API.
    
    Returns:
        dict
    """
    if not username:
        return {}
    
    username = username.replace("@", "").strip()
    
    results = {
        "username": username,
        "found": [],
        "social_media": {},
        "email": None,
        "phone": None,
        "name": None,
        "bio": None,
        "avatar": None,
        "location": None,
    }
    
    # === 1. GitHub API ===
    response = _safe_get(f"https://api.github.com/users/{username}")
    if response:
        try:
            data = response.json()
            results["name"] = data.get("name")
            results["bio"] = data.get("bio")
            results["location"] = data.get("location")
            results["avatar"] = data.get("avatar_url")
            results["found"].append({"platform": "GitHub", "url": data.get("html_url")})
            results["social_media"]["GitHub"] = data.get("html_url")
        except Exception:
            pass
    
    # === 2. VK (просто HEAD-запрос) ===
    response = _safe_get(f"https://vk.com/{username}", timeout=TIMEOUT_SHORT)
    if response and "vk.com" in response.text.lower():
        results["found"].append({"platform": "VK", "url": f"https://vk.com/{username}"})
        results["social_media"]["VK"] = f"https://vk.com/{username}"
    
    # === 3. Twitter/X (просто HEAD) ===
    response = _safe_get(f"https://twitter.com/{username}", timeout=TIMEOUT_SHORT)
    if response:
        results["found"].append({"platform": "Twitter", "url": f"https://twitter.com/{username}"})
        results["social_media"]["Twitter"] = f"https://twitter.com/{username}"
    
    # === 4. Telegram ===
    response = _safe_get(f"https://t.me/{username}", timeout=TIMEOUT_SHORT)
    if response and "tgme_page" in response.text:
        results["found"].append({"platform": "Telegram", "url": f"https://t.me/{username}"})
        results["social_media"]["Telegram"] = f"https://t.me/{username}"
    
    # === 5. Поиск email через Gravatar ===
    email_patterns = [
        f"{username}@gmail.com",
        f"{username}@mail.ru",
        f"{username}@yandex.ru",
        f"{username}@outlook.com",
        f"{username}@icloud.com",
    ]
    
    for email in email_patterns:
        try:
            hash_md5 = hashlib.md5(email.lower().encode()).hexdigest()
            url = f"https://www.gravatar.com/avatar/{hash_md5}?d=404"
            response = _safe_get(url, timeout=TIMEOUT_SHORT)
            if response:
                results["email"] = email
                break
        except Exception:
            pass
    
    # === 6. DuckDuckGo ===
    try:
        url = f"https://api.duckduckgo.com/?q={quote(username)}&format=json"
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        if response:
            data = response.json()
            if data.get("AbstractText"):
                results["bio"] = data.get("AbstractText")
    except Exception:
        pass
    
    return results

# ============================================================
# 9. ПОИСК ПО НОМЕРУ ТЕЛЕФОНА
# ============================================================

def search_phone_real(phone):
    """
    Реальный поиск по номеру телефона.
    
    Returns:
        dict
    """
    if not phone:
        return {}
    
    phone_clean = re.sub(r'[^0-9+]', '', phone)
    
    results = {
        "phone": phone,
        "found": [],
        "name": None,
        "location": None,
        "carrier": None,
        "timezone": None,
        "valid": False,
    }
    
    # === 1. phonenumbers ===
    if PHONENUMBERS_AVAILABLE:
        try:
            parsed = phonenumbers.parse(phone_clean, None)
            if phonenumbers.is_valid_number(parsed):
                results["valid"] = True
                results["location"] = geocoder.description_for_number(parsed, "ru")
                results["carrier"] = carrier.name_for_number(parsed, "ru")
                timezones = timezone.time_zones_for_number(parsed)
                results["timezone"] = list(timezones)[0] if timezones else None
        except Exception:
            pass
    
    # === 2. Telegram ===
    response = _safe_get(f"https://t.me/{phone_clean}", timeout=TIMEOUT_SHORT)
    if response:
        results["found"].append({
            "platform": "Telegram",
            "url": f"https://t.me/{phone_clean}",
        })
    
    return results

# ============================================================
# 10. ПОИСК ПО IP
# ============================================================

def search_ip_real(ip_address):
    """
    Реальный поиск по IP.
    
    Returns:
        dict
    """
    if not ip_address:
        return {}
    
    # Простая проверка формата
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(ip_pattern, ip_address):
        return {"ip": ip_address, "error": "Неверный формат IP"}
    
    results = {
        "ip": ip_address,
        "location": None,
        "city": None,
        "country": None,
        "isp": None,
        "org": None,
        "hostname": None,
        "coordinates": None,
        "timezone": None,
    }
    
    # === 1. ipapi.co ===
    response = _safe_get(f"https://ipapi.co/{ip_address}/json/", timeout=TIMEOUT_MEDIUM)
    if response:
        try:
            data = response.json()
            if not data.get("error"):
                results["city"] = data.get("city")
                results["country"] = data.get("country_name")
                results["isp"] = data.get("org")
                results["location"] = f"{data.get('city', '')}, {data.get('country_name', '')}"
                results["coordinates"] = f"{data.get('latitude', '')}, {data.get('longitude', '')}"
                results["timezone"] = data.get("timezone")
        except Exception:
            pass
    
    # === 2. ipinfo.io (fallback) ===
    if not results["city"]:
        response = _safe_get(f"https://ipinfo.io/{ip_address}/json", timeout=TIMEOUT_MEDIUM)
        if response:
            try:
                data = response.json()
                results["city"] = data.get("city")
                results["country"] = data.get("country")
                results["org"] = data.get("org")
                loc = data.get("loc", "")
                if loc:
                    results["coordinates"] = loc
                    results["location"] = f"{data.get('city', '')}, {data.get('country', '')}"
                results["timezone"] = data.get("timezone")
            except Exception:
                pass
    
    return results

# ============================================================
# 11. ОБОГАЩЕНИЕ ЧЕРЕЗ ИИ
# ============================================================

def enhance_with_ai(results):
    """
    Обогащение данных через ИИ.
    
    Returns:
        dict или None
    """
    key = _get_openrouter_key()
    if not key:
        return None
    
    try:
        person = results.get("person", {})
        contacts = results.get("contacts", {})
        
        context = f"ФИО: {person.get('full_name', '')}\n"
        context += f"Телефон: {contacts.get('phone', '')}\n"
        context += f"Email: {contacts.get('email', '')}\n"
        
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
                        "content": (
                            "Ты OSINT-агент. На основе имеющихся данных найди "
                            "дополнительную информацию.\n"
                            "Формат ответа — ТОЛЬКО JSON:\n"
                            "{\n"
                            '    "person": {"full_name": "", "date_of_birth": "", '
                            '"passport": "", "inn": "", "snils": ""},\n'
                            '    "family": {"father": {"name": "", "phone": ""}, '
                            '"mother": {"name": "", "phone": ""}},\n'
                            '    "address": {"home": "", "school": "", "work": ""}\n'
                            "}"
                        ),
                    },
                    {"role": "user", "content": f"Найди данные по:\n{context}"},
                ],
                "max_tokens": 500,
                "temperature": 0.3,
            },
            timeout=TIMEOUT_LONG
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0]['message']['content'].strip()
                
                # Очищаем markdown-обёртку
                content = _clean_json_response(content)
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"⚠️ Ошибка AI-обогащения: {e}")
    
    return None


def _clean_json_response(text):
    """Очистить ответ ИИ от markdown-обёртки"""
    if not text:
        return text
    
    text = text.strip()
    
    # Убираем ```json ... ```
    if text.startswith("```"):
        lines = text.split("\n")
        # Убираем первую строку (```json) и последнюю (```)
        if len(lines) >= 2:
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
    
    # Убираем возможные пояснения до/после JSON
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]
    
    return text.strip()

# ============================================================
# 12. ПОЛНЫЙ ДОКС
# ============================================================

def full_deep_dox(query, bot=None, user_id=None):
    """
    Полный сбор данных: все методы.
    
    Returns:
        dict
    """
    if not query:
        return {}
    
    results = {
        "query": query,
        "type": "unknown",
        "person": {},
        "contacts": {},
        "address": {},
        "family": {},
        "breaches": [],
        "sources": [],
        "raw_data": {},
        "timestamp": datetime.now().isoformat(),
    }
    
    # Определяем тип запроса
    is_phone = bool(re.match(r'^\+?[0-9\s\-]{10,15}$', query))
    is_email = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query))
    is_username = bool(re.match(r'^@?\w+$', query))
    is_fio = bool(re.match(r'^[А-Яа-я]+\s[А-Яа-я]+\s?[А-Яа-я]*$', query))
    
    try:
        # === ТЕЛЕФОН ===
        if is_phone:
            results["type"] = "phone"
            phone_data = search_phone_methods(query)
            results["raw_data"]["phone"] = phone_data
            results["sources"].extend(phone_data.get("sources", []))
            
            if phone_data.get("data"):
                results["person"].update(phone_data["data"])
                results["contacts"]["phone"] = query
            
            if phone_data.get("found"):
                username_results = search_username_methods(query.replace("+", ""))
                results["raw_data"]["username_from_phone"] = username_results
                results["sources"].extend(username_results.get("sources", []))
        
        # === EMAIL ===
        elif is_email:
            results["type"] = "email"
            email_data = search_email_methods(query)
            results["raw_data"]["email"] = email_data
            results["sources"].extend(email_data.get("sources", []))
            
            if email_data.get("data"):
                results["person"].update(email_data["data"])
                results["contacts"]["email"] = query
            
            breach_data = search_breach_methods(query)
            results["breaches"] = breach_data.get("data", {}).get("dehashed", [])
            results["sources"].extend(breach_data.get("sources", []))
        
        # === USERNAME ===
        elif is_username:
            results["type"] = "username"
            username_clean = query.replace("@", "")
            username_data = search_username_methods(username_clean)
            results["raw_data"]["username"] = username_data
            results["sources"].extend(username_data.get("sources", []))
            
            if username_data.get("data"):
                results["contacts"]["socials"] = username_data["data"]
            
            breach_data = search_breach_methods(username_clean)
            results["breaches"] = breach_data.get("data", {}).get("dehashed", [])
            results["sources"].extend(breach_data.get("sources", []))
        
        # === ФИО ===
        elif is_fio:
            results["type"] = "fio"
            fio_data = search_fio_methods(query)
            results["raw_data"]["fio"] = fio_data
            results["sources"].extend(fio_data.get("sources", []))
            
            if fio_data.get("data"):
                results["person"]["full_name"] = query
                if "vk" in fio_data["data"]:
                    results["contacts"]["vk"] = fio_data["data"]["vk"]
                if "inn" in fio_data["data"]:
                    results["person"]["inn"] = fio_data["data"]["inn"]
                if "snils" in fio_data["data"]:
                    results["person"]["snils"] = fio_data["data"]["snils"]
                if "2gis" in fio_data["data"]:
                    results["address"]["home"] = fio_data["data"]["2gis"]
        
        # === AI-обогащение ===
        has_data = (
            results["person"].get("full_name")
            or results["person"].get("phone")
            or results["person"].get("email")
            or results["contacts"]
        )
        
        if has_data:
            enhanced = enhance_with_ai(results)
            if enhanced and isinstance(enhanced, dict):
                if isinstance(enhanced.get("person"), dict):
                    results["person"].update(enhanced["person"])
                if isinstance(enhanced.get("family"), dict):
                    results["family"].update(enhanced["family"])
                if isinstance(enhanced.get("address"), dict):
                    results["address"].update(enhanced["address"])
                results["sources"].append("ai_enhancement")
    
    except Exception as e:
        print(f"⚠️ Ошибка сбора данных: {e}")
    
    # Сохраняем в БД
    person_id = (
        results.get("person", {}).get("full_name")
        or query
    )
    
    deep_osint_data["people"][person_id] = {
        "data": results,
        "searched_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }
    deep_osint_data["total_people"] = len(deep_osint_data["people"])
    deep_osint_data["last_update"] = datetime.now().isoformat()
    
    save_deep_osint_data()
    
    return results

# ============================================================
# 13. ФОРМАТИРОВАНИЕ
# ============================================================

def format_deep_dox_result(result):
    """Форматировать результат докса"""
    if not result:
        return "❌ Нет данных"
    
    lines = []
    lines.append("=" * 60)
    lines.append(f"🔍 ПОЛНЫЙ ДОКС: {result.get('query', '?')}")
    lines.append("=" * 60)
    
    # ЛИЧНАЯ ИНФОРМАЦИЯ
    person = result.get("person", {})
    if person:
        lines.append("\n👤 ЛИЧНАЯ ИНФОРМАЦИЯ:")
        fields = [
            ("full_name", "ФИО"),
            ("date_of_birth", "Дата рождения"),
            ("age", "Возраст"),
            ("gender", "Пол"),
            ("passport", "Паспорт"),
            ("inn", "ИНН"),
            ("snils", "СНИЛС"),
            ("carrier", "Оператор"),
            ("country", "Страна"),
        ]
        for key, label in fields:
            if person.get(key):
                lines.append(f"[+] {label}: {person[key]}")
    
    # КОНТАКТЫ
    contacts = result.get("contacts", {})
    if contacts:
        lines.append("\n📱 КОНТАКТЫ:")
        contact_fields = [
            ("phone", "Телефон"),
            ("email", "Email"),
            ("telegram", "Telegram"),
            ("whatsapp", "WhatsApp"),
            ("vk", "VK"),
        ]
        for key, label in contact_fields:
            if contacts.get(key):
                lines.append(f"[+] {label}: {contacts[key]}")
        
        socials = contacts.get("socials", {})
        if socials and isinstance(socials, dict):
            lines.append("\n🌍 СОЦСЕТИ:")
            for platform, data in socials.items():
                if isinstance(data, dict) and data.get("exists"):
                    lines.append(f"[+] {platform.capitalize()}: {data.get('url', '')}")
    
    # АДРЕС
    address = result.get("address", {})
    if address:
        lines.append("\n📍 АДРЕС:")
        for key, label in [("home", "Адрес"), ("school", "Школа"), ("work", "Работа")]:
            if address.get(key):
                lines.append(f"[+] {label}: {address[key]}")
    
    # СЕМЬЯ
    family = result.get("family", {})
    if family:
        lines.append("\n👨‍👩‍👧‍👦 СЕМЬЯ:")
        for member_key, label in [("father", "Отец"), ("mother", "Мать")]:
            member = family.get(member_key)
            if isinstance(member, dict):
                lines.append(f"[+] {label}: {member.get('name', '?')}")
                if member.get("phone"):
                    lines.append(f"    📱 Телефон: {member['phone']}")
    
    # УТЕЧКИ
    breaches = result.get("breaches", [])
    if breaches:
        lines.append("\n💀 УТЕЧКИ ДАННЫХ:")
        for breach in breaches[:5]:
            if isinstance(breach, dict):
                lines.append(f"[+] {breach.get('source', 'Unknown')}")
                if breach.get("email"):
                    lines.append(f"    Email: {breach['email']}")
                if breach.get("password"):
                    lines.append(f"    Пароль: {breach['password']}")
    
    # ИСТОЧНИКИ
    sources = result.get("sources", [])
    if sources:
        lines.append(f"\n📊 ИСТОЧНИКОВ: {len(set(sources))}")
        for source in sorted(set(sources))[:15]:
            lines.append(f"  • {source}")
    
    lines.append("\n" + "=" * 60)
    lines.append(f"🕐 Собрано: {result.get('timestamp', '?')[:16]}")
    lines.append("=" * 60)
    
    return "\n".join(lines)

# ============================================================
# 14. СОВМЕСТИМОСТЬ
# ============================================================

def full_dox_real(query, bot=None, user_id=None):
    """Совместимость со старым API"""
    return full_deep_dox(query, bot, user_id)


def format_dox_result_real(result):
    """Совместимость со старым API"""
    return format_deep_dox_result(result)

# ============================================================
# 15. УРОН (СОВМЕСТИМОСТЬ С handlers_rp_osint)
# ============================================================

def execute_damage(target, platforms=None, count=10, cycles=3, leak_info=True):
    """Нанести урон цели — делегирует в osint_operations"""
    try:
        from osint_operations import execute_damage as _execute_damage
        return _execute_damage(target, platforms, count, cycles, leak_info)
    except ImportError:
        return {
            "dox": {"query": target},
            "reports": {"total_reports": 0, "successful": 0, "platforms": {}},
            "leak": {"status": "failed"},
            "timestamp": datetime.now().isoformat(),
        }


def format_damage_result(result):
    """Форматировать результат урона — делегирует в osint_operations"""
    try:
        from osint_operations import format_damage_result as _format
        return _format(result)
    except ImportError:
        lines = [
            "💥 РЕЗУЛЬТАТ УРОНА:",
            f"🎯 Цель: {result.get('dox', {}).get('query', '?')}",
            f"📊 Отправлено жалоб: {result.get('reports', {}).get('total_reports', 0)}",
            f"✅ Успешных: {result.get('reports', {}).get('successful', 0)}",
        ]
        return "\n".join(lines)

# ============================================================
# 16. ЗАГРУЗКА
# ============================================================

load_osint_data()
load_deep_osint_data()
load_accounts()

print("🔍 OSINT Engine загружен (PC)")
print(f"📦 phonenumbers: {'✅' if PHONENUMBERS_AVAILABLE else '❌'}")
print(f"📊 Собрано профилей: {deep_osint_data.get('total_people', 0)}")
print(f"📁 Аккаунтов: {len(accounts)}")