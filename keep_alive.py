"""
keep_alive.py — Внутренний пингер для Render.

Стучит на /health каждые N секунд, чтобы Render не усыплял сервис.
Работает без cron-job.org.
"""

import os
import time
import threading
import requests


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

PING_INTERVAL = 240  # 4 минуты (Render усыпляет через 15 минут)
PING_TIMEOUT = 10


# ============================================================
# 2. ПИНГЕР
# ============================================================

_pinger_running = False
_pinger_thread = None


def get_health_url() -> str:
    """Получить URL для пинга."""
    # На Render переменная RENDER_EXTERNAL_URL содержит URL сервиса
    base_url = os.environ.get("RENDER_EXTERNAL_URL")
    
    if base_url:
        return f"{base_url}/health"
    
    # Fallback — локальный
    port = os.environ.get("PORT", "8080")
    return f"http://localhost:{port}/health"


def ping_once() -> bool:
    """Один пинг."""
    url = get_health_url()
    
    try:
        response = requests.get(url, timeout=PING_TIMEOUT)
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"⚠️ Пинг не удался: {e}")
    
    return False


def _pinger_loop():
    """Фоновый цикл пинга."""
    global _pinger_running
    
    url = get_health_url()
    print(f"🏓 Пингер запущен: {url} (каждые {PING_INTERVAL}с)")
    
    # Первый пинг через 30 секунд после старта
    time.sleep(30)
    
    success_count = 0
    fail_count = 0
    
    while _pinger_running:
        if ping_once():
            success_count += 1
        else:
            fail_count += 1
        
        if (success_count + fail_count) % 10 == 0:
            print(f"🏓 Пингер: ✅ {success_count} | ❌ {fail_count}")
        
        time.sleep(PING_INTERVAL)
    
    print("🏓 Пингер остановлен")


def start_pinger():
    """Запустить пингер."""
    global _pinger_running, _pinger_thread
    
    if _pinger_running:
        return
    
    _pinger_running = True
    _pinger_thread = threading.Thread(
        target=_pinger_loop,
        daemon=True,
        name="keep_alive"
    )
    _pinger_thread.start()


def stop_pinger():
    """Остановить пингер."""
    global _pinger_running
    _pinger_running = False


def get_pinger_stats() -> dict:
    """Статистика пингера."""
    return {
        "running": _pinger_running,
        "url": get_health_url(),
        "interval": PING_INTERVAL,
    }


# ============================================================
# 3. ЗАГРУЗКА
# ============================================================

print("🏓 keep_alive загружен")
print(f"📡 URL: {get_health_url()}")
print(f"⏱ Интервал: {PING_INTERVAL}с")