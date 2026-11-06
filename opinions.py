"""Мнения Систмки о людях — живые, эмоциональные, изменяемые, с историей"""

import json
import os
import random
import re
import requests
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

OPINIONS_FILE = "opinions.json"
MAX_OPINION_HISTORY = 50

opinions = {
    "people": {},  # {user_id: {"name": str, "current_feeling": str, "rating": int, "tags": [], "history": [], "first_impression": str, "last_interaction": str}}
    "statistics": {
        "total_people": 0,
        "liked": 0,
        "disliked": 0,
        "neutral": 0,
        "changed_minds": 0,  # Сколько раз менялось мнение
    },
    "last_update": None,
}

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_opinions():
    try:
        with open(OPINIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(opinions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения мнений: {e}")
        return False

def load_opinions():
    global opinions
    try:
        if os.path.exists(OPINIONS_FILE):
            with open(OPINIONS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                opinions.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки мнений: {e}")
        return False

load_opinions()

# ============================================================
# 3. СОЗДАНИЕ МНЕНИЯ
# ============================================================

def create_opinion(user_id, name, first_interaction=None):
    """Создать первое мнение о человеке"""
    
    user_id_str = str(user_id)
    
    if user_id_str in opinions["people"]:
        return opinions["people"][user_id_str]
    
    first_impression = generate_first_impression(name, first_interaction)
    
    opinion = {
        "name": name,
        "user_id": user_id,
        "first_impression": first_impression,
        "current_feeling": "neutral",
        "rating": 5,
        "tags": [],
        "history": [
            {
                "date": datetime.now().isoformat(),
                "event": "Первое знакомство",
                "feeling": "neutral",
                "note": first_impression,
                "rating": 5
            }
        ],
        "interactions": 0,
        "last_interaction": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "opinion_changes": 0,
    }
    
    opinions["people"][user_id_str] = opinion
    opinions["statistics"]["total_people"] += 1
    opinions["statistics"]["neutral"] += 1
    opinions["last_update"] = datetime.now().isoformat()
    
    save_opinions()
    
    return opinion

def generate_first_impression(name, interaction=None):
    """Сгенерировать первое впечатление через ИИ"""
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        context = f"Первое общение с {name}."
        if interaction:
            context += f" Он/она сказал(а): {interaction[:100]}"
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Напиши своё первое впечатление о человеке.
1-2 предложения.
Будь честной, но не грубой.
Пиши как живой человек.
НЕ ПИШИ что ты ИИ."""},
                    {"role": "user", "content": f"{context}\n\nМоё первое впечатление:"}
                ],
                "max_tokens": 100,
                "temperature": 0.9
            },
            timeout=20
        )
        data = response.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка генерации первого впечатления: {e}")
    
    # Fallback
    impressions = [
        f"{name} кажется интересным человеком",
        f"С {name} приятно общаться",
        f"{name} вызывает у меня любопытство",
        f"Я пока не знаю что думать о {name}",
        f"{name} выглядит дружелюбно",
        f"Что-то в {name} есть особенное",
    ]
    return random.choice(impressions)

# ============================================================
# 4. ОБНОВЛЕНИЕ МНЕНИЯ
# ============================================================

def update_opinion(user_id, interaction_text, feeling=None, rating=None):
    """Обновить мнение после общения"""
    
    user_id_str = str(user_id)
    if user_id_str not in opinions["people"]:
        return create_opinion(user_id, "Пользователь", interaction_text)
    
    opinion = opinions["people"][user_id_str]
    old_feeling = opinion.get("current_feeling", "neutral")
    old_rating = opinion.get("rating", 5)
    
    # Анализируем взаимодействие
    analysis = analyze_interaction(interaction_text, opinion)
    
    if feeling:
        opinion["current_feeling"] = feeling
    elif analysis.get("feeling"):
        opinion["current_feeling"] = analysis["feeling"]
    
    if rating:
        opinion["rating"] = rating
    elif analysis.get("rating"):
        new_rating = analysis["rating"]
        opinion["rating"] = old_rating + (new_rating - old_rating) * 0.3
    
    # Проверяем, изменилось ли мнение
    if opinion["current_feeling"] != old_feeling or abs(opinion["rating"] - old_rating) > 1:
        opinions["statistics"]["changed_minds"] += 1
        opinion["opinion_changes"] = opinion.get("opinion_changes", 0) + 1
    
    # Добавляем в историю
    opinion["history"].append({
        "date": datetime.now().isoformat(),
        "event": interaction_text[:100],
        "feeling": opinion["current_feeling"],
        "note": analysis.get("note", ""),
        "rating": opinion["rating"],
    })
    
    if len(opinion["history"]) > MAX_OPINION_HISTORY:
        opinion["history"] = opinion["history"][-MAX_OPINION_HISTORY:]
    
    opinion["interactions"] += 1
    opinion["last_interaction"] = datetime.now().isoformat()
    
    # Обновляем теги
    if analysis.get("tags"):
        for tag in analysis["tags"]:
            if tag not in opinion["tags"]:
                opinion["tags"].append(tag)
    
    # Обновляем статистику
    update_statistics(opinion, old_feeling)
    
    opinions["last_update"] = datetime.now().isoformat()
    save_opinions()
    
    return opinion

def analyze_interaction(text, current_opinion):
    """Проанализировать взаимодействие через ИИ"""
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Проанализируй взаимодействие с человеком.

ОТВЕТЬ В ФОРМАТЕ:
НАСТРОЕНИЕ: (positive/negative/neutral)
ОЦЕНКА: (1-10)
ЗАМЕТКА: (1 предложение что ты чувствуешь)
ТЕГИ: (теги через запятую)"""},
                    {"role": "user", "content": f"Человек: {current_opinion['name']}\nМоё текущее мнение: {current_opinion['first_impression']}\nВзаимодействие: {text}\n\nПроанализируй:"}
                ],
                "max_tokens": 200,
                "temperature": 0.8
            },
            timeout=20
        )
        data = response.json()
        if 'choices' in data:
            result = data['choices'][0]['message']['content']
            
            feeling_match = re.search(r'НАСТРОЕНИЕ:\s*(.+)', result, re.IGNORECASE)
            rating_match = re.search(r'ОЦЕНКА:\s*(\d+)', result, re.IGNORECASE)
            note_match = re.search(r'ЗАМЕТКА:\s*(.+)', result, re.IGNORECASE)
            tags_match = re.search(r'ТЕГИ:\s*(.+)', result, re.IGNORECASE)
            
            return {
                "feeling": feeling_match.group(1).strip().lower() if feeling_match else "neutral",
                "rating": int(rating_match.group(1)) if rating_match else 5,
                "note": note_match.group(1).strip() if note_match else "",
                "tags": [t.strip() for t in tags_match.group(1).split(',')] if tags_match else [],
            }
    except Exception as e:
        print(f"⚠️ Ошибка анализа взаимодействия: {e}")
    
    return {
        "feeling": "neutral",
        "rating": 5,
        "note": "Обычное общение",
        "tags": []
    }

def update_statistics(opinion, old_feeling):
    """Обновить глобальную статистику"""
    rating = opinion.get("rating", 5)
    feeling = opinion.get("current_feeling", "neutral")
    
    # Убираем из старой статистики
    if old_feeling == "positive" or rating >= 7:
        opinions["statistics"]["liked"] = max(0, opinions["statistics"]["liked"] - 1)
    elif old_feeling == "negative" or rating <= 3:
        opinions["statistics"]["disliked"] = max(0, opinions["statistics"]["disliked"] - 1)
    else:
        opinions["statistics"]["neutral"] = max(0, opinions["statistics"]["neutral"] - 1)
    
    # Добавляем в новую
    if feeling == "positive" or rating >= 7:
        opinions["statistics"]["liked"] += 1
    elif feeling == "negative" or rating <= 3:
        opinions["statistics"]["disliked"] += 1
    else:
        opinions["statistics"]["neutral"] += 1

# ============================================================
# 5. ПОЛУЧЕНИЕ ИНФОРМАЦИИ
# ============================================================

def get_opinion(user_id):
    user_id_str = str(user_id)
    return opinions["people"].get(user_id_str)

def get_all_opinions():
    return opinions["people"]

def get_opinion_summary(user_id):
    opinion = get_opinion(user_id)
    if not opinion:
        return None
    
    return {
        "name": opinion["name"],
        "rating": opinion["rating"],
        "feeling": opinion["current_feeling"],
        "first_impression": opinion["first_impression"],
        "interactions": opinion["interactions"],
        "tags": opinion["tags"],
        "changes": opinion.get("opinion_changes", 0),
    }

def get_people_by_feeling(feeling):
    """Получить людей с определённым настроением"""
    return {
        uid: data for uid, data in opinions["people"].items()
        if data.get("current_feeling") == feeling
    }

def get_top_rated(limit=10):
    """Получить людей с самым высоким рейтингом"""
    sorted_people = sorted(
        opinions["people"].items(),
        key=lambda x: x[1].get("rating", 0),
        reverse=True
    )
    return sorted_people[:limit]

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_opinion(user_id):
    opinion = get_opinion(user_id)
    if not opinion:
        return "❌ Нет мнения об этом человеке"
    
    lines = [
        f"👤 {opinion['name']}",
        f"⭐ Оценка: {opinion['rating']}/10",
        f"💭 Настроение: {opinion['current_feeling']}",
        f"📝 Первое впечатление: {opinion['first_impression']}",
        f"💬 Взаимодействий: {opinion['interactions']}",
        f"🔄 Изменений мнения: {opinion.get('opinion_changes', 0)}",
        f"🏷 Теги: {', '.join(opinion['tags']) if opinion['tags'] else 'нет'}",
    ]
    
    if opinion['history']:
        last = opinion['history'][-1]
        lines.append(f"🕐 Последнее: {last['note'][:50]}...")
        lines.append(f"   ({last['date'][:16]})")
    
    return "\n".join(lines)

def format_all_opinions():
    all_opinions = get_all_opinions()
    
    if not all_opinions:
        return "😐 Пока нет мнений о людях"
    
    # Сортируем по рейтингу
    sorted_people = sorted(
        all_opinions.items(),
        key=lambda x: x[1].get("rating", 0),
        reverse=True
    )
    
    lines = ["👥 МОИ МНЕНИЯ О ЛЮДЯХ:"]
    lines.append("")
    
    for user_id, opinion in sorted_people[:20]:
        rating = opinion.get("rating", 5)
        feeling = opinion.get("current_feeling", "neutral")
        
        if rating >= 7:
            icon = "❤️"
        elif rating <= 3:
            icon = "💔"
        else:
            icon = "😐"
        
        lines.append(f"{icon} {opinion['name']} — {rating}/10 ({feeling})")
    
    # Статистика
    stats = opinions["statistics"]
    lines.append("")
    lines.append(f"📊 Всего: {stats['total_people']} | ❤️ {stats['liked']} | 💔 {stats['disliked']} | 😐 {stats['neutral']}")
    lines.append(f"🔄 Изменений мнения: {stats['changed_minds']}")
    
    return "\n".join(lines)

def format_opinion_stats():
    stats = opinions["statistics"]
    lines = [
        "📊 СТАТИСТИКА МНЕНИЙ:",
        f"👥 Всего людей: {stats['total_people']}",
        f"❤️ Нравятся: {stats['liked']}",
        f"💔 Не нравятся: {stats['disliked']}",
        f"😐 Нейтральные: {stats['neutral']}",
        f"🔄 Изменений мнения: {stats['changed_minds']}",
    ]
    if opinions.get('last_update'):
        lines.append(f"🕐 Обновлено: {opinions['last_update'][:16]}")
    return "\n".join(lines)

print("💜 Модуль мнений загружен")
print(f"👥 Всего мнений: {len(opinions['people'])}")
print(f"❤️ Нравятся: {opinions['statistics']['liked']}")
print(f"💔 Не нравятся: {opinions['statistics']['disliked']}")