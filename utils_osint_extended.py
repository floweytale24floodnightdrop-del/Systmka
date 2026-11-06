"""Расширенный OSINT — анализ телефонов, email, username, IP"""

import os
import re
import json
import urllib.parse
import requests
from datetime import datetime

# ============================================================
# 1. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ (С ЗАЩИТОЙ)
# ============================================================

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    print("⚠️ phonenumbers не установлен — анализ телефонов недоступен")

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("⚠️ dnspython не установлен — DNS-запросы недоступны")

# ============================================================
# 2. АНАЛИЗ ТЕЛЕФОНА
# ============================================================

def analyze_phone_number(phone):
    """
    Анализ номера телефона через phonenumbers.
    
    Args:
        phone: номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX
    
    Returns:
        dict или None
    """
    if not PHONENUMBERS_AVAILABLE:
        return {
            "error": "phonenumbers не установлен",
            "phone": phone,
        }
    
    try:
        # Определяем регион по номеру (по умолчанию RU)
        parsed = phonenumbers.parse(phone, "RU")
        
        if not phonenumbers.is_valid_number(parsed):
            return {
                "valid": False,
                "phone": phone,
                "error": "Неверный номер",
            }
        
        return {
            "valid": True,
            "phone": phone,
            "formatted": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
            "country": geocoder.description_for_number(parsed, "ru"),
            "carrier": carrier.name_for_number(parsed, "ru"),
            "timezone": list(timezone.time_zones_for_number(parsed)),
            "is_possible": phonenumbers.is_possible_number(parsed),
        }
    except phonenumbers.NumberParseException as e:
        return {
            "valid": False,
            "phone": phone,
            "error": f"Ошибка парсинга: {e}",
        }
    except Exception as e:
        return {
            "valid": False,
            "phone": phone,
            "error": str(e),
        }

def format_phone_info(result):
    """Форматировать информацию о телефоне"""
    if not result:
        return "❌ Нет данных"
    
    lines = [f"📞 {result.get('phone', '?')}"]
    
    if not result.get("valid"):
        lines.append(f"❌ {result.get('error', 'Неверный номер')}")
        return "\n".join(lines)
    
    if result.get("formatted"):
        lines.append(f"  Формат: {result['formatted']}")
    if result.get("country"):
        lines.append(f"  Страна: {result['country']}")
    if result.get("carrier"):
        lines.append(f"  Оператор: {result['carrier']}")
    if result.get("timezone"):
        lines.append(f"  Часовой пояс: {', '.join(result['timezone'])}")
    
    return "\n".join(lines)

# ============================================================
# 3. ПРОВЕРКА EMAIL ДОМЕНА
# ============================================================

def check_email_domain(email):
    """
    Проверка домена email через MX-записи.
    
    Returns:
        dict: {domain, mx_records, has_mx}
    """
    if not email or "@" not in email:
        return {"email": email, "valid": False, "error": "Неверный email"}
    
    domain = email.split("@")[1].strip()
    
    result = {
        "email": email,
        "domain": domain,
        "mx_records": [],
        "has_mx": False,
        "valid": False,
    }
    
    if not DNS_AVAILABLE:
        result["error"] = "dnspython не установлен"
        return result
    
    try:
        answers = dns.resolver.resolve(domain, "MX")
        result["mx_records"] = [str(r.exchange).rstrip(".") for r in answers]
        result["has_mx"] = len(result["mx_records"]) > 0
        result["valid"] = result["has_mx"]
    except dns.resolver.NXDOMAIN:
        result["error"] = "Домен не существует"
    except dns.resolver.NoAnswer:
        result["error"] = "Нет MX-записей"
    except dns.resolver.Timeout:
        result["error"] = "Таймаут DNS"
    except Exception as e:
        result["error"] = str(e)[:80]
    
    return result

def check_email_smtp(email):
    """
    Проверка SMTP-сервера через DNS.
    
    Returns:
        dict: {smtp_server, port}
    """
    domain = email.split("@")[1].strip() if "@" in email else None
    if not domain:
        return {"error": "Неверный email"}
    
    if not DNS_AVAILABLE:
        return {"error": "dnspython не установлен"}
    
    smtp_servers = [
        f"smtp.{domain}",
        f"mail.{domain}",
        domain,
    ]
    
    for server in smtp_servers:
        try:
            dns.resolver.resolve(server, "A")
            return {
                "smtp_server": server,
                "domain": domain,
            }
        except Exception:
            continue
    
    return {"error": "SMTP-сервер не найден", "domain": domain}

# ============================================================
# 4. ВАРИАНТЫ USERNAME
# ============================================================

def search_username_variants(username):
    """
    Сгенерировать варианты ника.
    
    Returns:
        list: список вариантов
    """
    if not username:
        return []
    
    variants = [
        username,
        username.lower(),
        username.upper(),
        username.capitalize(),
        f"_{username}_",
        f"{username}_official",
        f"real_{username}",
        f"{username}1",
        f"{username}2",
        f"{username}228",
        f"{username}777",
        f"the_{username}",
        f"xX_{username}_Xx",
        f"{username}_bot",
        f"{username}_ai",
    ]
    
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    result = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            result.append(v)
    
    return result

# ============================================================
# 5. ПОИСК ПО СОЦСЕТЯМ
# ============================================================

def search_social_media_deep(username):
    """
    Глубокий поиск по соцсетям.
    
    Returns:
        list: [{platform, url, found}, ...]
    """
    if not username:
        return []
    
    results = []
    
    platforms = {
        "GitHub": f"https://api.github.com/users/{username}",
        "GitLab": f"https://gitlab.com/api/v4/users?username={username}",
        "Reddit": f"https://www.reddit.com/user/{username}/about.json",
        "VK": f"https://vk.com/{username}",
        "Instagram": f"https://www.instagram.com/{username}/",
        "Twitter": f"https://twitter.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Telegram": f"https://t.me/{username}",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for platform, url in platforms.items():
        try:
            response = requests.get(url, headers=headers, timeout=8)
            found = response.status_code == 200
            
            # Для Instagram/TikTok 200 может быть даже если юзера нет
            if platform in ["Instagram", "TikTok"] and response.status_code == 200:
                # Проверяем наличие признаков "не найдено"
                text_lower = response.text.lower()
                if "not found" in text_lower or "page not found" in text_lower:
                    found = False
            
            results.append({
                "platform": platform,
                "url": url,
                "found": found,
                "status_code": response.status_code,
            })
        except requests.exceptions.Timeout:
            results.append({
                "platform": platform,
                "url": url,
                "found": False,
                "error": "timeout",
            })
        except Exception as e:
            results.append({
                "platform": platform,
                "url": url,
                "found": False,
                "error": str(e)[:50],
            })
    
    return results

def format_social_results(results):
    """Форматировать результаты поиска по соцсетям"""
    if not results:
        return "❌ Ничего не найдено"
    
    found = [r for r in results if r.get("found")]
    not_found = [r for r in results if not r.get("found")]
    
    lines = [f"🔍 Найдено: {len(found)} из {len(results)}", ""]
    
    if found:
        lines.append("✅ Найдено:")
        for r in found:
            lines.append(f"  • {r['platform']}: {r['url']}")
    
    if not_found:
        lines.append("")
        lines.append("❌ Не найдено:")
        for r in not_found[:10]:
            lines.append(f"  • {r['platform']}")
    
    return "\n".join(lines)

# ============================================================
# 6. ИНФОРМАЦИЯ ПО IP
# ============================================================

def get_ip_info(ip_address):
    """
    Информация по IP-адресу.
    
    Returns:
        dict или None
    """
    if not ip_address:
        return None
    
    # Проверяем формат IP
    ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    if not re.match(ip_pattern, ip_address):
        return {"error": "Неверный формат IP", "ip": ip_address}
    
    try:
        # ipapi.co
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                return {
                    "ip": ip_address,
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "postal": data.get("postal"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("org"),
                    "asn": data.get("asn"),
                }
    except Exception as e:
        print(f"⚠️ ipapi.co ошибка: {e}")
    
    # Fallback — ipinfo.io
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            loc = data.get("loc", "").split(",")
            return {
                "ip": ip_address,
                "country": data.get("country"),
                "region": data.get("region"),
                "city": data.get("city"),
                "latitude": loc[0] if len(loc) > 0 else None,
                "longitude": loc[1] if len(loc) > 1 else None,
                "timezone": data.get("timezone"),
                "isp": data.get("org"),
            }
    except Exception as e:
        print(f"⚠️ ipinfo.io ошибка: {e}")
    
    return {"ip": ip_address, "error": "Не удалось получить данные"}

def format_ip_info(result):
    """Форматировать информацию об IP"""
    if not result:
        return "❌ Нет данных"
    
    if result.get("error"):
        return f"❌ {result['error']}"
    
    lines = [f"🌐 IP: {result.get('ip', '?')}"]
    
    if result.get("country"):
        lines.append(f"  Страна: {result['country']}")
    if result.get("region"):
        lines.append(f"  Регион: {result['region']}")
    if result.get("city"):
        lines.append(f"  Город: {result['city']}")
    if result.get("isp"):
        lines.append(f"  Провайдер: {result['isp']}")
    if result.get("asn"):
        lines.append(f"  ASN: {result['asn']}")
    if result.get("latitude") and result.get("longitude"):
        lines.append(f"  Координаты: {result['latitude']}, {result['longitude']}")
    
    return "\n".join(lines)

# ============================================================
# 7. ОБРАТНЫЙ ПОИСК ПО КАРТИНКЕ
# ============================================================

def reverse_image_search(image_url):
    """
    Обратный поиск по картинке.
    
    Returns:
        dict: ссылки на поисковики
    """
    if not image_url:
        return {"error": "Нет URL картинки"}
    
    encoded = urllib.parse.quote(image_url, safe="")
    
    return {
        "google": f"https://lens.google.com/uploadbyurl?url={encoded}",
        "yandex": f"https://yandex.ru/images/search?rpt=imageview&url={encoded}",
        "bing": f"https://www.bing.com/images/search?q=imgurl:{encoded}&view=detailv2",
        "tineye": f"https://tineye.com/search?url={encoded}",
    }

def format_reverse_search(result):
    """Форматировать ссылки обратного поиска"""
    if not result or result.get("error"):
        return "❌ Нет данных"
    
    lines = ["🔍 ОБРАТНЫЙ ПОИСК:"]
    for name, url in result.items():
        lines.append(f"  • {name.capitalize()}: {url}")
    
    return "\n".join(lines)

# ============================================================
# 8. ПОИСК УТЕЧЕК
# ============================================================

def search_darkweb_leaks(email):
    """
    Поиск утечек через Have I Been Pwned.
    
    Returns:
        list: [{source, date, data}, ...]
    """
    if not email or "@" not in email:
        return []
    
    leaks = []
    
    try:
        # HIBP требует API-ключ для большинства запросов,
        # но базовый запрос работает без ключа
        response = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            timeout=10,
            headers={"User-Agent": "Systmka-OSINT"}
        )
        
        if response.status_code == 200:
            breaches = response.json()
            for breach in breaches:
                leaks.append({
                    "source": breach.get("Name", "Неизвестно"),
                    "date": breach.get("BreachDate", "?"),
                    "data": breach.get("DataClasses", []),
                    "description": breach.get("Description", "")[:100],
                })
        elif response.status_code == 404:
            # Нет утечек — это нормально
            pass
        elif response.status_code == 401:
            print("⚠️ HIBP: нужен API-ключ")
        elif response.status_code == 429:
            print("⚠️ HIBP: лимит запросов")
    except Exception as e:
        print(f"⚠️ HIBP ошибка: {e}")
    
    return leaks

def format_leaks(leaks):
    """Форматировать утечки"""
    if not leaks:
        return "✅ Утечек не найдено"
    
    lines = [f"💀 УТЕЧЕК: {len(leaks)}", ""]
    
    for leak in leaks[:10]:
        lines.append(f"📌 {leak['source']} ({leak['date']})")
        if leak.get("data"):
            data_str = ", ".join(leak["data"][:5])
            lines.append(f"   Данные: {data_str}")
        lines.append("")
    
    return "\n".join(lines)

# ============================================================
# 9. WHOIS ДОМЕНА
# ============================================================

def whois_domain(domain):
    """
    WHOIS-информация о домене через DNS.
    
    Returns:
        dict: {domain, a_records, ns_records, has_mx}
    """
    if not domain:
        return None
    
    # Убираем протокол
    domain = re.sub(r'^https?://', '', domain).split("/")[0].strip()
    
    result = {
        "domain": domain,
        "a_records": [],
        "ns_records": [],
        "has_mx": False,
    }
    
    if not DNS_AVAILABLE:
        result["error"] = "dnspython не установлен"
        return result
    
    try:
        # A-записи
        try:
            answers = dns.resolver.resolve(domain, "A")
            result["a_records"] = [str(r) for r in answers]
        except Exception:
            pass
        
        # NS-записи
        try:
            answers = dns.resolver.resolve(domain, "NS")
            result["ns_records"] = [str(r).rstrip(".") for r in answers]
        except Exception:
            pass
        
        # MX
        try:
            answers = dns.resolver.resolve(domain, "MX")
            result["has_mx"] = len(answers) > 0
        except Exception:
            pass
        
        result["valid"] = bool(result["a_records"] or result["ns_records"])
        
    except Exception as e:
        result["error"] = str(e)[:80]
    
    return result

def format_whois(result):
    """Форматировать WHOIS"""
    if not result:
        return "❌ Нет данных"
    
    lines = [f"🌐 Домен: {result.get('domain', '?')}"]
    
    if result.get("a_records"):
        lines.append(f"  A: {', '.join(result['a_records'][:3])}")
    if result.get("ns_records"):
        lines.append(f"  NS: {', '.join(result['ns_records'][:3])}")
    lines.append(f"  MX: {'✅' if result.get('has_mx') else '❌'}")
    
    if result.get("error"):
        lines.append(f"  ⚠️ {result['error']}")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("🔍 Модуль расширенного OSINT загружен")
print(f"📦 phonenumbers: {'✅' if PHONENUMBERS_AVAILABLE else '❌'}")
print(f"📦 dnspython: {'✅' if DNS_AVAILABLE else '❌'}")
print(f"🔧 Доступно функций: 9")