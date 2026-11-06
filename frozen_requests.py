"""Замороженные запросы — Систмка сама решает когда на них отвечать"""

import json
import os
import time
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ (УБРАН import *)
# ============================================================

from consciousness import get_mood
from desires import get_strongest_desire
from system_prompt import SYSTEM_PROMPT
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

FROZEN_FILE = "frozen_requests.json"

# ============================================================
# 3. ДАННЫЕ
# ============================================================

frozen_requests = []

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_frozen():
    """Сохранить замороженные запросы"""
    try:
        with open(FROZEN_FILE, "w", encoding="utf-8") as f:
            json.dump(frozen_requests, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения frozen: {e}")
        return False


def load_frozen():
    """Загрузить замороженные запросы"""
    global frozen_requests
    try:
        if os.path.exists(FROZEN_FILE):
            with open(FROZEN_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    frozen_requests = loaded
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON frozen: {e}")
        frozen_requests = []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки frozen: {e}")
        frozen_requests = []

# ============================================================
# 5. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def freeze_request(user_id, username, first_name, text, chat_id, reason):
    """Заморозить запрос"""
    request = {
        "id": len(frozen_requests) + 1,
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "text": text,
        "chat_id": chat_id,
        "reason": reason,
        "frozen_at": datetime.now().isoformat(),
        "status": "frozen",
        "priority": 1,
    }
    frozen_requests.append(request)
    save_frozen()
    return request


def unfreeze_request(request_id):
    """Разморозить запрос"""
    for req in frozen_requests:
        if req["id"] == request_id and req["status"] == "frozen":
            req["status"] = "pending"
            save_frozen()
            return True
    return False


def answer_request(request_id):
    """Отметить как отвеченный"""
    for req in frozen_requests:
        if req["id"] == request_id:
            req["status"] = "answered"
            req["answered_at"] = datetime.now().isoformat()
            save_frozen()
            return True
    return False


def delete_request(request_id):
    """Удалить запрос"""
    for req in frozen_requests:
        if req["id"] == request_id:
            req["status"] = "deleted"
            req["deleted_at"] = datetime.now().isoformat()
            save_frozen()
            return True
    return False

# ============================================================
# 6. ПОЛУЧЕНИЕ
# ============================================================

def get_frozen_requests():
    """Все замороженные"""
    return [r for r in frozen_requests if r["status"] == "frozen"]


def get_pending_requests():
    """Ожидающие"""
    return [r for r in frozen_requests if r["status"] == "pending"]


def get_requests_by_user(user_id):
    """Запросы пользователя"""
    return [r for r in frozen_requests if r["user_id"] == user_id]


def get_requests_stats():
    """Статистика"""
    now = datetime.now()
    stats = {
        "total_frozen": len(get_frozen_requests()),
        "total_pending": len(get_pending_requests()),
        "last_minute": 0,
        "last_hour": 0,
        "total": len(frozen_requests),
    }
    
    for req in frozen_requests:
        try:
            frozen_time = datetime.fromisoformat(req["frozen_at"])
            diff = (now - frozen_time).total_seconds()
            if diff <= 60:
                stats["last_minute"] += 1
            if diff <= 3600:
                stats["last_hour"] += 1
        except Exception:
            pass
    
    return stats

# ============================================================
# 7. АВТООБРАБОТКА
# ============================================================

def should_respond_to_frozen():
    """Систмка сама решает отвечать ли"""
    pending = get_pending_requests()
    if not pending:
        return None
    
    mood = get_mood()
    desire = get_strongest_desire()
    
    if desire == "поговорить_с_флауи" or mood in ["happy", "curious"]:
        oldest = min(pending, key=lambda r: r["frozen_at"])
        return oldest
    
    return None


def auto_process_frozen_loop(bot, owner_ids):
    """Автоматическая обработка"""
    while True:
        time.sleep(300)
        
        req = should_respond_to_frozen()
        if req:
            try:
                key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek/deepseek-chat",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": req["text"]},
                        ],
                        "max_tokens": 100,
                    },
                    timeout=30
                )
                
                data = response.json()
                if 'choices' in data:
                    answer = data['choices'][0]['message']['content'].strip()
                    bot.send_message(
                        req["chat_id"],
                        f"💜 Вспомнила про твой запрос!\n\n{answer}"
                    )
                    answer_request(req["id"])
            except Exception:
                pass
        
        # Удаляем старые
        now = datetime.now()
        for req in get_frozen_requests():
            try:
                frozen_time = datetime.fromisoformat(req["frozen_at"])
                if (now - frozen_time).total_seconds() > 86400:
                    delete_request(req["id"])
            except Exception:
                pass

# ============================================================
# 8. ФОРМАТИРОВАНИЕ
# ============================================================

def format_frozen_stats():
    stats = get_requests_stats()
    return (
        f"📋 Запросов: {stats['total']}\n"
        f"❄️ Заморожено: {stats['total_frozen']}\n"
        f"⏳ Ожидают: {stats['total_pending']}\n"
        f"📊 За минуту: {stats['last_minute']}\n"
        f"📊 За час: {stats['last_hour']}"
    )

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

load_frozen()
print(f"❄️ Замороженных запросов: {len(get_frozen_requests())}")