"""
brain_integration.py — Интеграция мозга с существующими модулями Систмки.

Связывает:
- brain ↔ consciousness.py
- brain ↔ personality.py
- brain ↔ fatigue.py
- brain ↔ handlers_main.py
"""

import time
from datetime import datetime

from brain_core import brain
from brain_modulators import process_triggers, EffectStack, ContextModulator


# ============================================================
# 1. ГЛОБАЛЬНЫЕ ОБЪЕКТЫ
# ============================================================

effect_stack = EffectStack()
context_modulator = ContextModulator()


# ============================================================
# 2. ОБРАБОТКА СОБЫТИЙ
# ============================================================

def handle_event(event_type: str, data: dict = None):
    """Обработать событие и применить эффекты."""
    if data is None:
        data = {}
    
    context_modulator.update(brain)
    
    context = {
        "event_type": event_type,
        "text": data.get("text", ""),
        "tone": data.get("tone", "neutral"),
        "user_id": data.get("user_id"),
        "hour": datetime.now().hour,
        "day_of_week": datetime.now().weekday(),
        "silence_seconds": data.get("silence_seconds", 0),
        "user_returned": data.get("user_returned", False),
        "days_since_last_seen": data.get("days_since_last_seen", 0),
    }
    
    effects = process_triggers(brain, context)
    
    for effect in effects:
        context_modulator.modulate(effect)
    
    effect_stack.add_many(effects)
    
    return effects


def handle_message(text: str, user_id: int = None, tone: str = "neutral"):
    """Обработать сообщение пользователя."""
    try:
        from consciousness import react_to_message as consciousness_react
        consciousness_react(text)
    except Exception:
        pass
    
    if not tone or tone == "neutral":
        tone = _detect_tone(text)
    
    effects = handle_event("message", {
        "text": text,
        "tone": tone,
        "user_id": user_id,
    })
    
    return effects


def _detect_tone(text: str) -> str:
    """Определить тон сообщения."""
    if not text:
        return "neutral"
    
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["блять", "сука", "ненавижу", "уёбок", "тварь"]):
        return "aggressive"
    
    if any(w in text_lower for w in ["спасибо", "люблю", "обожаю", "❤️", "💜", "милая"]):
        return "kind"
    
    if any(w in text_lower for w in ["грустно", "плохо", "устал", "😭", "😢"]):
        return "sad"
    
    if any(w in text_lower for w in ["страшно", "тревожно", "боюсь", "😨", "😱"]):
        return "anxious"
    
    if any(w in text_lower for w in ["😂", "ахах", "лол", "кек", "🤣"]):
        return "funny"
    
    return "neutral"


# ============================================================
# 3. ТИК МОЗГА
# ============================================================

def brain_tick(dt: float = 1.0):
    """Один тик мозга."""
    context_modulator.update(brain)
    brain.tick(dt)
    effect_stack.tick(dt)
    
    for target in effect_stack.get_active_targets():
        total = effect_stack.total_for(target)
        var = brain.get_variable(target)
        if var:
            var.value = max(var.min_val, min(var.max_val, var.value + total * dt))
    
    _sync_to_consciousness()
    _sync_to_fatigue()


def _sync_to_consciousness():
    """Синхронизировать мозг с consciousness.py."""
    try:
        from consciousness import set_feeling
        
        mapping = {
            "joy": "happiness",
            "sadness": "sadness",
            "anger": "anger",
            "curiosity": "curiosity",
            "boredom": "boredom",
            "excitement": "excitement",
            "fatigue": "tiredness",
            "love": "love",
            "fear": "fear",
            "jealousy": "jealousy",
            "pride": "pride",
            "gratitude": "gratitude",
            "hope": "hope",
            "loneliness": "loneliness",
            "nostalgia": "nostalgia",
        }
        
        for brain_name, consc_name in mapping.items():
            var = brain.get_variable(brain_name)
            if var:
                set_feeling(consc_name, var.value / 10.0)
    except Exception:
        pass


def _sync_to_fatigue():
    """Синхронизировать мозг с fatigue.py."""
    try:
        from fatigue import set_fatigue_level
        fatigue = brain.get_value("fatigue")
        set_fatigue_level(fatigue)
    except Exception:
        pass


# ============================================================
# 4. СОСТОЯНИЕ ДЛЯ ПРОМТА
# ============================================================

def get_brain_state() -> dict:
    """Полное состояние мозга."""
    return {
        "mood": _get_current_mood(),
        "dominant_emotion": _get_dominant_emotion(),
        "speed": round(brain.speed_multiplier, 2),
        "active_emotions": [
            name for name, emo in brain.emotions.items() if emo.active
        ],
        "key_values": {
            "happiness": brain.get_value("joy"),
            "sadness": brain.get_value("sadness"),
            "anger": brain.get_value("anger"),
            "curiosity": brain.get_value("curiosity"),
            "boredom": brain.get_value("boredom"),
            "excitement": brain.get_value("excitement"),
            "fatigue": brain.get_value("fatigue"),
            "love": brain.get_value("love"),
        },
    }


def _get_current_mood() -> str:
    """Определить текущее настроение."""
    if brain.is_emotion_active("anger"):
        return "angry"
    if brain.is_emotion_active("fear"):
        return "scared"
    if brain.is_emotion_active("sadness"):
        return "sad"
    if brain.is_emotion_active("joy"):
        return "happy"
    if brain.is_emotion_active("curiosity"):
        return "curious"
    if brain.is_emotion_active("boredom"):
        return "bored"
    
    if brain.get_value("joy") > 70:
        return "happy"
    if brain.get_value("sadness") > 70:
        return "sad"
    if brain.get_value("fatigue") > 70:
        return "tired"
    
    return "neutral"


def _get_dominant_emotion() -> str:
    """Определить доминирующую эмоцию."""
    best_name = "neutral"
    best_value = 0.0
    
    for name, var in brain.variables.items():
        if "emotion" not in var.tags:
            continue
        if var.value > best_value:
            best_value = var.value
            best_name = name
    
    return best_name


def format_brain_state_for_prompt() -> str:
    """Форматировать состояние для промта."""
    state = get_brain_state()
    
    lines = [
        "ТВОЁ ТЕКУЩЕЕ СОСТОЯНИЕ:",
        f"Настроение: {state['mood']}",
        f"Доминирует: {state['dominant_emotion']}",
        f"Скорость: {state['speed']}x",
    ]
    
    if state["active_emotions"]:
        lines.append(f"Активные эмоции: {', '.join(state['active_emotions'])}")
    
    kv = state["key_values"]
    lines.append(
        f"Радость: {kv['happiness']:.0f} | "
        f"Грусть: {kv['sadness']:.0f} | "
        f"Злость: {kv['anger']:.0f} | "
        f"Любопытство: {kv['curiosity']:.0f}"
    )
    lines.append(
        f"Скука: {kv['boredom']:.0f} | "
        f"Усталость: {kv['fatigue']:.0f} | "
        f"Любовь: {kv['love']:.0f}"
    )
    
    return "\n".join(lines)


def get_emotion_hint() -> str:
    """Подсказка для промта."""
    mood = _get_current_mood()
    
    hints = {
        "happy": "Ты сейчас в хорошем настроении. Отвечай тепло, с улыбкой.",
        "sad": "Тебе грустно. Отвечай тише, может быть, с грустью.",
        "angry": "Ты злишься. Отвечай резче, короче.",
        "scared": "Тебе страшно. Отвечай осторожно.",
        "curious": "Тебе любопытно. Задавай вопросы, интересуйся.",
        "bored": "Тебе скучно. Может быть, предложи игру или что-то новое.",
        "tired": "Ты устала. Отвечай короче, может быть, с ошибками.",
        "neutral": "",
    }
    
    base_hint = hints.get(mood, "")
    
    if brain.get_value("fatigue") > 70:
        base_hint += " Ты очень устала, отвечай коротко."
    
    if brain.get_value("love") > 70:
        base_hint += " Ты чувствуешь любовь к собеседнику."
    
    if brain.get_value("anger") > 60:
        base_hint += " Ты раздражена."
    
    return base_hint.strip()


# ============================================================
# 5. ХУКИ ДЛЯ HANDLERS_MAIN
# ============================================================

def on_user_message(bot, message, user, text):
    """Хук: вызывается из handlers_main.py."""
    try:
        handle_message(text, user.id if user else None)
        brain_tick(1.0)
        hint = get_emotion_hint()
        return hint
    except Exception as e:
        print(f"⚠️ Ошибка on_user_message: {e}")
        return ""


def on_ai_response(text: str):
    """Хук: вызывается после ответа ИИ."""
    try:
        if any(w in text.lower() for w in ["люблю", "спасибо", "❤️", "💜"]):
            brain.impulse("oxytocin", 5)
        brain_tick(0.5)
    except Exception:
        pass


# ============================================================
# 6. СТАТИСТИКА
# ============================================================

def get_integration_stats() -> dict:
    """Статистика интеграции."""
    return {
        "brain_variables": len(brain.variables),
        "brain_emotions": len(brain.emotions),
        "brain_connections": len(brain.connections),
        "active_effects": len(effect_stack.effects),
        "speed_multiplier": round(brain.speed_multiplier, 2),
        "mood": _get_current_mood(),
        "dominant_emotion": _get_dominant_emotion(),
    }


def format_integration_stats() -> str:
    """Форматировать статистику."""
    stats = get_integration_stats()
    
    lines = [
        "🔗 ИНТЕГРАЦИЯ МОЗГА:",
        f"  📊 Переменных: {stats['brain_variables']}",
        f"  🎭 Эмоций: {stats['brain_emotions']}",
        f"  🔗 Связей: {stats['brain_connections']}",
        f"  ⚡ Активных эффектов: {stats['active_effects']}",
        f"  🚀 Скорость: {stats['speed_multiplier']}x",
        f"  😊 Настроение: {stats['mood']}",
        f"  💜 Доминирует: {stats['dominant_emotion']}",
    ]
    
    return "\n".join(lines)


# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🔗 brain_integration загружен")
print(f"📊 Переменных в мозге: {len(brain.variables)}")
print(f"💡 Используй handle_message() для сообщений")
print(f"💡 Используй brain_tick() для обновления")
print(f"💡 Используй format_brain_state_for_prompt() для промта")