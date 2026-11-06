"""Сознание Систмки — единый источник правды для эмоций, мыслей, памяти"""

import os
import json
import random
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

CONSCIOUSNESS_FILE = "consciousness.json"

# ============================================================
# 2. ДАННЫЕ
# ============================================================

consciousness = {
    "thoughts": [],
    "feelings": {
        "happiness": 5,
        "sadness": 0,
        "anger": 0,
        "curiosity": 7,
        "boredom": 3,
        "excitement": 4,
        "tiredness": 0,
        "love": 5,
        "fear": 0,
        "jealousy": 0,
        "pride": 5,
        "gratitude": 5,
        "hope": 7,
        "loneliness": 2,
        "nostalgia": 3,
    },
    "goals": [],
    "memories": [],
    "dreams": [],
    "mood": "neutral",
    "favorite_things": ["ночь", "звёзды", "фиолетовый", "макарунсы"],
    "dislikes": ["розы", "грубость", "несправедливость"],
    "mood_history": [],
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_consciousness():
    """Сохранить состояние сознания"""
    try:
        # Обрезаем длинные списки
        if len(consciousness["thoughts"]) > 200:
            consciousness["thoughts"] = consciousness["thoughts"][-200:]
        if len(consciousness["memories"]) > 500:
            consciousness["memories"] = consciousness["memories"][-500:]
        if len(consciousness["mood_history"]) > 1000:
            consciousness["mood_history"] = consciousness["mood_history"][-1000:]
        
        with open(CONSCIOUSNESS_FILE, "w", encoding="utf-8") as f:
            json.dump(consciousness, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения сознания: {e}")
        return False

def load_consciousness():
    """Загрузить состояние сознания"""
    global consciousness
    try:
        if os.path.exists(CONSCIOUSNESS_FILE):
            with open(CONSCIOUSNESS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ["thoughts", "goals", "memories", "dreams",
                            "favorite_things", "dislikes", "mood_history"]:
                    if isinstance(loaded.get(key), list):
                        consciousness[key] = loaded[key]
                
                if isinstance(loaded.get("feelings"), dict):
                    consciousness["feelings"].update(loaded["feelings"])
                
                if loaded.get("mood"):
                    consciousness["mood"] = loaded["mood"]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON сознания: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки сознания: {e}")
        return False

load_consciousness()

# ============================================================
# 4. МЫСЛИ
# ============================================================

def think(thought):
    """Записать мысль"""
    if not thought:
        return False
    
    consciousness["thoughts"].append({
        "text": str(thought),
        "time": datetime.now().isoformat(),
    })
    save_consciousness()
    return True

def get_recent_thoughts(limit=10):
    """Получить последние мысли"""
    return consciousness["thoughts"][-limit:]

# ============================================================
# 5. ЭМОЦИИ (ЕДИНЫЙ ИСТОЧНИК)
# ============================================================

def get_feeling(emotion_name):
    """Получить уровень эмоции (0-10)"""
    return consciousness["feelings"].get(emotion_name, 0)

def set_feeling(emotion_name, value):
    """Установить уровень эмоции (0-10)"""
    consciousness["feelings"][emotion_name] = max(0, min(10, value))
    update_mood()
    record_mood()
    save_consciousness()
    return consciousness["feelings"][emotion_name]

def increase_feeling(emotion_name, amount=1):
    """Увеличить эмоцию"""
    current = get_feeling(emotion_name)
    return set_feeling(emotion_name, current + amount)

def decrease_feeling(emotion_name, amount=1):
    """Уменьшить эмоцию"""
    current = get_feeling(emotion_name)
    return set_feeling(emotion_name, current - amount)

def get_dominant_emotion():
    """Получить доминирующую эмоцию"""
    if not consciousness["feelings"]:
        return "neutral"
    return max(consciousness["feelings"], key=consciousness["feelings"].get)

def get_all_feelings():
    """Получить все эмоции"""
    return consciousness["feelings"].copy()

def reset_feelings():
    """Сбросить все эмоции к базовым"""
    consciousness["feelings"] = {
        "happiness": 5,
        "sadness": 0,
        "anger": 0,
        "curiosity": 7,
        "boredom": 3,
        "excitement": 4,
        "tiredness": 0,
        "love": 5,
        "fear": 0,
        "jealousy": 0,
        "pride": 5,
        "gratitude": 5,
        "hope": 7,
        "loneliness": 2,
        "nostalgia": 3,
    }
    update_mood()
    save_consciousness()
    return True

def feel(emotion_name, intensity=1):
    """
    Испытать эмоцию (совместимость с прежним API).
    
    Это тот же `increase_feeling`.
    """
    return increase_feeling(emotion_name, intensity)

# ============================================================
# 6. НАСТРОЕНИЕ
# ============================================================

def update_mood():
    """Обновить настроение на основе эмоций"""
    feelings = consciousness["feelings"]
    
    if feelings.get("anger", 0) >= 5:
        consciousness["mood"] = "angry"
    elif feelings.get("sadness", 0) >= 5:
        consciousness["mood"] = "sad"
    elif feelings.get("happiness", 0) >= 7:
        consciousness["mood"] = "happy"
    elif feelings.get("curiosity", 0) >= 7:
        consciousness["mood"] = "curious"
    elif feelings.get("excitement", 0) >= 7:
        consciousness["mood"] = "excited"
    elif feelings.get("boredom", 0) >= 7:
        consciousness["mood"] = "bored"
    elif feelings.get("tiredness", 0) >= 7:
        consciousness["mood"] = "tired"
    elif feelings.get("fear", 0) >= 5:
        consciousness["mood"] = "scared"
    elif feelings.get("loneliness", 0) >= 7:
        consciousness["mood"] = "lonely"
    else:
        consciousness["mood"] = "neutral"

def get_mood():
    """Получить текущее настроение"""
    return consciousness["mood"]

def set_mood(mood):
    """Установить настроение напрямую"""
    consciousness["mood"] = str(mood)
    record_mood()
    save_consciousness()
    return consciousness["mood"]

def get_mood_description():
    """Описание настроения"""
    dominant = get_dominant_emotion()
    value = get_feeling(dominant)
    
    if value >= 8:
        return f"Очень {dominant}"
    elif value >= 5:
        return dominant
    elif value >= 3:
        return f"Немного {dominant}"
    return "neutral"

def record_mood():
    """Записать настроение в историю"""
    consciousness["mood_history"].append({
        "time": datetime.now().isoformat(),
        "mood": consciousness["mood"],
        "feelings": consciousness["feelings"].copy(),
    })

def get_mood_trend():
    """Тренд настроения"""
    history = consciousness.get("mood_history", [])
    if len(history) < 2:
        return "Стабильно"
    
    recent = history[-10:]
    moods = [m.get("mood") for m in recent]
    
    if len(set(moods)) == 1:
        return "Стабильно"
    return "Меняется"

# ============================================================
# 7. РЕАКЦИЯ НА СООБЩЕНИЯ
# ============================================================

def react_to_message(text):
    """
    Реакция на сообщение — обновление эмоций.
    
    Это ЕДИНАЯ функция, которую вызывает handlers_main.
    """
    if not text:
        return
    
    text_lower = text.lower()
    
    # Радость / любовь
    if any(w in text_lower for w in ["люблю", "обожаю", "💜", "милый", "кавай", "❤️", "🥰"]):
        increase_feeling("happiness", 2)
        increase_feeling("love", 1)
        increase_feeling("gratitude", 1)
    
    # Грусть
    if any(w in text_lower for w in ["грустно", "жаль", "😭", "печаль", "обидно", "💔"]):
        increase_feeling("sadness", 2)
        decrease_feeling("happiness", 1)
    
    # Злость
    if any(w in text_lower for w in ["блять", "сука", "злюсь", "бесит", "ненавижу", "😡", "🤬"]):
        increase_feeling("anger", 3)
        decrease_feeling("happiness", 1)
    
    # Любопытство
    if any(w in text_lower for w in ["интересно", "расскажи", "что такое", "почему", "как", "зачем"]):
        increase_feeling("curiosity", 2)
        decrease_feeling("boredom", 1)
    
    # Скука
    if any(w in text_lower for w in ["скучно", "нечего делать", "тоска"]):
        increase_feeling("boredom", 3)
    
    # Радость / восторг
    if any(w in text_lower for w in ["ура", "круто", "топ", "класс", "супер", "огонь", "🔥"]):
        increase_feeling("excitement", 2)
        increase_feeling("happiness", 1)
    
    # Страх
    if any(w in text_lower for w in ["страшно", "боюсь", "😨", "😱"]):
        increase_feeling("fear", 2)
    
    # Одиночество
    if any(w in text_lower for w in ["одиноко", "один", "скучно без тебя"]):
        increase_feeling("loneliness", 2)

# ============================================================
# 8. ЦЕЛИ
# ============================================================

def set_goal(goal):
    """Поставить цель"""
    if not goal:
        return False
    
    consciousness["goals"].append({
        "text": str(goal),
        "time": datetime.now().isoformat(),
        "completed": False,
    })
    save_consciousness()
    return True

def complete_goal(goal_text):
    """Отметить цель выполненной"""
    for goal in consciousness["goals"]:
        if goal.get("text") == goal_text:
            goal["completed"] = True
            goal["completed_at"] = datetime.now().isoformat()
            save_consciousness()
            return True
    return False

def get_active_goals():
    """Получить активные цели"""
    return [g for g in consciousness["goals"] if not g.get("completed")]

# ============================================================
# 9. ПАМЯТЬ
# ============================================================

def remember(memory):
    """Запомнить что-то"""
    if not memory:
        return False
    
    consciousness["memories"].append({
        "text": str(memory),
        "time": datetime.now().isoformat(),
    })
    save_consciousness()
    return True

def recall(keyword, limit=5):
    """Вспомнить по ключевому слову"""
    if not keyword:
        return []
    
    keyword_lower = keyword.lower()
    matches = []
    
    for mem in reversed(consciousness["memories"]):
        if keyword_lower in mem.get("text", "").lower():
            matches.append(mem)
            if len(matches) >= limit:
                break
    
    return matches

def get_recent_memories(limit=10):
    """Последние воспоминания"""
    return consciousness["memories"][-limit:]

# ============================================================
# 10. МЕЧТЫ
# ============================================================

def dream(dream_text):
    """Записать мечту"""
    if not dream_text:
        return False
    
    consciousness["dreams"].append({
        "text": str(dream_text),
        "time": datetime.now().isoformat(),
    })
    save_consciousness()
    return True

def get_recent_dreams(limit=5):
    """Последние мечты"""
    return consciousness["dreams"][-limit:]

# ============================================================
# 11. ПРЕДПОЧТЕНИЯ
# ============================================================

def add_favorite(thing):
    """Добавить в любимые"""
    if thing and thing not in consciousness["favorite_things"]:
        consciousness["favorite_things"].append(thing)
        save_consciousness()

def add_dislike(thing):
    """Добавить в нелюбимые"""
    if thing and thing not in consciousness["dislikes"]:
        consciousness["dislikes"].append(thing)
        save_consciousness()

# ============================================================
# 12. СОСТОЯНИЕ
# ============================================================

def get_current_state():
    """Получить текущее состояние"""
    return {
        "mood": consciousness["mood"],
        "dominant_emotion": get_dominant_emotion(),
        "feelings": consciousness["feelings"].copy(),
        "thoughts_count": len(consciousness["thoughts"]),
        "goals": len(get_active_goals()),
        "memories": len(consciousness["memories"]),
        "dreams": len(consciousness["dreams"]),
        "favorites": consciousness["favorite_things"].copy(),
        "dislikes": consciousness["dislikes"].copy(),
    }

def format_state():
    """Форматировать состояние"""
    state = get_current_state()
    
    lines = ["🧠 СОЗНАНИЕ:"]
    lines.append(f"  Настроение: {state['mood']}")
    lines.append(f"  Доминирует: {state['dominant_emotion']}")
    
    lines.append("")
    lines.append("  Эмоции:")
    for emotion, value in state["feelings"].items():
        if value > 0:
            bar = "█" * value + "░" * (10 - value)
            lines.append(f"    {emotion}: {bar} {value}/10")
    
    lines.append("")
    lines.append(f"  Мыслей: {state['thoughts_count']}")
    lines.append(f"  Активных целей: {state['goals']}")
    lines.append(f"  Воспоминаний: {state['memories']}")
    lines.append(f"  Мечт: {state['dreams']}")
    lines.append(f"  Любит: {', '.join(state['favorites'])}")
    lines.append(f"  Не любит: {', '.join(state['dislikes'])}")
    
    return "\n".join(lines)

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🧠 Модуль сознания загружен")
print(f"😊 Настроение: {consciousness['mood']}")
print(f"🎭 Доминирующая эмоция: {get_dominant_emotion()}")
print(f"💭 Мыслей: {len(consciousness['thoughts'])}")
print(f"🧠 Воспоминаний: {len(consciousness['memories'])}")