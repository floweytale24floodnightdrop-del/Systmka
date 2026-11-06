"""Настройка сети — прокси, retry, timeout, headers для всех requests"""

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

# Прокси (если VPN работает как прокси)
# Пример: "socks5://127.0.0.1:1080" или "http://127.0.0.1:8080"
PROXY_URL = os.environ.get("SYSTMKA_PROXY", None)

# Таймауты
DEFAULT_TIMEOUT = 30
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30

# Retry
MAX_RETRIES = 3
BACKOFF_FACTOR = 1

# ============================================================
# 2. ПРОВЕРКА ПРОКСИ
# ============================================================

def get_proxies():
    """Получить словарь прокси для requests"""
    if not PROXY_URL:
        return None
    
    return {
        "http": PROXY_URL,
        "https": PROXY_URL,
    }

# ============================================================
# 3. СОЗДАНИЕ SESSION С RETRY
# ============================================================

def create_session(
    retries=MAX_RETRIES,
    backoff=BACKOFF_FACTOR,
    timeout=DEFAULT_TIMEOUT,
    use_proxy=True,
):
    """
    Создать requests.Session с retry и прокси.
    
    Returns:
        requests.Session
    """
    session = requests.Session()
    
    # Retry
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20,
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Прокси
    if use_proxy:
        proxies = get_proxies()
        if proxies:
            session.proxies.update(proxies)
            print(f"🌐 Прокси: {PROXY_URL}")
    
    # Headers
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    })
    
    # Таймаут (по умолчанию)
    session.timeout = timeout
    
    return session

# ============================================================
# 4. ГЛОБАЛЬНАЯ SESSION
# ============================================================

_default_session = None


def get_session():
    """Получить глобальную session"""
    global _default_session
    if _default_session is None:
        _default_session = create_session()
    return _default_session

# ============================================================
# 5. БЕЗОПАСНЫЕ ЗАПРОСЫ
# ============================================================

def safe_get(url, timeout=DEFAULT_TIMEOUT, **kwargs):
    """
    Безопасный GET с retry и прокси.
    
    Returns:
        requests.Response или None
    """
    session = get_session()
    
    if "timeout" not in kwargs:
        kwargs["timeout"] = (CONNECT_TIMEOUT, READ_TIMEOUT)
    
    try:
        return session.get(url, **kwargs)
    except Exception as e:
        print(f"⚠️ safe_get {url}: {e}")
        return None


def safe_post(url, timeout=DEFAULT_TIMEOUT, **kwargs):
    """Безопасный POST с retry и прокси"""
    session = get_session()
    
    if "timeout" not in kwargs:
        kwargs["timeout"] = (CONNECT_TIMEOUT, READ_TIMEOUT)
    
    try:
        return session.post(url, **kwargs)
    except Exception as e:
        print(f"⚠️ safe_post {url}: {e}")
        return None

# ============================================================
# 6. ПРОВЕРКА
# ============================================================

def check_telegram():
    """Проверить Telegram API"""
    response = safe_get("https://api.telegram.org", timeout=10)
    if response and response.status_code == 200:
        return True
    return False


def check_youtube():
    """Проверить YouTube"""
    response = safe_get("https://www.youtube.com", timeout=10)
    if response and response.status_code == 200:
        return True
    return False


def check_my_ip():
    """Получить текущий IP (для проверки VPN)"""
    response = safe_get("https://api.ipify.org?format=json", timeout=10)
    if response and response.status_code == 200:
        try:
            return response.json().get("ip")
        except Exception:
            pass
    return None

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🌐 network_config загружен")
print(f"🔌 Прокси: {PROXY_URL or 'не указан'}")
print(f"⏱ Таймаут: {DEFAULT_TIMEOUT}с")
print(f"🔄 Retry: {MAX_RETRIES}")

# Проверка
_tg = check_telegram()
_yt = check_youtube()
_ip = check_my_ip()

print(f"📱 Telegram: {'✅' if _tg else '❌'}")
print(f"📺 YouTube: {'✅' if _yt else '❌'}")
print(f"🌍 IP: {_ip or '?'}")