"""OSINT — поиск по телефону и email. Только рабочие методы."""

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime

# ============================================================
# 1. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ
# ============================================================

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    print("⚠️ phonenumbers не установлен")

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

TIMEOUT_SHORT = 5
TIMEOUT_MEDIUM = 10

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _safe_get(url, headers=None, timeout=TIMEOUT_MEDIUM):
    """Безопасный GET-запрос"""
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
# 4. ПОИСК ПО НОМЕРУ ТЕЛЕФОНА
# ============================================================

def search_phone_methods(phone):
    """
    Поиск по номеру телефона — только рабочие методы.
    
    Методы:
    1. phonenumbers — базовая информация (оператор, страна, регион)
    2. Telegram — проверка существования аккаунта
    3. WhatsApp — генерация ссылки
    4. Viber — генерация ссылки
    
    Returns:
        dict: {found, data, sources}
    """
    results = {
        "found": False,
        "data": {},
        "sources": [],
    }
    
    if not phone:
        return results
    
    phone_clean = re.sub(r'[^0-9+]', '', phone)
    
    # === 1. phonenumbers ===
    if PHONENUMBERS_AVAILABLE:
        try:
            parsed = phonenumbers.parse(phone_clean, None)
            
            if phonenumbers.is_valid_number(parsed):
                results["data"]["valid"] = True
                results["data"]["country"] = geocoder.description_for_number(parsed, "ru")
                results["data"]["carrier"] = carrier.name_for_number(parsed, "ru")
                
                timezones = timezone.time_zones_for_number(parsed)
                results["data"]["timezone"] = list(timezones)[0] if timezones else None
                
                results["data"]["formatted"] = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                
                results["data"]["country_code"] = parsed.country_code
                results["data"]["national_number"] = parsed.national_number
                
                results["sources"].append("phonenumbers")
                results["found"] = True
        except phonenumbers.NumberParseException:
            pass
        except Exception as e:
            print(f"⚠️ phonenumbers: {e}")
    
    # === 2. Telegram ===
    response = _safe_get(f"https://t.me/{phone_clean}", timeout=TIMEOUT_SHORT)
    if response and "tgme_page" in response.text:
        results["data"]["telegram"] = f"https://t.me/{phone_clean}"
        results["sources"].append("telegram")
        results["found"] = True
    
    # === 3. WhatsApp (генерация ссылки) ===
    results["data"]["whatsapp"] = f"https://wa.me/{phone_clean}"
    results["sources"].append("whatsapp_link")
    
    # === 4. Viber (генерация ссылки) ===
    results["data"]["viber"] = f"viber://chat?number={phone_clean}"
    results["sources"].append("viber_link")
    
    return results

# ============================================================
# 5. ПОИСК ПО EMAIL
# ============================================================

def search_email_methods(email):
    """
    Поиск по email — только рабочие методы.
    
    Методы:
    1. Gravatar — аватар и профиль (без ключа)
    2. Have I Been Pwned — утечки (без ключа, базово)
    3. Emailrep.io — репутация (без ключа)
    
    Returns:
        dict: {found, data, sources}
    """
    results = {
        "found": False,
        "data": {},
        "sources": [],
    }
    
    if not email or "@" not in email:
        return results
    
    email_lower = email.lower().strip()
    
    # === 1. Gravatar ===
    try:
        hash_md5 = hashlib.md5(email_lower.encode()).hexdigest()
        url = f"https://www.gravatar.com/{hash_md5}.json"
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        
        if response:
            try:
                data = response.json()
                entry = data.get("entry", [])
                if entry:
                    first = entry[0]
                    results["data"]["gravatar_name"] = first.get("displayName")
                    results["data"]["gravatar_avatar"] = first.get("thumbnailUrl")
                    results["data"]["gravatar_profile"] = first.get("profileUrl")
                    
                    about = first.get("aboutMe")
                    if about:
                        results["data"]["gravatar_about"] = about[:200]
                    
                    accounts = first.get("accounts", [])
                    if accounts:
                        results["data"]["gravatar_accounts"] = [
                            {"shortname": a.get("shortname"), "url": a.get("url")}
                            for a in accounts[:5]
                        ]
                    
                    results["sources"].append("gravatar")
                    results["found"] = True
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ Gravatar: {e}")
    
    # === 2. Have I Been Pwned (базовый запрос) ===
    try:
        response = _safe_get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email_lower}",
            headers={"User-Agent": "Systmka-OSINT"},
            timeout=TIMEOUT_MEDIUM,
        )
        
        if response:
            try:
                breaches = response.json()
                if isinstance(breaches, list):
                    results["data"]["hibp_breaches"] = [
                        {
                            "name": b.get("Name", "Unknown"),
                            "date": b.get("BreachDate", "?"),
                            "data_classes": b.get("DataClasses", []),
                            "description": b.get("Description", "")[:200],
                        }
                        for b in breaches[:10]
                    ]
                    results["sources"].append("hibp")
                    results["found"] = True
            except Exception:
                pass
    except Exception:
        pass
    
    # === 3. Emailrep.io ===
    try:
        response = _safe_get(
            f"https://emailrep.io/{email_lower}",
            timeout=TIMEOUT_MEDIUM,
        )
        
        if response:
            try:
                data = response.json()
                results["data"]["emailrep"] = {
                    "reputation": data.get("reputation"),
                    "suspicious": data.get("suspicious"),
                    "domain": data.get("domain"),
                    "disposable": data.get("disposable"),
                    "profiles": data.get("details", {}).get("profiles", []),
                }
                results["sources"].append("emailrep")
                results["found"] = True
            except Exception:
                pass
    except Exception:
        pass
    
    return results

# ============================================================
# 6. ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def check_phone_format(phone):
    """
    Проверить формат телефона.
    
    Returns:
        dict: {valid, formatted, error}
    """
    if not phone:
        return {"valid": False, "error": "Пустой номер"}
    
    phone_clean = re.sub(r'[^0-9+]', '', phone)
    
    if not PHONENUMBERS_AVAILABLE:
        return {
            "valid": False,
            "phone": phone_clean,
            "error": "phonenumbers не установлен",
        }
    
    try:
        parsed = phonenumbers.parse(phone_clean, None)
        
        if phonenumbers.is_valid_number(parsed):
            return {
                "valid": True,
                "phone": phone_clean,
                "formatted": phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ),
                "country_code": parsed.country_code,
            }
        else:
            return {
                "valid": False,
                "phone": phone_clean,
                "error": "Неверный номер",
            }
    except phonenumbers.NumberParseException as e:
        return {
            "valid": False,
            "phone": phone_clean,
            "error": str(e),
        }
    except Exception as e:
        return {
            "valid": False,
            "phone": phone_clean,
            "error": str(e),
        }


def get_phone_links(phone):
    """
    Получить ссылки для мессенджеров.
    
    Returns:
        dict
    """
    phone_clean = re.sub(r'[^0-9+]', '', phone)
    
    return {
        "telegram": f"https://t.me/{phone_clean}",
        "whatsapp": f"https://wa.me/{phone_clean}",
        "viber": f"viber://chat?number={phone_clean}",
        "signal": f"https://signal.me/#p/{phone_clean}",
    }


def format_phone_info(result):
    """Форматировать информацию о телефоне"""
    if not result:
        return "❌ Нет данных"
    
    data = result.get("data", {})
    lines = ["📞 " + data.get("formatted", result.get("phone", "?"))]
    
    if data.get("country"):
        lines.append(f"  🌍 Страна: {data['country']}")
    if data.get("carrier"):
        lines.append(f"  📡 Оператор: {data['carrier']}")
    if data.get("timezone"):
        lines.append(f"  🕐 Часовой пояс: {data['timezone']}")
    
    # Мессенджеры
    if data.get("telegram"):
        lines.append(f"  ✈️ Telegram: {data['telegram']}")
    if data.get("whatsapp"):
        lines.append(f"  💬 WhatsApp: {data['whatsapp']}")
    if data.get("viber"):
        lines.append(f"  📱 Viber: {data['viber']}")
    
    if result.get("sources"):
        lines.append(f"  📊 Источников: {len(result['sources'])}")
    
    return "\n".join(lines)


def format_email_info(result):
    """Форматировать информацию об email"""
    if not result:
        return "❌ Нет данных"
    
    data = result.get("data", {})
    lines = ["📧 " + data.get("email", "?")]
    
    # Gravatar
    if data.get("gravatar_name"):
        lines.append(f"  👤 Gravatar: {data['gravatar_name']}")
    if data.get("gravatar_profile"):
        lines.append(f"  🔗 Профиль: {data['gravatar_profile']}")
    
    # Emailrep
    emailrep = data.get("emailrep", {})
    if emailrep:
        lines.append(f"  ⭐ Репутация: {emailrep.get('reputation', '?')}")
        if emailrep.get("suspicious"):
            lines.append(f"  ⚠️ Подозрительный: {'✅' if emailrep['suspicious'] else '❌'}")
        if emailrep.get("disposable"):
            lines.append(f"  🗑 Одноразовый: {'✅' if emailrep['disposable'] else '❌'}")
    
    # HIBP
    breaches = data.get("hibp_breaches", [])
    if breaches:
        lines.append(f"  💀 Утечек: {len(breaches)}")
        for b in breaches[:3]:
            lines.append(f"    • {b.get('name', '?')} ({b.get('date', '?')})")
    
    if result.get("sources"):
        lines.append(f"  📊 Источников: {len(result['sources'])}")
    
    return "\n".join(lines)

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📧 OSINT Phone & Email загружен (PC)")
print(f"📦 phonenumbers: {'✅' if PHONENUMBERS_AVAILABLE else '❌'}")
print(f"🔧 Методов телефона: 4")
print(f"🔧 Методов email: 3")