"""Сетевые утилиты — проверка интернета, кэш, безопасные запросы"""

import os
import json
import requests
from datetime import datetime

# ============================================================
# 1. СОСТОЯНИЕ ИНТЕРНЕТА
# ============================================================

internet_status = {
    "is_online": False,
    "last_check": None,
    "was_offline": False,
    "offline_count": 0,
    "restore_notified": False,
}

# Кэш проверки (чтобы не долбить Telegram API)
_INTERNET_CACHE_TTL = 5  # секунд

# ============================================================
# 2. ПРОВЕРКА ИНТЕРНЕТА
# ============================================================

def check_internet():
    """
    Проверить наличие интернета.
    
    Returns:
        str: "online", "offline" или "restored"
    """
    now = datetime.now()
    
    # Проверяем кэш
    last_check = internet_status.get("last_check")
    if last_check:
        if isinstance(last_check, str):
            try:
                last_check = datetime.fromisoformat(last_check)
            except ValueError:
                last_check = None
        
        if last_check and (now - last_check).total_seconds() < _INTERNET_CACHE_TTL:
            return "online" if internet_status["is_online"] else "offline"
    
    try:
        response = requests.get("https://api.telegram.org", timeout=5)
        
        if response.status_code == 200:
            internet_status["is_online"] = True
            internet_status["last_check"] = now
            
            # Проверяем, был ли оффлайн
            if internet_status["was_offline"] and not internet_status["restore_notified"]:
                internet_status["was_offline"] = False
                internet_status["restore_notified"] = True
                internet_status["offline_count"] = 0
                return "restored"
            
            internet_status["restore_notified"] = False
            return "online"
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass
    except Exception:
        pass
    
    # Оффлайн
    internet_status["is_online"] = False
    internet_status["last_check"] = now
    internet_status["was_offline"] = True
    internet_status["offline_count"] += 1
    return "offline"

def is_online():
    """Быстрая проверка: онлайн ли сейчас"""
    return internet_status.get("is_online", False)

def get_offline_count():
    """Сколько раз подряд был оффлайн"""
    return internet_status.get("offline_count", 0)

def reset_offline_count():
    """Сбросить счётчик оффлайна"""
    internet_status["offline_count"] = 0
    internet_status["restore_notified"] = False

def format_internet_status():
    """Форматировать статус интернета"""
    online = internet_status.get("is_online", False)
    last_check = internet_status.get("last_check")
    
    if isinstance(last_check, datetime):
        last_str = last_check.strftime("%H:%M:%S")
    else:
        last_str = "никогда"
    
    return (
        f"🌐 Интернет: {'✅ онлайн' if online else '❌ оффлайн'}\n"
        f"🕐 Последняя проверка: {last_str}\n"
        f"📊 Оффлайн подряд: {internet_status.get('offline_count', 0)}"
    )

# ============================================================
# 3. КЭШ
# ============================================================

cache = {}
CACHE_TTL = 300  # 5 минут

def cache_get(key):
    """
    Получить значение из кэша.
    
    Returns:
        Значение или None
    """
    if key in cache:
        data, timestamp = cache[key]
        
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                del cache[key]
                return None
        
        if (datetime.now() - timestamp).total_seconds() < CACHE_TTL:
            return data
        
        del cache[key]
    
    return None

def cache_set(key, data):
    """Сохранить значение в кэш"""
    cache[key] = (data, datetime.now())
    
    # Чистим старые, если кэш большой
    if len(cache) > 100:
        now = datetime.now()
        expired = []
        
        for k, (_, ts) in cache.items():
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except ValueError:
                    expired.append(k)
                    continue
            
            if (now - ts).total_seconds() > CACHE_TTL:
                expired.append(k)
        
        for k in expired:
            del cache[k]

def cache_clear():
    """Очистить весь кэш"""
    global cache
    cache = {}

def cache_size():
    """Размер кэша"""
    return len(cache)

# ============================================================
# 4. БЕЗОПАСНЫЕ ЗАПРОСЫ
# ============================================================

def safe_request(url, method="GET", headers=None, timeout=15, retries=2, **kwargs):
    """
    Безопасный HTTP-запрос с retry.
    
    Args:
        url: URL
        method: "GET" или "POST"
        headers: заголовки
        timeout: таймаут
        retries: количество повторных попыток
        **kwargs: дополнительные параметры (json, data и т.д.)
    
    Returns:
        Response или None
    """
    if not url:
        return None
    
    method = method.upper()
    
    for attempt in range(retries + 1):
        try:
            if method == "GET":
                response = requests.get(
                    url, headers=headers, timeout=timeout, **kwargs
                )
            elif method == "POST":
                response = requests.post(
                    url, headers=headers, timeout=timeout, **kwargs
                )
            else:
                return None
            
            # Успех
            if response.status_code == 200:
                return response
            
            # Лимит запросов — ждём и пробуем снова
            if response.status_code == 429:
                import time
                wait_time = 2 ** attempt  # 1, 2, 4 секунды
                time.sleep(wait_time)
                continue
            
            # Другие ошибки — возвращаем как есть
            return response
        
        except requests.exceptions.Timeout:
            if attempt < retries:
                import time
                time.sleep(1)
                continue
            return None
        
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                import time
                time.sleep(2)
                continue
            return None
        
        except Exception:
            return None
    
    return None

def safe_get(url, headers=None, timeout=15, **kwargs):
    """Безопасный GET"""
    return safe_request(url, "GET", headers, timeout, **kwargs)

def safe_post(url, headers=None, timeout=15, **kwargs):
    """Безопасный POST"""
    return safe_request(url, "POST", headers, timeout, **kwargs)

# ============================================================
# 5. HEADERS
# ============================================================

def get_headers(mobile=False):
    """
    Получить стандартные заголовки.
    
    Args:
        mobile: использовать мобильный User-Agent
    
    Returns:
        dict
    """
    if mobile:
        ua = (
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36"
        )
    else:
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

def get_json_headers():
    """Заголовки для JSON-запросов"""
    return {
        "User-Agent": get_headers()["User-Agent"],
        "Content-Type": "application/json",
    }

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("🌐 Модуль сетевых утилит загружен")
print(f"💾 Кэш: {len(cache)} записей")
print(f"🌐 Интернет: {'✅' if internet_status.get('is_online') else '❌'}")