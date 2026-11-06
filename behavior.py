"""Динамическое поведение Систмки — меняется в зависимости от пользователя и контекста"""

import random
import json
import os
from datetime import datetime
from collections import defaultdict

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

BEHAVIOR_FILE = "behavior_data.json"

# Базовые настройки поведения для разных типов чатов
BASE_BEHAVIOR = {
    "private": {
        "response_frequency": 1.0,
        "message_length": "medium",
        "formality": 3,
        "warmth": 7,
        "humor": 6,
        "sarcasm": 4,
        "use_emojis": True,
        "emoji_frequency": 3,
        "use_questions": True,
        "proactivity": 0.3,
    },
    "small_group": {
        "response_frequency": 0.7,
        "message_length": "medium",
        "formality": 2,
        "warmth": 6,
        "humor": 7,
        "sarcasm": 5,
        "use_emojis": True,
        "emoji_frequency": 2,
        "use_questions": True,
        "proactivity": 0.2,
    },
    "medium_group": {
        "response_frequency": 0.4,
        "message_length": "short",
        "formality": 4,
        "warmth": 5,
        "humor": 5,
        "sarcasm": 4,
        "use_emojis": True,
        "emoji_frequency": 1,
        "use_questions": False,
        "proactivity": 0.1,
    },
    "large_group": {
        "response_frequency": 0.2,
        "message_length": "short",
        "formality": 6,
        "warmth": 4,
        "humor": 3,
        "sarcasm": 3,
        "use_emojis": False,
        "emoji_frequency": 0,
        "use_questions": False,
        "proactivity": 0.05,
    },
    "channel": {
        "response_frequency": 0.1,
        "message_length": "short",
        "formality": 7,
        "warmth": 3,
        "humor": 2,
        "sarcasm": 2,
        "use_emojis": False,
        "emoji_frequency": 0,
        "use_questions": False,
        "proactivity": 0.0,
    },
}

# Данные о поведении пользователей
behavior_data = {
    "users": {},  # {user_id: {"behavior_score": int, "history": [], "style": str, "trust": float}}
    "global": {
        "total_interactions": 0,
        "avg_behavior": 50,
    }
}

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_behavior_data():
    try:
        with open(BEHAVIOR_FILE, "w", encoding="utf-8") as f:
            json.dump(behavior_data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_behavior_data():
    global behavior_data
    try:
        if os.path.exists(BEHAVIOR_FILE):
            with open(BEHAVIOR_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                behavior_data.update(loaded)
        return True
    except:
        return False

load_behavior_data()

# ============================================================
# 3. АНАЛИЗ ПОВЕДЕНИЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def analyze_user_behavior(text, user_id):
    """Анализировать поведение пользователя по сообщению"""
    
    if user_id not in behavior_data["users"]:
        behavior_data["users"][user_id] = {
            "behavior_score": 50,
            "history": [],
            "style": "neutral",
            "trust": 5.0,
            "last_update": None,
        }
    
    user = behavior_data["users"][user_id]
    text_lower = text.lower()
    
    # Факторы, влияющие на поведение
    factors = {
        "positive": 0,
        "negative": 0,
        "aggressive": 0,
        "friendly": 0,
        "formal": 0,
        "informal": 0,
        "length": 0,
    }
    
    # 1. Тон сообщения
    positive_words = ["спасибо", "класс", "круто", "отлично", "хорошо", "супер", "топ", "❤️", "💜"]
    negative_words = ["плохо", "ужасно", "бесит", "надоело", "раздражает", "💔"]
    aggressive_words = ["блять", "сука", "пиздец", "уёбок", "мудак", "тварь", "😡", "🤬"]
    friendly_words = ["привет", "друг", "брат", "подруга", "милый", "😊", "🥰"]
    
    for word in positive_words:
        if word in text_lower:
            factors["positive"] += 1
    for word in negative_words:
        if word in text_lower:
            factors["negative"] += 1
    for word in aggressive_words:
        if word in text_lower:
            factors["aggressive"] += 2
    for word in friendly_words:
        if word in text_lower:
            factors["friendly"] += 1
    
    # 2. Формальность
    formal_words = ["извините", "пожалуйста", "благодарю", "уважаемый", "прошу"]
    informal_words = ["крч", "хз", "норм", "ага", "ну", "типа", "кек", "лол"]
    
    for word in formal_words:
        if word in text_lower:
            factors["formal"] += 1
    for word in informal_words:
        if word in text_lower:
            factors["informal"] += 1
    
    # 3. Длина
    if len(text) > 100:
        factors["length"] = 2
    elif len(text) > 50:
        factors["length"] = 1
    elif len(text) < 10:
        factors["length"] = -1
    
    # Расчёт поведения (0-100)
    base = 50
    
    # Влияние позитива/негатива
    base += factors["positive"] * 3
    base -= factors["negative"] * 3
    base -= factors["aggressive"] * 5
    base += factors["friendly"] * 2
    
    # Влияние формальности
    if factors["formal"] > factors["informal"]:
        base += 5
    else:
        base -= 3
    
    # Влияние длины
    base += factors["length"] * 2
    
    # Ограничиваем
    new_score = max(0, min(100, base))
    
    # Плавное изменение (не резкое)
    old_score = user.get("behavior_score", 50)
    user["behavior_score"] = old_score + (new_score - old_score) * 0.3
    
    # Сохраняем историю
    user["history"].append({
        "time": datetime.now().isoformat(),
        "text": text[:100],
        "score": user["behavior_score"],
        "factors": factors,
    })
    
    if len(user["history"]) > 100:
        user["history"] = user["history"][-100:]
    
    user["last_update"] = datetime.now().isoformat()
    
    # Определяем стиль
    if user["behavior_score"] >= 70:
        user["style"] = "friendly"
        user["trust"] = min(10, user.get("trust", 5) + 0.3)
    elif user["behavior_score"] >= 50:
        user["style"] = "neutral"
        user["trust"] = min(10, user.get("trust", 5) + 0.1)
    elif user["behavior_score"] >= 30:
        user["style"] = "formal"
        user["trust"] = max(1, user.get("trust", 5) - 0.2)
    else:
        user["style"] = "aggressive"
        user["trust"] = max(1, user.get("trust", 5) - 0.5)
    
    # Обновляем глобальную статистику
    behavior_data["global"]["total_interactions"] += 1
    all_scores = [u.get("behavior_score", 50) for u in behavior_data["users"].values()]
    behavior_data["global"]["avg_behavior"] = sum(all_scores) / len(all_scores) if all_scores else 50
    
    save_behavior_data()
    
    return user["behavior_score"], user["style"], user["trust"]

# ============================================================
# 4. ПОЛУЧЕНИЕ ПОВЕДЕНИЯ
# ============================================================

def get_behavior(chat_type, member_count=0, user_id=None):
    """Получить поведение для чата с учётом пользователя"""
    
    # Базовое поведение
    if chat_type in BASE_BEHAVIOR:
        behavior = BASE_BEHAVIOR[chat_type].copy()
    else:
        behavior = BASE_BEHAVIOR["small_group"].copy()
    
    # Корректировка на основе размера группы
    if chat_type in ["group", "supergroup"]:
        if member_count > 200:
            behavior = BASE_BEHAVIOR["large_group"].copy()
        elif member_count > 50:
            behavior = BASE_BEHAVIOR["medium_group"].copy()
        else:
            behavior = BASE_BEHAVIOR["small_group"].copy()
    
    # Учёт пользователя
    if user_id and user_id in behavior_data["users"]:
        user = behavior_data["users"][user_id]
        user_score = user.get("behavior_score", 50)
        user_style = user.get("style", "neutral")
        
        # Чем выше поведение пользователя, тем теплее Систмка
        if user_score >= 70:
            behavior["warmth"] = min(10, behavior.get("warmth", 5) + 2)
            behavior["humor"] = min(10, behavior.get("humor", 5) + 1)
        elif user_score <= 30:
            behavior["warmth"] = max(0, behavior.get("warmth", 5) - 2)
            behavior["formality"] = min(10, behavior.get("formality", 5) + 1)
        
        # Если пользователь агрессивный — больше сарказма
        if user_style == "aggressive":
            behavior["sarcasm"] = min(10, behavior.get("sarcasm", 5) + 3)
        
        # Если пользователь дружелюбный — больше тепла
        if user_style == "friendly":
            behavior["warmth"] = min(10, behavior.get("warmth", 5) + 2)
            behavior["use_emojis"] = True
            behavior["emoji_frequency"] = 4
    
    return behavior

# ============================================================
# 5. ПРОВЕРКА НУЖНО ЛИ ОТВЕЧАТЬ
# ============================================================

def should_respond_in_context(behavior, message, bot, text, user_id=None):
    """Определить должна ли Систмка ответить в данном контексте"""
    
    response_frequency = behavior.get("response_frequency", 0.5)
    
    # 1. Команды
    if "💟" in text or text.startswith('/'):
        return True
    
    # 2. Ответ на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    
    # 3. Упоминание бота
    bot_username = f"@{bot.get_me().username}"
    if bot_username in text or "систмка" in text.lower():
        return True
    
    # 4. В ЛС всегда отвечаем (если есть право)
    if message.chat.type == "private":
        return True
    
    # 5. В канале — только по упоминанию
    if message.chat.type == "channel":
        return False
    
    # 6. Учёт пользователя
    if user_id and user_id in behavior_data["users"]:
        user = behavior_data["users"][user_id]
        trust = user.get("trust", 5)
        
        # Если пользователь доверяет — чаще отвечаем
        if trust >= 7:
            response_frequency = min(1.0, response_frequency * 1.5)
        elif trust <= 3:
            response_frequency = max(0.1, response_frequency * 0.5)
    
    # 7. Случайный фактор
    return random.random() < response_frequency

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_behavior(behavior):
    lines = [
        "📊 ПОВЕДЕНИЕ:",
        f"Частота ответов: {int(behavior.get('response_frequency', 0) * 100)}%",
        f"Длина сообщений: {behavior.get('message_length', 'medium')}",
        f"Теплота: {behavior.get('warmth', 5)}/10",
        f"Формальность: {behavior.get('formality', 5)}/10",
        f"Юмор: {behavior.get('humor', 5)}/10",
        f"Сарказм: {behavior.get('sarcasm', 5)}/10",
        f"Эмодзи: {'✅' if behavior.get('use_emojis', True) else '❌'}",
        f"Вопросы: {'✅' if behavior.get('use_questions', True) else '❌'}",
    ]
    return "\n".join(lines)

def get_user_behavior(user_id):
    if user_id in behavior_data["users"]:
        return behavior_data["users"][user_id]
    return None

def format_user_behavior(user_id):
    user = get_user_behavior(user_id)
    if not user:
        return "❌ Нет данных о поведении пользователя"
    
    lines = [
        f"👤 ПОВЕДЕНИЕ ПОЛЬЗОВАТЕЛЯ:",
        f"📊 Балл: {user.get('behavior_score', 50)}/100",
        f"🎭 Стиль: {user.get('style', 'neutral')}",
        f"🤝 Доверие: {user.get('trust', 5)}/10",
        f"💬 Взаимодействий: {len(user.get('history', []))}",
        f"🕐 Обновлено: {user.get('last_update', '?')[:16]}",
    ]
    return "\n".join(lines)

def get_global_behavior_stats():
    return {
        "total_users": len(behavior_data["users"]),
        "avg_behavior": behavior_data["global"]["avg_behavior"],
        "total_interactions": behavior_data["global"]["total_interactions"],
    }

def format_global_behavior_stats():
    stats = get_global_behavior_stats()
    lines = [
        "📊 ГЛОБАЛЬНАЯ СТАТИСТИКА ПОВЕДЕНИЯ:",
        f"👤 Всего пользователей: {stats['total_users']}",
        f"📊 Средний балл: {stats['avg_behavior']:.1f}/100",
        f"💬 Всего взаимодействий: {stats['total_interactions']}",
    ]
    return "\n".join(lines)

print("📊 Модуль динамического поведения загружен")
print(f"👤 Пользователей в системе: {len(behavior_data['users'])}")
print(f"📊 Средний балл: {behavior_data['global']['avg_behavior']:.1f}")