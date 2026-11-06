"""Статистика и проверка моделей ИИ"""

import json
import os
import time
import requests
import threading
from datetime import datetime
from collections import defaultdict

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from ai_models import FREE_MODELS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

AI_ROUTER_FILE = "ai_router_stats.json"
MODEL_CHECK_INTERVAL = 60
MAX_FAILURES_BEFORE_DISABLE = 3

# ============================================================
# 3. СТАТИСТИКА
# ============================================================

router_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "fallback_events": 0,
    "model_stats": {},
    "task_distribution": defaultdict(int),
    "disabled_models": [],
    "last_updated": None,
}

# ============================================================
# 4. ЗАГРУЗКА/СОХРАНЕНИЕ
# ============================================================

def load_router_stats():
    global router_stats
    try:
        if os.path.exists(AI_ROUTER_FILE):
            with open(AI_ROUTER_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                router_stats.update(loaded)
                router_stats["task_distribution"] = defaultdict(
                    int, router_stats.get("task_distribution", {})
                )
        return True
    except Exception:
        return False


def save_router_stats():
    try:
        data = {
            "total_requests": router_stats["total_requests"],
            "successful_requests": router_stats["successful_requests"],
            "failed_requests": router_stats["failed_requests"],
            "fallback_events": router_stats["fallback_events"],
            "model_stats": router_stats["model_stats"],
            "task_distribution": dict(router_stats["task_distribution"]),
            "disabled_models": router_stats["disabled_models"],
            "last_updated": datetime.now().isoformat(),
        }
        with open(AI_ROUTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


load_router_stats()

# ============================================================
# 5. ПРОВЕРКА МОДЕЛЕЙ
# ============================================================

def check_model_availability(model_id):
    try:
        from config import OPENROUTER_KEY
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False


def check_all_models_loop():
    while True:
        time.sleep(MODEL_CHECK_INTERVAL * 2)
        try:
            for model_id in FREE_MODELS:
                if model_id in router_stats["disabled_models"]:
                    continue
                
                is_available = check_model_availability(model_id)
                FREE_MODELS[model_id]["available"] = is_available
                FREE_MODELS[model_id]["last_check"] = datetime.now().isoformat()
                
                if not is_available:
                    failures = FREE_MODELS[model_id].get("failures", 0)
                    if failures >= MAX_FAILURES_BEFORE_DISABLE:
                        if model_id not in router_stats["disabled_models"]:
                            router_stats["disabled_models"].append(model_id)
                            print(f"🔒 Модель {model_id} заморожена")
                            save_router_stats()
                    else:
                        FREE_MODELS[model_id]["failures"] = failures + 1
                else:
                    if model_id in router_stats["disabled_models"]:
                        router_stats["disabled_models"].remove(model_id)
                        FREE_MODELS[model_id]["failures"] = 0
                        print(f"🔓 Модель {model_id} разморожена")
                        save_router_stats()
        except Exception:
            pass


def start_model_checker():
    thread = threading.Thread(target=check_all_models_loop, daemon=True)
    thread.start()
    print("🔍 Проверка моделей запущена")

# ============================================================
# 6. СТАТИСТИКА (ДЛЯ КОМАНД)
# ============================================================

def get_router_stats():
    return {
        "total_requests": router_stats.get("total_requests", 0),
        "successful": router_stats.get("successful_requests", 0),
        "failed": router_stats.get("failed_requests", 0),
        "fallbacks": router_stats.get("fallback_events", 0),
        "disabled_models": router_stats.get("disabled_models", []),
        "models": len(FREE_MODELS),
        "available_models": len([
            m for m, d in FREE_MODELS.items()
            if d.get("available", False)
            and m not in router_stats.get("disabled_models", [])
        ]),
        "last_updated": router_stats.get("last_updated"),
    }


def get_available_models():
    available = []
    for model_id, data in FREE_MODELS.items():
        if data.get("available", False) and model_id not in router_stats.get("disabled_models", []):
            available.append({
                "id": model_id,
                "name": data.get("name", model_id),
                "provider": data.get("provider", "Unknown"),
                "strengths": data.get("strengths", []),
                "speed": data.get("speed", 0.5),
                "quality": data.get("quality", 0.5),
            })
    return available


def get_disabled_models():
    return router_stats.get("disabled_models", [])


def reset_model(model_id):
    if model_id in router_stats.get("disabled_models", []):
        router_stats["disabled_models"].remove(model_id)
        if model_id in FREE_MODELS:
            FREE_MODELS[model_id]["failures"] = 0
            FREE_MODELS[model_id]["available"] = True
        save_router_stats()
        return True
    return False


def format_router_stats():
    stats = get_router_stats()
    lines = [
        "🤖 СТАТИСТИКА МАРШРУТИЗАТОРА ИИ:",
        f"📊 Всего запросов: {stats['total_requests']}",
        f"✅ Успешных: {stats['successful']}",
        f"❌ Ошибок: {stats['failed']}",
        f"📈 Успешность: {stats['successful'] / max(1, stats['total_requests']) * 100:.1f}%",
        f"🔄 Переключений: {stats['fallbacks']}",
        f"🔒 Заморожено моделей: {len(stats['disabled_models'])}",
        f"🧠 Всего моделей: {stats['models']}",
        f"✅ Доступно: {stats['available_models']}",
    ]
    
    if stats['last_updated']:
        lines.append(f"🕐 Обновлено: {stats['last_updated'][:16]}")
    
    available = get_available_models()
    if available:
        lines.append("\n📋 ДОСТУПНЫЕ МОДЕЛИ:")
        for m in available[:5]:
            lines.append(f"  • {m['name']} ({m['provider']})")
    
    disabled = get_disabled_models()
    if disabled:
        lines.append("\n🔒 ЗАМОРОЖЕННЫЕ МОДЕЛИ:")
        for m in disabled[:5]:
            name = FREE_MODELS.get(m, {}).get("name", m)
            lines.append(f"  • {name}")
    
    return "\n".join(lines)

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print(f"📊 Статистика маршрутизатора загружена")
print(f"🔒 Заморожено: {len(router_stats['disabled_models'])}")

start_model_checker()