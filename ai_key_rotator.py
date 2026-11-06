"""Управление ключами ИИ — ротация по %, статистика по каждому ключу, общий лимит"""

import json
import os
import time
import random
import threading
import requests
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

KEY_STATS_FILE = "key_stats.json"
STATS_UPDATE_INTERVAL = 300
OPENROUTER_LIMIT_PER_KEY = 200   # OpenRouter бесплатный лимит на ключ
GEMINI_LIMIT = 1500              # Gemini бесплатный лимит
HUGGINGFACE_LIMIT = 2000         # Hugging Face бесплатный лимит

# ============================================================
# 2. ДАННЫЕ СТАТИСТИКИ КЛЮЧЕЙ
# ============================================================

key_stats = {
    "openrouter": {},  # {key: {"email": str, "total": int, "used": int, "remaining": int, "status": str, "last_used": str, "percent": float}}
    "gemini": {"total": GEMINI_LIMIT, "used": 0, "remaining": GEMINI_LIMIT, "status": "active", "last_used": None, "percent": 100.0},
    "huggingface": {"total": HUGGINGFACE_LIMIT, "used": 0, "remaining": HUGGINGFACE_LIMIT, "status": "active", "last_used": None, "percent": 100.0},
    "last_update": None,
    "total_requests_today": 0,
    "requests_last_hour": 0,
    "requests_24h": 0,
    "request_history": [],
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_key_stats():
    try:
        with open(KEY_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(key_stats, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения статистики ключей: {e}")
        return False

def load_key_stats():
    global key_stats
    try:
        if os.path.exists(KEY_STATS_FILE):
            with open(KEY_STATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                key_stats.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки статистики ключей: {e}")
        return False

load_key_stats()

# ============================================================
# 4. ИНИЦИАЛИЗАЦИЯ КЛЮЧЕЙ
# ============================================================

def init_keys(openrouter_keys, openrouter_emails, gemini_key, huggingface_key):
    """Инициализировать все ключи"""
    
    # OpenRouter ключи
    for i, key in enumerate(openrouter_keys):
        email = openrouter_emails[i] if i < len(openrouter_emails) else f"key_{i+1}@gmail.com"
        if key not in key_stats["openrouter"]:
            key_stats["openrouter"][key] = {
                "email": email,
                "total": OPENROUTER_LIMIT_PER_KEY,
                "used": 0,
                "remaining": OPENROUTER_LIMIT_PER_KEY,
                "status": "active",
                "last_used": None,
                "failures": 0,
                "percent": 100.0,
            }
        else:
            # Обновляем если ключ уже есть
            if key_stats["openrouter"][key].get("total", 0) == 0:
                key_stats["openrouter"][key]["total"] = OPENROUTER_LIMIT_PER_KEY
                key_stats["openrouter"][key]["remaining"] = OPENROUTER_LIMIT_PER_KEY
                key_stats["openrouter"][key]["percent"] = 100.0
    
    # Gemini
    if gemini_key:
        remaining = GEMINI_LIMIT - key_stats["gemini"].get("used", 0)
        key_stats["gemini"] = {
            "total": GEMINI_LIMIT,
            "used": key_stats["gemini"].get("used", 0),
            "remaining": max(0, remaining),
            "status": "active" if remaining > 0 else "exhausted",
            "last_used": key_stats["gemini"].get("last_used"),
            "percent": (remaining / GEMINI_LIMIT) * 100 if GEMINI_LIMIT > 0 else 0,
        }
    
    # Hugging Face
    if huggingface_key:
        remaining = HUGGINGFACE_LIMIT - key_stats["huggingface"].get("used", 0)
        key_stats["huggingface"] = {
            "total": HUGGINGFACE_LIMIT,
            "used": key_stats["huggingface"].get("used", 0),
            "remaining": max(0, remaining),
            "status": "active" if remaining > 0 else "exhausted",
            "last_used": key_stats["huggingface"].get("last_used"),
            "percent": (remaining / HUGGINGFACE_LIMIT) * 100 if HUGGINGFACE_LIMIT > 0 else 0,
        }
    
    save_key_stats()
    print(f"🔑 Инициализировано ключей: {len(key_stats['openrouter'])} OpenRouter, 1 Gemini, 1 Hugging Face")
    return key_stats

# ============================================================
# 5. РОТАЦИЯ OPENROUTER КЛЮЧЕЙ (ПО % ОСТАТКА)
# ============================================================

def get_best_openrouter_key():
    """Получить лучший доступный ключ OpenRouter по % остатка"""
    
    if not key_stats["openrouter"]:
        return None
    
    active_keys = []      # > 50%
    low_keys = []         # 10-50%
    exhausted_keys = []   # 0-10%
    
    for key, data in key_stats["openrouter"].items():
        status = data.get("status", "active")
        remaining = data.get("remaining", 0)
        
        if status == "disabled":
            continue
        
        total = data.get("total", OPENROUTER_LIMIT_PER_KEY)
        percent = (remaining / total) * 100 if total > 0 else 0
        data["percent"] = percent  # Обновляем процент
        
        if percent >= 50:
            active_keys.append((key, percent, data.get("email", key[:20])))
        elif percent >= 10:
            low_keys.append((key, percent, data.get("email", key[:20])))
        else:
            exhausted_keys.append((key, percent, data.get("email", key[:20])))
    
    # 1. Если есть ключи с > 50% — берём случайный из них
    if active_keys:
        selected = random.choice(active_keys)
        print(f"🔑 Выбран ключ {selected[2]} — {selected[1]:.1f}% (активный)")
        return selected[0]
    
    # 2. Если есть ключи с 10-50% — берём случайный
    if low_keys:
        selected = random.choice(low_keys)
        print(f"⚠️ Выбран ключ {selected[2]} — {selected[1]:.1f}% (низкий)")
        return selected[0]
    
    # 3. Если есть ключи с 0-10% — берём случайный (последний шанс)
    if exhausted_keys:
        selected = random.choice(exhausted_keys)
        print(f"🔴 Выбран ключ {selected[2]} — {selected[1]:.1f}% (истощён)")
        return selected[0]
    
    # 4. Если все ключи закончились
    return None

def use_openrouter_key(key):
    """Использовать ключ (увеличить счётчик)"""
    if key in key_stats["openrouter"]:
        data = key_stats["openrouter"][key]
        data["used"] = data.get("used", 0) + 1
        data["remaining"] = data.get("remaining", OPENROUTER_LIMIT_PER_KEY) - 1
        data["last_used"] = datetime.now().isoformat()
        
        total = data.get("total", OPENROUTER_LIMIT_PER_KEY)
        percent = (data["remaining"] / total) * 100 if total > 0 else 0
        data["percent"] = percent
        
        # Обновляем статус
        if percent < 10:
            data["status"] = "exhausted"
        elif percent < 50:
            data["status"] = "low"
        else:
            data["status"] = "active"
        
        # Обновляем общую статистику
        key_stats["total_requests_today"] = key_stats.get("total_requests_today", 0) + 1
        now = datetime.now()
        key_stats["request_history"].append(now.isoformat())
        
        # Очищаем старые записи (старше 24 часов)
        cutoff = now - timedelta(hours=24)
        key_stats["request_history"] = [
            t for t in key_stats["request_history"] 
            if datetime.fromisoformat(t) > cutoff
        ]
        
        # Обновляем статистику за час и 24 часа
        key_stats["requests_last_hour"] = sum(
            1 for t in key_stats["request_history"] 
            if (now - datetime.fromisoformat(t)).total_seconds() < 3600
        )
        key_stats["requests_24h"] = len(key_stats["request_history"])
        key_stats["last_update"] = now.isoformat()
        
        save_key_stats()
        return True
    return False

def get_openrouter_key_status(key):
    return key_stats["openrouter"].get(key)

def get_all_openrouter_keys_status():
    return key_stats["openrouter"]

# ============================================================
# 6. ИСПОЛЬЗОВАНИЕ ДОПОЛНИТЕЛЬНЫХ КЛЮЧЕЙ
# ============================================================

def use_gemini_key(amount=1):
    if key_stats["gemini"]["status"] == "disabled":
        return False
    
    key_stats["gemini"]["used"] = key_stats["gemini"].get("used", 0) + amount
    key_stats["gemini"]["remaining"] = key_stats["gemini"]["total"] - key_stats["gemini"]["used"]
    key_stats["gemini"]["last_used"] = datetime.now().isoformat()
    key_stats["gemini"]["percent"] = (key_stats["gemini"]["remaining"] / key_stats["gemini"]["total"]) * 100 if key_stats["gemini"]["total"] > 0 else 0
    
    if key_stats["gemini"]["remaining"] <= 0:
        key_stats["gemini"]["status"] = "exhausted"
    elif key_stats["gemini"]["remaining"] < 100:
        key_stats["gemini"]["status"] = "low"
    
    save_key_stats()
    return True

def use_huggingface_key(amount=1):
    if key_stats["huggingface"]["status"] == "disabled":
        return False
    
    key_stats["huggingface"]["used"] = key_stats["huggingface"].get("used", 0) + amount
    key_stats["huggingface"]["remaining"] = key_stats["huggingface"]["total"] - key_stats["huggingface"]["used"]
    key_stats["huggingface"]["last_used"] = datetime.now().isoformat()
    key_stats["huggingface"]["percent"] = (key_stats["huggingface"]["remaining"] / key_stats["huggingface"]["total"]) * 100 if key_stats["huggingface"]["total"] > 0 else 0
    
    if key_stats["huggingface"]["remaining"] <= 0:
        key_stats["huggingface"]["status"] = "exhausted"
    elif key_stats["huggingface"]["remaining"] < 100:
        key_stats["huggingface"]["status"] = "low"
    
    save_key_stats()
    return True

# ============================================================
# 7. СТАТИСТИКА (ОБЩАЯ И ПО КЛЮЧАМ)
# ============================================================

def get_total_requests():
    total = 0
    for key, data in key_stats["openrouter"].items():
        total += data.get("used", 0)
    total += key_stats.get("gemini", {}).get("used", 0)
    total += key_stats.get("huggingface", {}).get("used", 0)
    return total

def get_total_remaining():
    total = 0
    for key, data in key_stats["openrouter"].items():
        total += data.get("remaining", 0)
    total += key_stats.get("gemini", {}).get("remaining", 0)
    total += key_stats.get("huggingface", {}).get("remaining", 0)
    return total

def get_total_limit():
    total = 0
    for key, data in key_stats["openrouter"].items():
        total += data.get("total", OPENROUTER_LIMIT_PER_KEY)
    total += key_stats.get("gemini", {}).get("total", 0)
    total += key_stats.get("huggingface", {}).get("total", 0)
    return total

def get_active_keys_count():
    active = 0
    for key, data in key_stats["openrouter"].items():
        if data.get("status") not in ["disabled", "exhausted"]:
            active += 1
    return active

def get_disabled_keys_count():
    disabled = 0
    for key, data in key_stats["openrouter"].items():
        if data.get("status") == "disabled":
            disabled += 1
    return disabled

def get_key_stats_summary():
    """Получить сводку по всем ключам"""
    total_limit = get_total_limit()
    total_used = get_total_requests()
    total_remaining = get_total_remaining()
    
    return {
        "total_keys": len(key_stats["openrouter"]),
        "active_keys": get_active_keys_count(),
        "disabled_keys": get_disabled_keys_count(),
        "total_used": total_used,
        "total_remaining": total_remaining,
        "total_limit": total_limit,
        "percent_used": (total_used / total_limit) * 100 if total_limit > 0 else 0,
        "requests_last_hour": key_stats.get("requests_last_hour", 0),
        "requests_24h": key_stats.get("requests_24h", 0),
        "gemini_remaining": key_stats.get("gemini", {}).get("remaining", 0),
        "gemini_percent": key_stats.get("gemini", {}).get("percent", 0),
        "huggingface_remaining": key_stats.get("huggingface", {}).get("remaining", 0),
        "huggingface_percent": key_stats.get("huggingface", {}).get("percent", 0),
        "last_update": key_stats.get("last_update"),
    }

def format_key_stats():
    """Форматировать статистику ключей"""
    summary = get_key_stats_summary()
    lines = [
        "🔑 СТАТИСТИКА КЛЮЧЕЙ:",
        f"📊 Всего ключей: {summary['total_keys']}",
        f"✅ Активных: {summary['active_keys']}",
        f"❌ Отключённых: {summary['disabled_keys']}",
        "",
        f"📈 ОБЩАЯ СТАТИСТИКА:",
        f"   Всего запросов: {summary['total_used']}",
        f"   Осталось: {summary['total_remaining']}",
        f"   Лимит: {summary['total_limit']}",
        f"   Использовано: {summary['percent_used']:.1f}%",
        "",
        f"⏱ ЗА ЧАС: {summary['requests_last_hour']}",
        f"⏱ ЗА 24 ЧАСА: {summary['requests_24h']}",
        "",
        f"🔑 GEMINI: {summary['gemini_remaining']}/{GEMINI_LIMIT} ({summary['gemini_percent']:.1f}%)",
        f"🔑 HUGGING FACE: {summary['huggingface_remaining']}/{HUGGINGFACE_LIMIT} ({summary['huggingface_percent']:.1f}%)",
    ]
    return "\n".join(lines)

# ============================================================
# 8. АВТООБНОВЛЕНИЕ
# ============================================================

def auto_update_stats_loop():
    while True:
        time.sleep(STATS_UPDATE_INTERVAL)
        try:
            key_stats["total_requests_today"] = get_total_requests()
            key_stats["last_update"] = datetime.now().isoformat()
            save_key_stats()
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")

def start_stats_updater():
    thread = threading.Thread(target=auto_update_stats_loop, daemon=True)
    thread.start()
    print("📊 Автообновление статистики ключей запущено")

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("🔑 Модуль ротации ключей загружен")
summary = get_key_stats_summary()
print(f"📊 OpenRouter ключей: {summary['total_keys']}")
print(f"📊 Всего запросов: {summary['total_used']}")
print(f"📊 Осталось: {summary['total_remaining']}")
print(f"📊 Лимит: {summary['total_limit']}")