"""Кэш ответов — запоминает одинаковые запросы для экономии токенов"""

import os
import json
import hashlib
import time
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

CACHE_FILE = "response_cache.json"
MAX_CACHE_SIZE = 500
CACHE_TTL = 86400  # 24 часа

# ============================================================
# 2. ДАННЫЕ
# ============================================================

cache_data = {
    "responses": {},
    "stats": {
        "total_cached": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_uses": 0,
    }
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения кэша: {e}")
        return False

def load_cache():
    global cache_data
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                cache_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки кэша: {e}")
        return False

load_cache()

# ============================================================
# 4. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def get_text_hash(text):
    """Получить хэш текста"""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def find_cached_response(text, user_id=None):
    """Найти закэшированный ответ"""
    text_hash = get_text_hash(text)
    
    if text_hash in cache_data["responses"]:
        response_data = cache_data["responses"][text_hash]
        
        # Проверяем TTL
        try:
            created = datetime.fromisoformat(response_data.get("time", "2000-01-01"))
            if (datetime.now() - created).total_seconds() > CACHE_TTL:
                del cache_data["responses"][text_hash]
                save_cache()
                return None
        except:
            pass
        
        cache_data["stats"]["cache_hits"] += 1
        cache_data["stats"]["total_uses"] += 1
        save_cache()
        return response_data.get("response")
    
    cache_data["stats"]["cache_misses"] += 1
    save_cache()
    return None

def save_to_cache(text, response, user_id=None, chat_id=None):
    """Сохранить ответ в кэш"""
    text_hash = get_text_hash(text)
    
    if text_hash in cache_data["responses"]:
        return True
    
    # Проверяем размер
    if len(cache_data["responses"]) >= MAX_CACHE_SIZE:
        # Удаляем старые
        oldest = min(cache_data["responses"].items(), key=lambda x: x[1].get("time", ""))
        del cache_data["responses"][oldest[0]]
    
    cache_data["responses"][text_hash] = {
        "text": text,
        "response": response,
        "user_id": user_id,
        "chat_id": chat_id,
        "time": datetime.now().isoformat(),
        "uses": 1,
    }
    cache_data["stats"]["total_cached"] = len(cache_data["responses"])
    save_cache()
    return True

def get_or_generate_response(text, user_id, generate_func, *args, **kwargs):
    """Получить ответ из кэша или сгенерировать новый"""
    cached = find_cached_response(text, user_id)
    if cached:
        return cached
    
    response = generate_func(text, *args, **kwargs)
    
    if response and len(response) > 10 and len(response) < 500:
        save_to_cache(text, response, user_id)
    
    return response

def get_cache_stats():
    return cache_data["stats"]

def format_cache_stats():
    stats = get_cache_stats()
    return f"📦 Кэш ответов: {stats['total_cached']} записей, попаданий: {stats['cache_hits']}"

print("📦 Модуль кэша ответов загружен")
print(f"📊 Всего закэшировано: {cache_data['stats']['total_cached']}")