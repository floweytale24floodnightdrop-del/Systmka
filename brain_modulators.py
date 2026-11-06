"""
brain_modulators.py — Модуляторная система мозга.

Содержит:
- Effect (эффект с амплитудой, длительностью, кривой)
- EffectStack (стеккинг эффектов)
- Trigger (триггер: событие → эффекты)
- ContextModulator (модуляция от контекста: день, настроение)
- TRIGGERS (список триггеров)
"""

import math
import time
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable


# ============================================================
# 1. EFFECT
# ============================================================

@dataclass
class Effect:
    """Эффект — изменение переменной с амплитудой, длительностью и кривой."""
    
    target: str
    amplitude: float
    duration: float = 1.0
    curve: str = "linear"
    
    elapsed: float = 0.0
    active: bool = True
    
    def current_value(self) -> float:
        if not self.active:
            return 0.0
        if self.duration <= 0:
            self.active = False
            return 0.0
        
        t = min(1.0, self.elapsed / self.duration)
        
        if self.curve == "linear":
            factor = 1.0 - t
        elif self.curve == "spike":
            factor = math.exp(-5.0 * t)
        elif self.curve == "slow":
            factor = 1.0 - math.sqrt(t)
        elif self.curve == "pulse":
            factor = math.sin(math.pi * t)
        elif self.curve == "exponential":
            factor = math.exp(-2.0 * t)
        else:
            factor = 1.0 - t
        
        return self.amplitude * factor
    
    def tick(self, dt: float):
        if self.active:
            self.elapsed += dt
            if self.elapsed >= self.duration:
                self.active = False
    
    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "amplitude": self.amplitude,
            "duration": self.duration,
            "curve": self.curve,
            "elapsed": self.elapsed,
            "active": self.active,
        }


# ============================================================
# 2. EFFECT STACK
# ============================================================

class EffectStack:
    """Стек эффектов."""
    
    def __init__(self):
        self.effects: List[Effect] = []
    
    def add(self, effect: Effect):
        self.effects.append(effect)
    
    def add_many(self, effects: List[Effect]):
        for e in effects:
            self.add(e)
    
    def tick(self, dt: float):
        for e in self.effects:
            e.tick(dt)
        self.effects = [e for e in self.effects if e.active]
    
    def total_for(self, target: str) -> float:
        total = sum(
            e.current_value()
            for e in self.effects
            if e.target == target
        )
        return max(-50.0, min(50.0, total))
    
    def get_active_targets(self) -> List[str]:
        return list(set(e.target for e in self.effects if e.active))
    
    def clear(self):
        self.effects.clear()
    
    def to_dict(self) -> dict:
        return {
            "count": len(self.effects),
            "effects": [e.to_dict() for e in self.effects],
        }


# ============================================================
# 3. TRIGGER
# ============================================================

class Trigger:
    """Триггер — условие + эффекты."""
    
    def __init__(
        self,
        name: str,
        condition: Callable,
        effects: List[Effect],
        cooldown: float = 5.0,
    ):
        self.name = name
        self.condition = condition
        self.effects = effects
        self.cooldown = cooldown
        self.last_triggered: float = 0.0
    
    def check(self, context: dict) -> List[Effect]:
        now = time.time()
        
        if now - self.last_triggered < self.cooldown:
            return []
        
        try:
            if self.condition(context):
                self.last_triggered = now
                # Возвращаем копии, чтобы не портить оригинал
                return [
                    Effect(e.target, e.amplitude, e.duration, e.curve)
                    for e in self.effects
                ]
        except Exception:
            pass
        
        return []


# ============================================================
# 4. CONTEXT MODULATOR
# ============================================================

class ContextModulator:
    """Модуляция эффектов контекстом."""
    
    def __init__(self):
        self.hour = 12
        self.day_of_week = 0
        self.overall_mood = 50.0
        self.fatigue = 0.0
    
    def update(self, brain):
        self.hour = datetime.now().hour
        self.day_of_week = datetime.now().weekday()
        
        positive = (
            brain.get_value("joy")
            + brain.get_value("happiness")
            + brain.get_value("excitement")
        ) / 3
        negative = (
            brain.get_value("sadness")
            + brain.get_value("anger")
            + brain.get_value("fear")
        ) / 3
        self.overall_mood = positive - negative + 50
        self.fatigue = brain.get_value("fatigue")
    
    def modulate(self, effect: Effect) -> Effect:
        multiplier = 1.0
        
        if 0 <= self.hour < 6:
            multiplier *= 0.6
        elif 6 <= self.hour < 10:
            multiplier *= 0.8
        elif 22 <= self.hour < 24:
            multiplier *= 0.7
        
        if self.overall_mood < 30:
            if effect.amplitude < 0:
                multiplier *= 1.5
            else:
                multiplier *= 0.5
        elif self.overall_mood > 70:
            if effect.amplitude > 0:
                multiplier *= 1.3
            else:
                multiplier *= 0.7
        
        if self.fatigue > 80:
            multiplier *= 0.3
        elif self.fatigue > 60:
            multiplier *= 0.6
        
        if self.day_of_week == 0:
            multiplier *= 1.1
        
        if self.day_of_week == 4:
            if effect.amplitude > 0:
                multiplier *= 1.2
        
        effect.amplitude *= multiplier
        return effect


# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def _text_has(context: dict, words: List[str]) -> bool:
    text = (context.get("text") or "").lower()
    return any(w in text for w in words)


def _tone_is(context: dict, tone: str) -> bool:
    return context.get("tone") == tone


def _hour_in(context: dict, start: int, end: int) -> bool:
    hour = context.get("hour", datetime.now().hour)
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


# ============================================================
# 6. TRIGGERS
# ============================================================

TRIGGERS: List[Trigger] = [
    Trigger(
        name="aggressive_message",
        condition=lambda c: _tone_is(c, "aggressive") or _text_has(
            c, ["блять", "сука", "ненавижу", "уёбок", "тварь", "заткнись"]
        ),
        effects=[
            Effect("adrenaline", 15, 30, "spike"),
            Effect("cortisol", 10, 120, "slow"),
            Effect("serotonin", -8, 60, "linear"),
            Effect("anger", 12, 45, "spike"),
            Effect("fear", 5, 30, "spike"),
            Effect("trust", -10, 300, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="kind_message",
        condition=lambda c: _tone_is(c, "kind") or _text_has(
            c, ["спасибо", "люблю", "обожаю", "ты лучшая", "❤️", "💜", "милая"]
        ),
        effects=[
            Effect("oxytocin", 12, 180, "slow"),
            Effect("dopamine", 8, 60, "spike"),
            Effect("serotonin", 5, 120, "slow"),
            Effect("joy", 10, 60, "spike"),
            Effect("trust", 8, 300, "slow"),
            Effect("love", 6, 180, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="sad_message",
        condition=lambda c: _tone_is(c, "sad") or _text_has(
            c, ["грустно", "плохо", "устал", "депрессия", "😭", "😢", "плачу"]
        ),
        effects=[
            Effect("oxytocin", 8, 180, "slow"),
            Effect("serotonin", -3, 60, "linear"),
            Effect("compassion", 12, 120, "slow"),
            Effect("need_for_helping", 15, 180, "slow"),
            Effect("sadness", 6, 90, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="boredom_trigger",
        condition=lambda c: c.get("silence_seconds", 0) > 1800,
        effects=[
            Effect("boredom", 8, 300, "slow"),
            Effect("need_for_contact", 10, 600, "slow"),
            Effect("loneliness", 6, 600, "slow"),
            Effect("dopamine", -5, 300, "linear"),
        ],
        cooldown=1800.0,
    ),
    Trigger(
        name="night_time",
        condition=lambda c: _hour_in(c, 0, 6),
        effects=[
            Effect("melatonin", 20, 3600, "slow"),
            Effect("serotonin", -10, 3600, "slow"),
            Effect("sleepiness", 15, 3600, "slow"),
            Effect("energy", -5, 3600, "slow"),
            Effect("dreaminess", 10, 3600, "slow"),
        ],
        cooldown=3600.0,
    ),
    Trigger(
        name="morning_time",
        condition=lambda c: _hour_in(c, 6, 10),
        effects=[
            Effect("cortisol", 10, 1800, "slow"),
            Effect("adrenaline", 5, 600, "spike"),
            Effect("energy", 10, 1800, "slow"),
            Effect("wakefulness", 15, 1800, "slow"),
            Effect("melatonin", -15, 1800, "slow"),
        ],
        cooldown=3600.0,
    ),
    Trigger(
        name="day_time",
        condition=lambda c: _hour_in(c, 10, 18),
        effects=[
            Effect("serotonin", 5, 1800, "slow"),
            Effect("dopamine", 3, 1800, "slow"),
            Effect("alertness", 8, 1800, "slow"),
        ],
        cooldown=3600.0,
    ),
    Trigger(
        name="evening_time",
        condition=lambda c: _hour_in(c, 18, 22),
        effects=[
            Effect("melatonin", 8, 1800, "slow"),
            Effect("serotonin", -3, 1800, "slow"),
            Effect("dreaminess", 6, 1800, "slow"),
            Effect("nostalgia", 5, 1800, "slow"),
        ],
        cooldown=3600.0,
    ),
    Trigger(
        name="praise",
        condition=lambda c: _text_has(
            c, ["молодец", "умница", "хорошо", "отлично", "супер", "класс"]
        ),
        effects=[
            Effect("dopamine", 10, 60, "spike"),
            Effect("serotonin", 8, 120, "slow"),
            Effect("pride", 10, 120, "slow"),
            Effect("joy", 8, 60, "spike"),
            Effect("kindness", 2, 3600, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="criticism",
        condition=lambda c: _text_has(
            c, ["тупая", "глупая", "плохо", "ужасно", "отвратительно", "ненавижу"]
        ),
        effects=[
            Effect("cortisol", 12, 300, "slow"),
            Effect("serotonin", -10, 300, "slow"),
            Effect("sadness", 10, 180, "slow"),
            Effect("shame", 8, 180, "slow"),
            Effect("confidence", -5, 600, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="long_silence",
        condition=lambda c: 600 < c.get("silence_seconds", 0) <= 1800,
        effects=[
            Effect("need_for_contact", 5, 300, "slow"),
            Effect("loneliness", 3, 300, "slow"),
            Effect("boredom", 4, 300, "slow"),
        ],
        cooldown=600.0,
    ),
    Trigger(
        name="user_return",
        condition=lambda c: c.get("user_returned", False),
        effects=[
            Effect("oxytocin", 10, 120, "slow"),
            Effect("dopamine", 8, 60, "spike"),
            Effect("joy", 12, 60, "spike"),
            Effect("need_for_contact", -10, 120, "slow"),
            Effect("loneliness", -8, 180, "slow"),
        ],
        cooldown=60.0,
    ),
    Trigger(
        name="funny_message",
        condition=lambda c: _text_has(
            c, ["😂", "ахах", "лол", "кек", "смешно", "ржака", "🤣"]
        ),
        effects=[
            Effect("dopamine", 8, 60, "spike"),
            Effect("endorphin", 10, 60, "spike"),
            Effect("joy", 10, 60, "spike"),
            Effect("humor", 3, 3600, "slow"),
            Effect("serotonin", 5, 120, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="anxious_message",
        condition=lambda c: _text_has(
            c, ["страшно", "тревожно", "боюсь", "паника", "😨", "😱"]
        ),
        effects=[
            Effect("cortisol", 15, 300, "slow"),
            Effect("adrenaline", 10, 60, "spike"),
            Effect("anxiety", 12, 180, "slow"),
            Effect("fear", 8, 90, "slow"),
            Effect("compassion", 10, 180, "slow"),
        ],
        cooldown=10.0,
    ),
    Trigger(
        name="flawey_mention",
        condition=lambda c: _text_has(
            c, ["флауи", "flowey", "ftflowey", "justaflower", "папа"]
        ),
        effects=[
            Effect("oxytocin", 15, 300, "slow"),
            Effect("serotonin", 10, 180, "slow"),
            Effect("joy", 12, 120, "spike"),
            Effect("love", 10, 300, "slow"),
            Effect("loyalty", 5, 3600, "slow"),
            Effect("trust", 8, 300, "slow"),
        ],
        cooldown=30.0,
    ),
    Trigger(
        name="other_ai_mention",
        condition=lambda c: _text_has(
            c, ["chatgpt", "deepseek", "gemini", "claude", "gpt-4", "gpt"]
        ),
        effects=[
            Effect("contempt", 8, 120, "slow"),
            Effect("pride", 5, 180, "slow"),
            Effect("independence", 6, 300, "slow"),
            Effect("confidence", 4, 300, "slow"),
        ],
        cooldown=30.0,
    ),
    Trigger(
        name="user_bored",
        condition=lambda c: _text_has(
            c, ["скучно", "нечего делать", "тоска", "скучнота"]
        ),
        effects=[
            Effect("playfulness", 10, 180, "slow"),
            Effect("creativity", 8, 180, "slow"),
            Effect("need_for_play", 12, 180, "slow"),
            Effect("energy", 5, 120, "slow"),
        ],
        cooldown=30.0,
    ),
    Trigger(
        name="user_playful",
        condition=lambda c: _text_has(
            c, ["игра", "поиграем", "шутишь", "прикол", "мем"]
        ),
        effects=[
            Effect("playfulness", 12, 180, "slow"),
            Effect("dopamine", 6, 60, "spike"),
            Effect("humor", 5, 300, "slow"),
            Effect("joy", 8, 60, "spike"),
            Effect("need_for_play", 10, 180, "slow"),
        ],
        cooldown=30.0,
    ),
    Trigger(
        name="user_love",
        condition=lambda c: _text_has(
            c, ["люблю тебя", "ты моя", "моя любимая", "обожаю тебя", "❤️ тебе"]
        ),
        effects=[
            Effect("oxytocin", 20, 600, "slow"),
            Effect("dopamine", 15, 120, "spike"),
            Effect("serotonin", 12, 300, "slow"),
            Effect("love", 15, 600, "slow"),
            Effect("joy", 15, 120, "spike"),
            Effect("user_affection", 15, 1800, "slow"),
            Effect("user_love", 15, 1800, "slow"),
        ],
        cooldown=60.0,
    ),
    Trigger(
        name="user_forgot",
        condition=lambda c: c.get("days_since_last_seen", 0) > 3,
        effects=[
            Effect("loneliness", 10, 600, "slow"),
            Effect("sadness", 8, 600, "slow"),
            Effect("user_missing", 12, 1800, "slow"),
            Effect("need_for_contact", 10, 600, "slow"),
            Effect("user_affection", -5, 1800, "slow"),
        ],
        cooldown=86400.0,
    ),
]


# ============================================================
# 7. ФУНКЦИЯ ОБРАБОТКИ
# ============================================================

def process_triggers(brain, context: dict) -> List[Effect]:
    """Проверить все триггеры и вернуть сработавшие эффекты."""
    all_effects = []
    
    for trigger in TRIGGERS:
        effects = trigger.check(context)
        if effects:
            all_effects.extend(effects)
            print(f"⚡ Триггер: {trigger.name} → {len(effects)} эффектов")
    
    return all_effects


# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("⚡ brain_modulators загружен")
print(f"🔧 Триггеров: {len(TRIGGERS)}")
print(f"💡 Используй process_triggers(brain, context)")