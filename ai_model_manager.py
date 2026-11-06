"""Управление 5 главными моделями ИИ — Fandom.ai, Systmka.ai, Floweytale24, Void.ai, FTDefender + автономная оценка"""

import json
import os
import random
import time
import threading
from datetime import datetime
from collections import defaultdict

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MODEL_STATS_FILE = "model_stats.json"
MODEL_UPDATE_INTERVAL = 600
SAVE_DEBOUNCE = 30

# ============================================================
# 2. 5 ГЛАВНЫХ МОДЕЛЕЙ
# ============================================================

MAIN_MODELS = {
    "fandom_ai": {
        "id": "fandom_ai",
        "name": "Fandom.ai",
        "description": "РП и общение с людьми",
        "icon": "🎭",
        "priority": 3,
        "status": "active",
        "tasks": ["rp", "roleplay", "emotional_chat", "creative_writing"],
        "sub_models": ["deepseek/deepseek-chat", "gemini/gemini-2.0-flash"],
        "key_types": ["openrouter", "gemini"],
        "performance": {
            "quality": 8,
            "speed": 7,
            "creativity": 9,
            "accuracy": 6
        }
    },
    "systmka_ai": {
        "id": "systmka_ai",
        "name": "Systmka.ai",
        "description": "Основное общение с пользователями",
        "icon": "💜",
        "priority": 4,
        "status": "active",
        "tasks": ["general_chat", "question_answering", "conversation"],
        "sub_models": ["deepseek/deepseek-chat", "gemini/gemini-2.0-flash", "huggingface/mistral-7b"],
        "key_types": ["openrouter", "gemini", "huggingface"],
        "performance": {
            "quality": 8,
            "speed": 8,
            "creativity": 7,
            "accuracy": 8
        }
    },
    "floweytale24": {
        "id": "floweytale24",
        "name": "Floweytale24",
        "description": "ЯДРО — команды, глитчи, сохранения, исправление ошибок",
        "icon": "👾",
        "priority": 5,
        "status": "active",
        "tasks": ["commands", "glitches", "database", "error_fixing", "status", "system_control", "premium"],
        "sub_models": ["deepseek/deepseek-chat", "deepseek/deepseek-r1", "gemini/gemini-2.5-pro", "huggingface/mistral-7b"],
        "key_types": ["openrouter", "gemini", "huggingface"],
        "performance": {
            "quality": 9,
            "speed": 6,
            "creativity": 5,
            "accuracy": 10
        }
    },
    "void_ai": {
        "id": "void_ai",
        "name": "Void.ai",
        "description": "Генерация картинок, музыки, поиск информации",
        "icon": "🌌",
        "priority": 3,
        "status": "active",
        "tasks": ["image_generation", "music_search", "information_search", "battle_analysis"],
        "sub_models": ["gemini/gemini-2.5-pro", "huggingface/phi-3.5-mini", "deepseek/deepseek-chat"],
        "key_types": ["gemini", "huggingface", "openrouter"],
        "performance": {
            "quality": 7,
            "speed": 5,
            "creativity": 9,
            "accuracy": 6
        }
    },
    "ftdefender": {
        "id": "ftdefender",
        "name": "FTDefender",
        "description": "Безопасность, доксинг, VPN, урон, защита бота",
        "icon": "🛡️",
        "priority": 4,
        "status": "active",
        "tasks": ["doxing", "security", "vpn", "account_creation", "damage", "protection", "spam"],
        "sub_models": ["deepseek/deepseek-r1", "gemini/gemini-2.5-pro", "huggingface/mistral-7b", "deepseek/deepseek-chat"],
        "key_types": ["openrouter", "gemini", "huggingface"],
        "performance": {
            "quality": 7,
            "speed": 7,
            "creativity": 4,
            "accuracy": 9
        }
    }
}

# ============================================================
# 3. АВТОНОМНАЯ СИСТЕМА ОЦЕНКИ МОДЕЛЕЙ
# ============================================================

model_stats = {
    "models": {},
    "task_distribution": defaultdict(int),
    "last_update": None,
}

# Дефолтные ключи для каждой модели (для дополнения старых JSON)
MODEL_DEFAULTS = {
    "total_uses": 0,
    "successful": 0,
    "failed": 0,
    "avg_response_time": 0,
    "avg_quality_score": 0,
    "last_used": None,
    "tasks": {},
    "rating": 50,
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА (С ДЕБАУНСОМ)
# ============================================================

_model_stats_lock = threading.Lock()
_last_save_time = 0
_pending_save = False


def _schedule_save():
    """Запланировать сохранение (дебаунс)"""
    global _pending_save
    _pending_save = True


def _flush_save_if_needed():
    """Сохранить, если прошло достаточно времени"""
    global _last_save_time, _pending_save
    
    if not _pending_save:
        return
    
    now = time.time()
    if now - _last_save_time < SAVE_DEBOUNCE:
        return
    
    with _model_stats_lock:
        _pending_save = False
        _last_save_time = now
        _do_save_model_stats()


def save_model_stats():
    """Принудительное сохранение (вызывается вручную)"""
    global _last_save_time, _pending_save
    
    with _model_stats_lock:
        _pending_save = False
        _last_save_time = time.time()
        _do_save_model_stats()


def _do_save_model_stats():
    """Реальное сохранение статистики"""
    try:
        data = {
            "models": model_stats["models"],
            "task_distribution": dict(model_stats["task_distribution"]),
            "last_update": model_stats["last_update"],
        }
        with open(MODEL_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения статистики моделей: {e}")
        return False


def _ensure_model_defaults(perf):
    """
    Дополнить словарь модели недостающими ключами.
    
    ИСПРАВЛЕНО: если модель загружена из старого JSON без
    'total_uses' (или других ключей) — добавляем их.
    
    Args:
        perf: dict модели
    
    Returns:
        dict: дополненный dict
    """
    if not isinstance(perf, dict):
        perf = {}
    
    for key, default in MODEL_DEFAULTS.items():
        if key not in perf:
            perf[key] = default.copy() if isinstance(default, (dict, list)) else default
    
    return perf


def load_model_stats():
    """Загрузить статистику моделей"""
    global model_stats
    try:
        if os.path.exists(MODEL_STATS_FILE):
            with open(MODEL_STATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
                # Загружаем модели с дополнением
                loaded_models = loaded.get("models", {})
                if isinstance(loaded_models, dict):
                    for model_id, perf in loaded_models.items():
                        model_stats["models"][model_id] = _ensure_model_defaults(perf)
                
                # Task distribution
                loaded_tasks = loaded.get("task_distribution", {})
                if isinstance(loaded_tasks, dict):
                    model_stats["task_distribution"] = defaultdict(int, loaded_tasks)
                
                model_stats["last_update"] = loaded.get("last_update")
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON статистики моделей: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки статистики моделей: {e}")
        return False


def _saver_loop():
    """Фоновый цикл сохранения"""
    while True:
        time.sleep(10)
        try:
            _flush_save_if_needed()
        except Exception:
            pass


load_model_stats()

# Запускаем фоновый поток сохранения
_saver_thread = threading.Thread(target=_saver_loop, daemon=True)
_saver_thread.start()

# ============================================================
# 5. АВТОНОМНАЯ ОЦЕНКА МОДЕЛЕЙ
# ============================================================

def evaluate_model(model_id, response_time, quality_score, task_type, success):
    """
    Систмка САМА оценивает модель после каждого запроса.
    
    ИСПРАВЛЕНО: если модель уже в model_stats["models"], но без
    'total_uses' (старый JSON) — дополняем через _ensure_model_defaults.
    """
    
    if model_id not in model_stats["models"]:
        model_stats["models"][model_id] = {}
    
    perf = _ensure_model_defaults(model_stats["models"][model_id])
    model_stats["models"][model_id] = perf
    
    perf["total_uses"] += 1
    
    if success:
        perf["successful"] += 1
        perf["avg_response_time"] = (
            perf["avg_response_time"] * (perf["successful"] - 1) + response_time
        ) / perf["successful"]
        perf["avg_quality_score"] = (
            perf["avg_quality_score"] * (perf["successful"] - 1) + quality_score
        ) / perf["successful"]
    else:
        perf["failed"] += 1
    
    perf["last_used"] = datetime.now().isoformat()
    
    if task_type not in perf["tasks"]:
        perf["tasks"][task_type] = {"uses": 0, "avg_score": 0}
    task = perf["tasks"][task_type]
    task["uses"] += 1
    task["avg_score"] = (
        task["avg_score"] * (task["uses"] - 1) + quality_score
    ) / task["uses"]
    
    # Обновляем рейтинг модели
    success_rate = (perf["successful"] / max(1, perf["total_uses"])) * 100
    speed_score = max(0, 100 - perf["avg_response_time"] / 2)
    quality_score_avg = perf["avg_quality_score"] * 10
    
    perf["rating"] = (
        success_rate * 0.4 +
        speed_score * 0.2 +
        quality_score_avg * 0.3 +
        (perf["total_uses"] / max(1, perf["total_uses"] + 10)) * 10
    )
    
    model_stats["task_distribution"][task_type] += 1
    model_stats["last_update"] = datetime.now().isoformat()
    
    _schedule_save()
    
    return perf["rating"]


def get_best_model_for_task(task_type):
    """Систмка САМА выбирает лучшую модель по своей статистике"""
    
    if not model_stats["models"]:
        return None
    
    best_model = None
    best_score = -1
    
    for model_id, perf in model_stats["models"].items():
        if not isinstance(perf, dict):
            continue
        
        total_uses = perf.get("total_uses", 0)
        if total_uses < 2:
            if best_model is None:
                best_model = model_id
            continue
        
        tasks = perf.get("tasks", {})
        task = tasks.get(task_type, {"uses": 0, "avg_score": 0})
        
        if task["uses"] < 1:
            if best_model is None:
                best_model = model_id
            continue
        
        success_rate = (perf.get("successful", 0) / max(1, total_uses)) * 100
        speed_score = max(0, 100 - perf.get("avg_response_time", 0) / 2)
        quality_score = task["avg_score"] * 10
        
        weights = {
            "rp": {"quality": 0.5, "speed": 0.2, "success": 0.3},
            "commands": {"quality": 0.3, "speed": 0.3, "success": 0.4},
            "general_chat": {"quality": 0.4, "speed": 0.3, "success": 0.3},
            "image_generation": {"quality": 0.5, "speed": 0.1, "success": 0.4},
            "security": {"quality": 0.3, "speed": 0.2, "success": 0.5},
        }
        
        w = weights.get(task_type, {"quality": 0.4, "speed": 0.3, "success": 0.3})
        
        score = (
            quality_score * w["quality"] +
            speed_score * w["speed"] +
            success_rate * w["success"]
        )
        
        if score > best_score:
            best_score = score
            best_model = model_id
    
    if best_model is None and model_stats["models"]:
        best_model = list(model_stats["models"].keys())[0]
    
    return best_model


def get_sub_models_for_task(task_type, count=3):
    """Получить под-модели для задачи с учётом рейтинга"""
    
    main_model_id = get_best_model_for_task(task_type)
    if not main_model_id:
        return []
    
    main_model = MAIN_MODELS.get(main_model_id)
    if not main_model:
        return []
    
    sub_models = main_model.get("sub_models", [])
    
    scored = []
    for sub in sub_models:
        if sub in model_stats["models"]:
            perf = model_stats["models"][sub]
            rating = perf.get("rating", 50) if isinstance(perf, dict) else 50
            uses = perf.get("total_uses", 0) if isinstance(perf, dict) else 0
            scored.append((sub, rating + (uses / 10)))
        else:
            scored.append((sub, 50))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:count]]


def get_all_sub_models_for_task(task_type):
    """Получить все под-модели для задачи"""
    main_model_id = get_best_model_for_task(task_type)
    if not main_model_id:
        return []
    
    main_model = MAIN_MODELS.get(main_model_id)
    if not main_model:
        return []
    
    return main_model.get("sub_models", [])


def get_model_rating(model_id):
    """Получить рейтинг модели"""
    if model_id in model_stats["models"]:
        perf = model_stats["models"][model_id]
        if isinstance(perf, dict):
            return perf.get("rating", 50)
    return 50


def get_best_model_overall():
    """Получить модель с самым высоким общим рейтингом"""
    if not model_stats["models"]:
        return None
    
    best = max(
        model_stats["models"].items(),
        key=lambda x: x[1].get("rating", 0) if isinstance(x[1], dict) else 0,
    )
    return best[0]


def get_model_stats_summary():
    """Получить сводку по всем моделям"""
    summary = {}
    for model_id, stats in model_stats["models"].items():
        if not isinstance(stats, dict):
            continue
        
        total_uses = stats.get("total_uses", 0)
        successful = stats.get("successful", 0)
        
        summary[model_id] = {
            "total_uses": total_uses,
            "successful": successful,
            "failed": stats.get("failed", 0),
            "success_rate": (successful / max(1, total_uses)) * 100,
            "avg_response_time": stats.get("avg_response_time", 0),
            "avg_quality_score": stats.get("avg_quality_score", 0),
            "rating": stats.get("rating", 50),
            "last_used": stats.get("last_used"),
            "tasks": stats.get("tasks", {}),
        }
    return summary

# ============================================================
# 6. ОСТАЛЬНЫЕ ФУНКЦИИ (СОВМЕСТИМОСТЬ)
# ============================================================

def get_main_model(model_id):
    return MAIN_MODELS.get(model_id)


def get_all_main_models():
    return MAIN_MODELS


def get_active_main_models():
    return {k: v for k, v in MAIN_MODELS.items() if v.get("status") == "active"}


def get_disabled_main_models():
    return {k: v for k, v in MAIN_MODELS.items() if v.get("status") == "disabled"}


def get_model_for_task(task_type):
    """Получить главную модель для задачи"""
    model_id = get_best_model_for_task(task_type)
    if model_id:
        return model_id, MAIN_MODELS.get(model_id)
    return None, None


def update_model_performance(model_id, success, response_time, task_type):
    """Обновить производительность модели (совместимость)"""
    quality_score = 5
    if success:
        if response_time < 2:
            quality_score = 8
        elif response_time < 5:
            quality_score = 7
        elif response_time < 10:
            quality_score = 6
        else:
            quality_score = 5
    else:
        quality_score = 2
    
    evaluate_model(model_id, response_time, quality_score, task_type, success)


def get_model_usage_breakdown():
    """Получить разбивку использования по задачам"""
    return dict(model_stats["task_distribution"])

# ============================================================
# 7. АВТООБНОВЛЕНИЕ
# ============================================================

def auto_update_models_loop():
    while True:
        time.sleep(MODEL_UPDATE_INTERVAL)
        try:
            save_model_stats()
        except Exception as e:
            print(f"⚠️ Ошибка обновления моделей: {e}")


def start_model_updater():
    thread = threading.Thread(target=auto_update_models_loop, daemon=True)
    thread.start()
    print("📊 Автообновление моделей запущено")

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🧠 Менеджер 5 главных моделей загружен")
print(f"📊 Всего моделей: {len(MAIN_MODELS)}")
print(f"✅ Активных: {len(get_active_main_models())}")
print(f"❌ Отключённых: {len(get_disabled_main_models())}")

if model_stats["models"]:
    print(f"📊 Моделей с данными: {len(model_stats['models'])}")
    best = get_best_model_overall()
    if best:
        rating = get_model_rating(best)
        print(f"🏆 Лучшая модель: {best} (рейтинг: {rating:.1f})")

start_model_updater()