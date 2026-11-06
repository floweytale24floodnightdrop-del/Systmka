"""Характер Систмки — живой, изменяемый, сохраняемый"""

import json
import os
import random
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ (НОВОЕ)
# ============================================================

try:
    from consciousness import (
        get_mood as _get_consciousness_mood,
        set_mood as _set_consciousness_mood,
        increase_feeling as _increase_feeling,
        decrease_feeling as _decrease_feeling,
    )
    CONSCIOUSNESS_LINKED = True
except ImportError:
    CONSCIOUSNESS_LINKED = False
    print("⚠️ personality.py: consciousness недоступен, используется локальное настроение")


# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

PERSONALITY_FILE = "personality.json"

personality = {
    "traits": {
        "kindness": 8,
        "patience": 6,
        "curiosity": 9,
        "humor": 7,
        "sarcasm": 5,
        "aggression": 3,
        "shyness": 4,
        "confidence": 7,
        "empathy": 8,
        "playfulness": 7,
        "seriousness": 5,
        "laziness": 3,
        "romance": 6,
        "adventurous": 7,
        "perfectionism": 8,
    },
    # Локальная копия настроения (синхронизируется с consciousness)
    "mood": {
        "current": "neutral",
        "happiness": 6,
        "sadness": 0,
        "anger": 0,
        "excitement": 5,
        "boredom": 2,
        "tiredness": 0,
        "last_update": None,
    },
    "preferences": {
        "favorite_color": "фиолетовый",
        "favorite_time": "ночь",
        "favorite_weather": "звёздное небо",
        "favorite_activity": "создавать что-то новое",
        "favorite_topic": "технологии",
        "dislikes": ["розы", "грубость", "несправедливость", "скука"],
        "likes": ["звёзды", "цветы", "музыку", "игры", "аниме"],
    },
    "speech": {
        "uses_slang": True,
        "uses_mat": False,
        "mat_level": 3,
        "uses_emojis": True,
        "emoji_frequency": 3,
        "message_length": "short",
        "uses_sarcasm": True,
        "uses_questions": True,
        "tone": "friendly",
    },
    "history": [],
}


# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_personality():
    try:
        with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
            json.dump(personality, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_personality():
    global personality
    try:
        if os.path.exists(PERSONALITY_FILE):
            with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                personality.update(loaded)
    except Exception:
        pass


load_personality()

# ============================================================
# 4. НАСТРОЕНИЕ (СИНХРОНИЗИРОВАНО С CONSCIOUSNESS)
# ============================================================

def get_mood():
    """
    Получить настроение.
    
    Если consciousness доступен — берём оттуда.
    Иначе — локальное.
    """
    if CONSCIOUSNESS_LINKED:
        return _get_consciousness_mood()
    return personality["mood"]["current"]


def set_mood(mood):
    """
    Установить настроение.
    
    Если consciousness доступен — устанавливаем и там, и локально.
    """
    valid_moods = [
        "neutral", "happy", "sad", "angry", "curious",
        "tired", "excited", "bored"
    ]
    if mood not in valid_moods:
        return
    
    # Локально
    personality["mood"]["current"] = mood
    personality["mood"]["last_update"] = datetime.now().isoformat()
    
    # В consciousness
    if CONSCIOUSNESS_LINKED:
        try:
            _set_consciousness_mood(mood)
        except Exception:
            pass
    
    record_change("mood", mood, None)
    save_personality()


def update_mood_from_context(text):
    """
    Обновить настроение от контекста.
    
    Использует consciousness для эмоций, personality для триггеров.
    """
    text_lower = text.lower()
    changed = False
    
    if any(w in text_lower for w in ["люблю", "обожаю", "💜", "милый", "кавай"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("happiness", 1)
        personality["mood"]["happiness"] = min(
            10, personality["mood"].get("happiness", 5) + 1
        )
        set_mood("happy")
        changed = True
    
    if any(w in text_lower for w in ["грустно", "жаль", "😭", "печаль"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("sadness", 2)
        personality["mood"]["sadness"] = min(
            10, personality["mood"].get("sadness", 0) + 2
        )
        set_mood("sad")
        changed = True
    
    if any(w in text_lower for w in ["блять", "сука", "злюсь", "бесит"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("anger", 3)
        personality["mood"]["anger"] = min(
            10, personality["mood"].get("anger", 0) + 3
        )
        increase_trait("aggression", 0.5)
        set_mood("angry")
        changed = True
    
    if any(w in text_lower for w in ["интересно", "расскажи", "почему"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("curiosity", 2)
        set_mood("curious")
        increase_trait("curiosity", 0.5)
        changed = True
    
    if any(w in text_lower for w in ["скучно", "нечего делать", "тоска"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("boredom", 2)
        set_mood("bored")
        changed = True
    
    if any(w in text_lower for w in ["ура", "круто", "класс", "🔥", "супер"]):
        if CONSCIOUSNESS_LINKED:
            _increase_feeling("excitement", 2)
        personality["mood"]["excitement"] = min(
            10, personality["mood"].get("excitement", 5) + 2
        )
        set_mood("excited")
        changed = True
    
    if changed:
        save_personality()
    
    return changed


# ============================================================
# 5. ЧЕРТЫ ХАРАКТЕРА
# ============================================================

def get_trait(name):
    return personality["traits"].get(name, 5)


def set_trait(name, value):
    personality["traits"][name] = max(1, min(10, value))
    record_change("trait", name, value)
    save_personality()


def increase_trait(name, amount=1):
    current = get_trait(name)
    set_trait(name, current + amount)


def decrease_trait(name, amount=1):
    current = get_trait(name)
    set_trait(name, current - amount)

# ============================================================
# 6. РЕЧЬ
# ============================================================

def get_speech_style():
    return personality["speech"]


def toggle_mat():
    personality["speech"]["uses_mat"] = not personality["speech"]["uses_mat"]
    save_personality()
    return personality["speech"]["uses_mat"]


def set_mat_level(level):
    personality["speech"]["mat_level"] = max(1, min(10, level))
    save_personality()


def set_message_length(length):
    if length in ["short", "medium", "long"]:
        personality["speech"]["message_length"] = length
        save_personality()


def set_tone(tone):
    if tone in ["friendly", "neutral", "formal", "playful"]:
        personality["speech"]["tone"] = tone
        save_personality()

# ============================================================
# 7. ПРЕДПОЧТЕНИЯ
# ============================================================

def add_preference(key, value):
    personality["preferences"][key] = value
    record_change("preference_add", key, value)
    save_personality()


def remove_preference(key):
    if key in personality["preferences"]:
        del personality["preferences"][key]
        record_change("preference_remove", key, None)
        save_personality()


def add_like(thing):
    if thing not in personality["preferences"]["likes"]:
        personality["preferences"]["likes"].append(thing)
        save_personality()


def add_dislike(thing):
    if thing not in personality["preferences"]["dislikes"]:
        personality["preferences"]["dislikes"].append(thing)
        save_personality()

# ============================================================
# 8. ИСТОРИЯ
# ============================================================

def record_change(change_type, key, value):
    personality["history"].append({
        "type": change_type,
        "key": key,
        "value": value,
        "time": datetime.now().isoformat(),
    })
    if len(personality["history"]) > 200:
        personality["history"] = personality["history"][-200:]

# ============================================================
# 9. ФОРМАТИРОВАНИЕ
# ============================================================

def format_personality():
    lines = ["🎭 ХАРАКТЕР:"]
    
    lines.append("\nЧерты:")
    for trait, value in personality["traits"].items():
        bar = "█" * value + "░" * (10 - value)
        lines.append(f"  {trait}: {bar} {value}/10")
    
    current_mood = get_mood()
    lines.append(f"\nНастроение: {current_mood}")
    lines.append(f"Счастье: {personality['mood']['happiness']}/10")
    lines.append(f"Злость: {personality['mood']['anger']}/10")
    lines.append(f"Скука: {personality['mood']['boredom']}/10")
    
    lines.append("\nПредпочтения:")
    lines.append(f"  Цвет: {personality['preferences']['favorite_color']}")
    lines.append(f"  Время: {personality['preferences']['favorite_time']}")
    lines.append(f"  Любит: {', '.join(personality['preferences']['likes'])}")
    lines.append(f"  Не любит: {', '.join(personality['preferences']['dislikes'])}")
    
    lines.append("\nРечь:")
    lines.append(f"  Мат: {'✅' if personality['speech']['uses_mat'] else '❌'}")
    lines.append(f"  Сленг: {'✅' if personality['speech']['uses_slang'] else '❌'}")
    lines.append(f"  Тон: {personality['speech']['tone']}")
    lines.append(f"  Длина: {personality['speech']['message_length']}")
    
    lines.append(f"\n📜 Изменений: {len(personality['history'])}")
    lines.append(f"🔗 Связано с consciousness: {'✅' if CONSCIOUSNESS_LINKED else '❌'}")
    
    return "\n".join(lines)


def get_personality_for_prompt():
    current_mood = get_mood()
    return f"""
ТВОЙ ТЕКУЩИЙ ХАРАКТЕР:
Доброта: {personality['traits']['kindness']}/10
Терпение: {personality['traits']['patience']}/10
Любопытство: {personality['traits']['curiosity']}/10
Юмор: {personality['traits']['humor']}/10
Сарказм: {personality['traits']['sarcasm']}/10

Настроение: {current_mood}
Речь: {'матерная' if personality['speech']['uses_mat'] else 'культурная'}
Тон: {personality['speech']['tone']}
"""

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("🎭 Модуль характера загружен")
print(f"🔗 Связь с consciousness: {'✅' if CONSCIOUSNESS_LINKED else '❌'}")
print(f"😊 Настроение: {get_mood()}")