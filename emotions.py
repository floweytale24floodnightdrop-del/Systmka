"""Эмоции Систмки — тонкая обёртка над consciousness.py"""

# ============================================================
# 1. ИМПОРТ ЕДИНОГО ИСТОЧНИКА ПРАВДЫ
# ============================================================

from consciousness import (
    # Эмоции
    get_feeling,
    set_feeling,
    increase_feeling,
    decrease_feeling,
    get_dominant_emotion,
    get_all_feelings,
    reset_feelings,
    feel,
    react_to_message,
    # Настроение
    get_mood,
    set_mood,
    get_mood_description,
    get_mood_trend,
    record_mood,
    update_mood,
    # Хранилище (для совместимости)
    consciousness,
)

# ============================================================
# 2. СОВМЕСТИМОСТЬ СО СТАРЫМ API
# ============================================================

# Старый API: `emotions` — это dict с эмоциями
# Теперь это ссылка на `consciousness["feelings"]`
emotions = consciousness["feelings"]

# Старый API: `mood_history` — это list
mood_history = consciousness["mood_history"]

# ============================================================
# 3. ОБЁРТКИ СТАРЫХ ФУНКЦИЙ
# ============================================================

def get_emotion(name):
    """Старое имя: get_emotion → get_feeling"""
    return get_feeling(name)

def set_emotion(name, value):
    """Старое имя: set_emotion → set_feeling"""
    return set_feeling(name, value)

def increase_emotion(name, amount=1):
    """Старое имя: increase_emotion → increase_feeling"""
    return increase_feeling(name, amount)

def decrease_emotion(name, amount=1):
    """Старое имя: decrease_emotion → decrease_feeling"""
    return decrease_feeling(name, amount)

# ============================================================
# 4. ФОРМАТИРОВАНИЕ
# ============================================================

def format_emotions():
    """Форматировать эмоции"""
    all_feelings = get_all_feelings()
    
    lines = ["😊 ЭМОЦИИ:"]
    for emotion, value in all_feelings.items():
        if value > 0:
            bar = "█" * int(value) + "░" * (10 - int(value))
            lines.append(f"  {emotion}: {bar} {value}/10")
    
    lines.append("")
    lines.append(f"  Доминирует: {get_mood_description()}")
    lines.append(f"  Тренд: {get_mood_trend()}")
    lines.append(f"  Настроение: {get_mood()}")
    
    return "\n".join(lines)

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("😊 Модуль эмоций загружен (обёртка над consciousness)")
print(f"📊 Доминирует: {get_dominant_emotion()}")
print(f"🎭 Настроение: {get_mood()}")