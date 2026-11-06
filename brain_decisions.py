"""
brain_decisions.py — Решения мозга о реакциях и ответах.

Заменяет should_react(), should_respond_in_context(), choose_reaction().
Систмка сама решает:
- Отвечать или нет
- Сколько сообщений
- Ставить ли реакцию
- Какую реакцию
- Убирать ли реакцию
- На чьё сообщение
"""

import time
import random
from datetime import datetime
from typing import Optional, Dict, List

from brain_core import brain


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

FAVORITE_REACTIONS = ["👾", "❤️", "🔥", "🥰", "👏", "🫶"]
SARCASTIC_REACTIONS = ["😏", "🤔", "👀", "🙄", "😐"]
SAD_REACTIONS = ["😢", "🥺", "💔"]
FUNNY_REACTIONS = ["😂", "🤣", "😁", "🤡"]
ANGRY_REACTIONS = ["😡", "🤬", "👎"]


# ============================================================
# 2. ВЫЧИСЛЕНИЕ ВАЖНОСТИ
# ============================================================

def compute_importance(text: str, message) -> float:
    """Насколько сообщение важно (0-100)."""
    if not text:
        return 10.0
    
    score = 30.0
    
    if "?" in text:
        score += 25
    
    if "систмка" in text.lower():
        score += 40
    
    if text.startswith('💟') or text.startswith('/'):
        score += 50
    
    if message.reply_to_message:
        try:
            bot_id = message.bot.get_me().id if hasattr(message, 'bot') else None
            if bot_id and message.reply_to_message.from_user.id == bot_id:
                score += 45
        except Exception:
            pass
    
    if len(text) > 100:
        score += 10
    elif len(text) < 5:
        score -= 20
    
    emotional = ["срочно", "помоги", "важно", "пожалуйста", "очень"]
    if any(w in text.lower() for w in emotional):
        score += 15
    
    return min(100, max(0, score))


def compute_urgency(message, text: str, user_id: int) -> float:
    """Насколько срочно нужно ответить (0-100)."""
    importance = compute_importance(text, message)
    user_affection = brain.get_value("user_affection")
    fatigue = brain.get_value("fatigue")
    
    joy = brain.get_value("joy")
    sadness = brain.get_value("sadness")
    mood_bonus = joy - sadness + 50
    
    urgency = (
        importance * 0.5 +
        user_affection * 0.2 +
        (100 - fatigue) * 0.2 +
        mood_bonus * 0.1
    )
    
    return min(100, max(0, urgency))


# ============================================================
# 3. РЕШЕНИЕ: ОТВЕЧАТЬ ИЛИ НЕТ
# ============================================================

def should_respond(message, text: str, user_id: int) -> Dict:
    """
    Решить, отвечать или нет.
    
    Returns:
        {
            "respond": bool,
            "response_count": int,
            "urgency": float,
            "reason": str,
            "delay": float,
        }
    """
    urgency = compute_urgency(message, text, user_id)
    
    fatigue = brain.get_value("fatigue")
    energy = brain.get_value("energy")
    
    if fatigue > 80:
        if urgency < 70:
            return {
                "respond": False,
                "response_count": 0,
                "urgency": urgency,
                "reason": "устала",
                "delay": 0,
            }
    
    if energy < 20 and urgency < 50:
        return {
            "respond": False,
            "response_count": 0,
            "urgency": urgency,
            "reason": "нет энергии",
            "delay": 0,
        }
    
    boredom = brain.get_value("boredom")
    if boredom > 70:
        urgency += 20
    
    if urgency >= 50:
        respond = True
        reason = "срочно"
    elif urgency >= 30:
        respond = random.random() < 0.7
        reason = "может быть"
    else:
        respond = False
        reason = "не срочно"
    
    response_count = 1
    
    if respond:
        excitement = brain.get_value("excitement")
        playfulness = brain.get_value("playfulness")
        mood = _get_mood()
        
        if mood == "excited" and energy > 70:
            response_count = random.choice([1, 2, 2, 3])
        elif mood == "playful" and playfulness > 70:
            response_count = random.choice([1, 2])
        elif fatigue > 70:
            response_count = 1
        
        if urgency > 70 and fatigue > 50:
            response_count = 1
    
    delay = 0.5
    if fatigue > 70:
        delay = 2.0
    elif _get_mood() == "excited":
        delay = 0.2
    
    return {
        "respond": respond,
        "response_count": response_count,
        "urgency": urgency,
        "reason": reason,
        "delay": delay,
    }


# ============================================================
# 4. РЕШЕНИЕ: РЕАКЦИЯ
# ============================================================

def should_react(message, text: str, user_id: int, already_reacted: bool = False) -> Dict:
    """
    Решить, ставить ли реакцию.
    
    Returns:
        {
            "react": bool,
            "reaction": str or None,
            "target": "user_message" / "own_message" / None,
            "sarcastic": bool,
            "reason": str,
            "remove": bool,
        }
    """
    if already_reacted:
        if random.random() < 0.1:
            return {
                "react": False,
                "reaction": None,
                "target": None,
                "sarcastic": False,
                "reason": "убрать",
                "remove": True,
            }
    
    user_affection = brain.get_value("user_affection")
    fatigue = brain.get_value("fatigue")
    joy = brain.get_value("joy")
    humor = brain.get_value("humor")
    sarcasm = brain.get_value("sarcasm")
    mood = _get_mood()
    
    react_weight = (
        user_affection * 0.3 +
        (100 - fatigue) * 0.2 +
        joy * 0.2 +
        humor * 0.15 +
        sarcasm * 0.15
    )
    
    if react_weight < 30:
        return {
            "react": False,
            "reaction": None,
            "target": None,
            "sarcastic": False,
            "reason": "не хочу",
            "remove": False,
        }
    
    reaction, sarcastic = _choose_reaction_by_mood(message, text, mood)
    
    if not reaction:
        return {
            "react": False,
            "reaction": None,
            "target": None,
            "sarcastic": False,
            "reason": "нет подходящей",
            "remove": False,
        }
    
    target = "user_message"
    
    if mood == "playful" and random.random() < 0.1:
        target = "own_message"
    
    return {
        "react": True,
        "reaction": reaction,
        "target": target,
        "sarcastic": sarcastic,
        "reason": f"настроение: {mood}",
        "remove": False,
    }


def _choose_reaction_by_mood(message, text: str, mood: str) -> tuple:
    """Выбрать реакцию по настроению."""
    text_lower = (text or "").lower()
    
    sarcasm = brain.get_value("sarcasm")
    if sarcasm > 60 and mood in ("neutral", "bored"):
        if random.random() < 0.4:
            return random.choice(SARCASTIC_REACTIONS), True
    
    love = brain.get_value("love")
    if love > 70:
        return "❤️", False
    
    humor = brain.get_value("humor")
    if humor > 70 and any(w in text_lower for w in ["😂", "ахах", "лол", "кек"]):
        return random.choice(FUNNY_REACTIONS), False
    
    if mood == "sad":
        return random.choice(SAD_REACTIONS), False
    
    if mood == "angry":
        return random.choice(ANGRY_REACTIONS), False
    
    if mood == "bored":
        return "🥱", False
    
    if mood == "happy":
        return random.choice(["❤️", "🔥", "👏", "😊"]), False
    
    return random.choice(FAVORITE_REACTIONS), False


# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def _get_mood() -> str:
    """Определить текущее настроение."""
    if brain.is_emotion_active("anger"):
        return "angry"
    if brain.is_emotion_active("fear"):
        return "scared"
    if brain.is_emotion_active("sadness"):
        return "sad"
    if brain.is_emotion_active("joy"):
        return "happy"
    if brain.is_emotion_active("boredom"):
        return "bored"
    if brain.get_value("excitement") > 70:
        return "excited"
    if brain.get_value("playfulness") > 70:
        return "playful"
    return "neutral"


# ============================================================
# 6. ОБЪЕДИНЕНИЕ СООБЩЕНИЙ
# ============================================================

def should_merge_messages(messages: List[Dict]) -> bool:
    """Объединять ли несколько сообщений в один ответ."""
    if len(messages) < 2:
        return False
    
    if brain.get_value("fatigue") > 60:
        return True
    
    if len(messages) >= 3:
        return True
    
    total_len = sum(len(m.get("text", "")) for m in messages)
    if total_len < 50:
        return True
    
    return False


# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🧠 brain_decisions загружен")
print(f"🎭 Любимых реакций: {len(FAVORITE_REACTIONS)}")
print(f"😏 Саркастичных: {len(SARCASTIC_REACTIONS)}")
print(f"💡 Используй should_respond() и should_react()")