"""OSINT — поиск по username (20 методов), ФИО, утечки"""

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime
from urllib.parse import quote

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

TIMEOUT_SHORT = 5
TIMEOUT_MEDIUM = 10

# ============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _safe_get(url, headers=None, timeout=TIMEOUT_MEDIUM):
    """Безопасный GET-запрос"""
    try:
        h = headers if headers else DEFAULT_HEADERS
        response = requests.get(url, headers=h, timeout=timeout)
        return response
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def _check_platform(username, url, headers=None, check_text=None):
    """
    Проверить наличие username на платформе.
    
    Args:
        username: ник
        url: URL профиля
        headers: заголовки
        check_text: если указан, проверяем наличие этой строки в ответе
    
    Returns:
        dict: {url, exists, status}
    """
    response = _safe_get(url, headers=headers, timeout=TIMEOUT_SHORT)
    
    if not response:
        return {
            "url": url,
            "exists": False,
            "status": "timeout",
        }
    
    exists = response.status_code == 200
    
    # Дополнительная проверка (если указан check_text)
    if exists and check_text:
        if check_text.lower() not in response.text.lower():
            exists = False
    
    # Проверка на "not found" страницы
    if exists:
        text_lower = response.text.lower()
        not_found_markers = [
            "page not found", "user not found",
            "not found", "не найден", "profile not found",
            "sorry, this page isn't available",
            "doesn't exist", "не существует",
        ]
        for marker in not_found_markers:
            if marker in text_lower:
                exists = False
                break
    
    return {
        "url": url,
        "exists": exists,
        "status": f"HTTP {response.status_code}",
    }

# ============================================================
# 3. ПОИСК ПО USERNAME (20+ ПЛАТФОРМ)
# ============================================================

def search_username_methods(username):
    """
    20+ методов поиска по username.
    
    Returns:
        dict: {found, data, sources}
    """
    if not username:
        return {"found": False, "data": {}, "sources": []}
    
    username_clean = username.replace("@", "").strip()
    
    results = {
        "found": False,
        "data": {},
        "sources": [],
    }
    
    # === Список платформ ===
    platforms = {
        "VK": {
            "url": f"https://vk.com/{username_clean}",
            "check_text": "vk.com",
        },
        "Instagram": {
            "url": f"https://instagram.com/{username_clean}",
        },
        "Twitter": {
            "url": f"https://twitter.com/{username_clean}",
        },
        "GitHub": {
            "url": f"https://github.com/{username_clean}",
        },
        "YouTube": {
            "url": f"https://youtube.com/@{username_clean}",
        },
        "Twitch": {
            "url": f"https://twitch.tv/{username_clean}",
        },
        "TikTok": {
            "url": f"https://tiktok.com/@{username_clean}",
        },
        "Reddit": {
            "url": f"https://reddit.com/user/{username_clean}",
        },
        "Pinterest": {
            "url": f"https://pinterest.com/{username_clean}",
        },
        "Spotify": {
            "url": f"https://open.spotify.com/user/{username_clean}",
        },
        "SoundCloud": {
            "url": f"https://soundcloud.com/{username_clean}",
        },
        "Steam": {
            "url": f"https://steamcommunity.com/id/{username_clean}",
        },
        "Telegram": {
            "url": f"https://t.me/{username_clean}",
            "check_text": "tgme_page",
        },
        "Discord": {
            "url": f"https://discord.com/users/{username_clean}",
        },
        "Tumblr": {
            "url": f"https://{username_clean}.tumblr.com",
        },
        "GitLab": {
            "url": f"https://gitlab.com/{username_clean}",
        },
        "Bitbucket": {
            "url": f"https://bitbucket.org/{username_clean}",
        },
        "HackerNews": {
            "url": f"https://news.ycombinator.com/user?id={username_clean}",
        },
        "ProductHunt": {
            "url": f"https://www.producthunt.com/@{username_clean}",
        },
        "Medium": {
            "url": f"https://medium.com/@{username_clean}",
        },
    }
    
    for platform, config in platforms.items():
        try:
            check_result = _check_platform(
                username_clean,
                config["url"],
                check_text=config.get("check_text"),
            )
            
            results["data"][platform.lower()] = check_result
            
            if check_result["exists"]:
                results["sources"].append(platform.lower())
                results["found"] = True
        except Exception as e:
            print(f"⚠️ Ошибка проверки {platform}: {e}")
        
        time.sleep(0.2)
    
    return results

# ============================================================
# 4. ПОИСК ПО ФИО
# ============================================================

def search_fio_methods(fio):
    """
    Поиск по ФИО.
    
    Рабочие методы:
    1. VK API — открытый поиск пользователей
    2. DuckDuckGo — Google-доркинг через API
    3. 2GIS — публичный поиск организаций
    
    Returns:
        dict: {found, data, sources}
    """
    if not fio:
        return {"found": False, "data": {}, "sources": []}
    
    results = {
        "found": False,
        "data": {},
        "sources": [],
    }
    
    fio_encoded = quote(fio)
    
    # === 1. VK API (публичный поиск) ===
    try:
        url = (
            f"https://api.vk.com/method/users.search"
            f"?q={fio_encoded}&count=3&v=5.131"
        )
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        
        if response:
            try:
                data = response.json()
                items = data.get("response", {}).get("items", [])
                if items:
                    results["data"]["vk"] = [
                        {
                            "id": item.get("id"),
                            "first_name": item.get("first_name"),
                            "last_name": item.get("last_name"),
                            "screen_name": item.get("screen_name"),
                            "url": f"https://vk.com/id{item.get('id')}",
                        }
                        for item in items[:3]
                    ]
                    results["sources"].append("vk")
                    results["found"] = True
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ VK FIO: {e}")
    
    # === 2. DuckDuckGo (Google-доркинг) ===
    try:
        query = quote(f'"{fio}"')
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        
        if response:
            try:
                data = response.json()
                abstract = data.get("AbstractText")
                if abstract:
                    results["data"]["google_result"] = abstract
                    results["sources"].append("duckduckgo")
                    results["found"] = True
                
                related = data.get("RelatedTopics", [])
                if related:
                    results["data"]["related"] = [
                        r.get("Text", "")[:150]
                        for r in related[:5]
                        if isinstance(r, dict) and r.get("Text")
                    ]
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ DuckDuckGo FIO: {e}")
    
    # === 3. 2GIS (публичный поиск) ===
    try:
        url = f"https://catalog.api.2gis.com/3.0/items?q={fio_encoded}&key=ruxlih4896"
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        
        if response:
            try:
                data = response.json()
                items = data.get("result", {}).get("items", [])
                if items:
                    results["data"]["2gis"] = [
                        {
                            "name": item.get("name"),
                            "address": item.get("address_name"),
                        }
                        for item in items[:3]
                    ]
                    results["sources"].append("2gis")
                    results["found"] = True
            except Exception:
                pass
    except Exception:
        pass
    
    return results

# ============================================================
# 5. ПОИСК УТЕЧЕК
# ============================================================

def search_breach_methods(query):
    """
    Поиск утечек — только рабочие методы.
    
    Рабочие методы:
    1. Have I Been Pwned — публичный (для email)
    2. Dehashed (публичный endpoint) — иногда работает без ключа
    
    Returns:
        dict: {found, data, sources}
    """
    if not query:
        return {"found": False, "data": {}, "sources": []}
    
    results = {
        "found": False,
        "data": {},
        "sources": [],
    }
    
    # === 1. Have I Been Pwned (для email) ===
    if "@" in query:
        try:
            response = _safe_get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{query}",
                headers={"User-Agent": "Systmka-OSINT"},
                timeout=TIMEOUT_MEDIUM,
            )
            
            if response:
                try:
                    breaches = response.json()
                    if isinstance(breaches, list) and breaches:
                        results["data"]["hibp"] = [
                            {
                                "name": b.get("Name", "Unknown"),
                                "date": b.get("BreachDate", "?"),
                                "data_classes": b.get("DataClasses", []),
                            }
                            for b in breaches[:10]
                        ]
                        results["sources"].append("hibp")
                        results["found"] = True
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ HIBP: {e}")
    
    # === 2. Dehashed (публичный endpoint) ===
    try:
        url = f"https://api.dehashed.com/search?query={quote(query)}"
        response = _safe_get(url, timeout=TIMEOUT_MEDIUM)
        
        if response:
            try:
                data = response.json()
                entries = data.get("entries", [])
                if entries:
                    results["data"]["dehashed"] = entries[:10]
                    results["sources"].append("dehashed")
                    results["found"] = True
            except Exception:
                pass
    except Exception:
        pass
    
    return results

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_username_result(result):
    """Форматировать результат поиска по username"""
    if not result:
        return "❌ Нет данных"
    
    lines = []
    found = result.get("found", [])
    
    if found:
        lines.append(f"🔍 Найдено на {len(found)} платформах:")
        for platform in found[:15]:
            url = result.get("data", {}).get(platform.lower(), {}).get("url", "")
            lines.append(f"  • {platform}: {url}")
    else:
        lines.append("❌ Ничего не найдено")
    
    return "\n".join(lines)


def format_fio_result(result):
    """Форматировать результат поиска по ФИО"""
    if not result:
        return "❌ Нет данных"
    
    lines = []
    data = result.get("data", {})
    
    if data.get("vk"):
        lines.append("🌐 VK:")
        for item in data["vk"]:
            lines.append(f"  • {item.get('first_name')} {item.get('last_name')}")
            lines.append(f"    {item.get('url')}")
    
    if data.get("google_result"):
        lines.append(f"\n🔍 Google: {data['google_result'][:200]}")
    
    if data.get("related"):
        lines.append("\n📎 Связанные:")
        for item in data["related"][:3]:
            lines.append(f"  • {item}")
    
    if data.get("2gis"):
        lines.append("\n📍 2GIS:")
        for item in data["2gis"]:
            lines.append(f"  • {item.get('name')} — {item.get('address')}")
    
    if not lines:
        lines.append("❌ Ничего не найдено")
    
    return "\n".join(lines)


def format_breach_result(result):
    """Форматировать результат поиска утечек"""
    if not result:
        return "❌ Нет данных"
    
    lines = []
    data = result.get("data", {})
    
    if data.get("hibp"):
        lines.append(f"💀 HIBP утечек: {len(data['hibp'])}")
        for b in data["hibp"][:5]:
            lines.append(f"  • {b.get('name', '?')} ({b.get('date', '?')})")
            if b.get("data_classes"):
                lines.append(f"    Данные: {', '.join(b['data_classes'][:3])}")
    
    if data.get("dehashed"):
        lines.append(f"\n💀 Dehashed записей: {len(data['dehashed'])}")
        for entry in data["dehashed"][:3]:
            if isinstance(entry, dict):
                lines.append(f"  • {entry.get('email', '?')}")
    
    if not lines:
        lines.append("✅ Утечек не найдено")
    
    return "\n".join(lines)

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("👤 OSINT Username & FIO загружен (PC)")
print(f"🔧 Платформ для username: 20")
print(f"🔧 Методов ФИО: 3")
print(f"🔧 Методов утечек: 2")