"""Мониторинг сети, запросов и лимитов"""

import time
import requests
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

network_stats = {
    "requests_last_minute": 0,
    "requests_last_hour": 0,
    "total_requests_today": 0,
    "total_tokens_today": 0,
    "last_request_time": None,
    "request_history": [],
    "rate_limit_remaining": 100,
    "rate_limit_reset": None,
}

# ============================================================
# 2. ПРОВЕРКА СКОРОСТИ
# ============================================================

def check_internet_speed():
    """Проверить скорость интернета"""
    try:
        start = time.time()
        response = requests.get("https://api.telegram.org", timeout=10)
        ping = int((time.time() - start) * 1000)
        
        start = time.time()
        response = requests.get("https://httpbin.org/bytes/1024", timeout=10)
        download_time = time.time() - start
        download_speed = 1024 / download_time if download_time > 0 else 0
        
        return {
            "ping_ms": ping,
            "download_speed_kbps": int(download_speed / 1024),
            "online": response.status_code == 200,
        }
    except Exception:
        return {"ping_ms": 0, "download_speed_kbps": 0, "online": False}

# ============================================================
# 3. УЧЁТ ЗАПРОСОВ
# ============================================================

def track_request(tokens_used=0):
    """Отследить запрос"""
    now = datetime.now()
    network_stats["last_request_time"] = now
    network_stats["request_history"].append(now)
    
    minute_ago = now - timedelta(minutes=1)
    network_stats["request_history"] = [
        t for t in network_stats["request_history"] if t > minute_ago
    ]
    
    network_stats["requests_last_minute"] = len(network_stats["request_history"])
    network_stats["requests_last_hour"] += 1
    network_stats["total_requests_today"] += 1
    network_stats["total_tokens_today"] += tokens_used

# ============================================================
# 4. ПОЛУЧЕНИЕ СТАТИСТИКИ
# ============================================================

def get_requests_per_minute():
    return network_stats["requests_last_minute"]


def get_requests_per_hour():
    return network_stats["requests_last_hour"]


def get_total_requests():
    return network_stats["total_requests_today"]


def get_rate_limit_info():
    """Информация о лимитах"""
    return {
        "telegram_limit": "30 msg/sec",
        "openrouter_limit": "1000 req/day (free)",
        "remaining": network_stats["rate_limit_remaining"],
        "reset_at": network_stats["rate_limit_reset"],
    }

# ============================================================
# 5. ФОРМАТИРОВАНИЕ
# ============================================================

def format_network_status():
    """Форматировать статус сети"""
    speed = check_internet_speed()
    
    lines = []
    lines.append("=" * 40)
    lines.append("📡 СЕТЬ:")
    lines.append(f"Интернет: {'✅' if speed['online'] else '❌'}")
    lines.append(f"Пинг: {speed['ping_ms']}мс")
    lines.append(f"Скорость: {speed['download_speed_kbps']} KB/s")
    lines.append("")
    lines.append("📊 ЗАПРОСЫ:")
    lines.append(f"В минуту: {network_stats['requests_last_minute']}")
    lines.append(f"В час: {network_stats['requests_last_hour']}")
    lines.append(f"Всего сегодня: {network_stats['total_requests_today']}")
    lines.append(f"Токенов сегодня: {network_stats['total_tokens_today']}")
    lines.append("")
    lines.append("🔑 ЛИМИТЫ:")
    limits = get_rate_limit_info()
    lines.append(f"Telegram: {limits['telegram_limit']}")
    lines.append(f"OpenRouter: {limits['openrouter_limit']}")
    lines.append("=" * 40)
    
    return "\n".join(lines)

# ============================================================
# 6. ФОНОВЫЙ ЦИКЛ
# ============================================================

def monitor_loop(bot, owner_ids):
    """Мониторинг в фоне"""
    while True:
        time.sleep(60)
        
        network_stats["requests_last_minute"] = 0
        
        speed = check_internet_speed()
        
        if not speed["online"]:
            for oid in owner_ids:
                try:
                    bot.send_message(oid, "❌ Интернет пропал!")
                except Exception:
                    pass

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📡 Модуль мониторинга сети загружен")