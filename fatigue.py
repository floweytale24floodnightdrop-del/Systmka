"""Система усталости Систмки — с сохранением и привязкой ко времени"""

import json
import os
import random
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

FATIGUE_FILE = "fatigue_data.json"

# Параметры усталости
MAX_FATIGUE = 100
SLEEP_RESTORE_RATE = 15
FATIGUE_PER_HOUR_AWAKE = 3
MAX_AWAKE_HOURS = 48
MIN_SLEEP_HOURS = 4
MAX_SLEEP_HOURS = 8

# ============================================================
# 2. ДАННЫЕ (СОХРАНЯЮТСЯ)
# ============================================================

fatigue_data = {
    "level": 0,
    "last_update": None,
    "last_sleep_start": None,
    "sleep_duration": 0,
    "total_sleep_today": 0,
    "awake_since": None,
    "daily_reset": None,
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_fatigue():
    try:
        data = {
            "level": fatigue_data["level"],
            "last_update": fatigue_data["last_update"].isoformat() if fatigue_data["last_update"] else None,
            "last_sleep_start": fatigue_data["last_sleep_start"].isoformat() if fatigue_data["last_sleep_start"] else None,
            "sleep_duration": fatigue_data["sleep_duration"],
            "total_sleep_today": fatigue_data["total_sleep_today"],
            "awake_since": fatigue_data["awake_since"].isoformat() if fatigue_data["awake_since"] else None,
            "daily_reset": fatigue_data["daily_reset"].isoformat() if fatigue_data["daily_reset"] else None,
        }
        with open(FATIGUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения усталости: {e}")
        return False

def load_fatigue():
    global fatigue_data
    try:
        if os.path.exists(FATIGUE_FILE):
            with open(FATIGUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                fatigue_data["level"] = data.get("level", 0)
                fatigue_data["last_update"] = datetime.fromisoformat(data["last_update"]) if data.get("last_update") else None
                fatigue_data["last_sleep_start"] = datetime.fromisoformat(data["last_sleep_start"]) if data.get("last_sleep_start") else None
                fatigue_data["sleep_duration"] = data.get("sleep_duration", 0)
                fatigue_data["total_sleep_today"] = data.get("total_sleep_today", 0)
                fatigue_data["awake_since"] = datetime.fromisoformat(data["awake_since"]) if data.get("awake_since") else None
                fatigue_data["daily_reset"] = datetime.fromisoformat(data["daily_reset"]) if data.get("daily_reset") else None
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки усталости: {e}")
        return False

load_fatigue()

# ============================================================
# 4. ОБНОВЛЕНИЕ УСТАЛОСТИ
# ============================================================

def update_fatigue():
    now = datetime.now()
    
    if fatigue_data["daily_reset"] is None:
        fatigue_data["daily_reset"] = now
    elif (now - fatigue_data["daily_reset"]).days > 0:
        fatigue_data["total_sleep_today"] = 0
        fatigue_data["daily_reset"] = now
    
    if fatigue_data["last_update"] is None:
        fatigue_data["last_update"] = now
        save_fatigue()
        return
    
    delta = now - fatigue_data["last_update"]
    hours_passed = delta.total_seconds() / 3600
    
    if hours_passed < 0.05:
        return
    
    if fatigue_data["last_sleep_start"] is not None:
        sleep_delta = now - fatigue_data["last_sleep_start"]
        sleep_hours = sleep_delta.total_seconds() / 3600
        
        restore_amount = sleep_hours * SLEEP_RESTORE_RATE
        fatigue_data["level"] = max(0, fatigue_data["level"] - restore_amount)
        fatigue_data["sleep_duration"] += sleep_hours
        fatigue_data["total_sleep_today"] += sleep_hours
        
        if fatigue_data["level"] <= 0 or fatigue_data["sleep_duration"] >= MAX_SLEEP_HOURS:
            fatigue_data["level"] = 0
            fatigue_data["last_sleep_start"] = None
            fatigue_data["sleep_duration"] = 0
            fatigue_data["awake_since"] = now
            print("😊 Систмка проснулась!")
            save_fatigue()
            return
        
        save_fatigue()
        return
    
    if fatigue_data["awake_since"] is not None:
        awake_delta = now - fatigue_data["awake_since"]
        awake_hours = awake_delta.total_seconds() / 3600
        
        fatigue_increase = awake_hours * FATIGUE_PER_HOUR_AWAKE
        fatigue_data["level"] = min(MAX_FATIGUE, fatigue_data["level"] + fatigue_increase)
        
        if awake_hours >= MAX_AWAKE_HOURS:
            fatigue_data["level"] = MAX_FATIGUE
            print("⚠️ Систмка не спала 48 часов! Срочно нужен сон!")
    
    fatigue_data["last_update"] = now
    save_fatigue()

# ============================================================
# 5. УПРАВЛЕНИЕ СНОМ
# ============================================================

def go_to_sleep():
    if fatigue_data["last_sleep_start"] is not None:
        return False, "Уже сплю"
    
    fatigue_data["last_sleep_start"] = datetime.now()
    fatigue_data["sleep_duration"] = 0
    fatigue_data["awake_since"] = None
    save_fatigue()
    print("💤 Систмка легла спать")
    return True, "Спокойной ночи! 🌙"

def wake_up():
    if fatigue_data["last_sleep_start"] is None:
        return False, "Я не сплю"
    
    now = datetime.now()
    sleep_delta = now - fatigue_data["last_sleep_start"]
    sleep_hours = sleep_delta.total_seconds() / 3600
    
    if sleep_hours < MIN_SLEEP_HOURS:
        fatigue_data["level"] = min(MAX_FATIGUE, fatigue_data["level"] + 10)
        print("⚠️ Систмка проснулась раньше времени!")
    
    fatigue_data["last_sleep_start"] = None
    fatigue_data["sleep_duration"] = 0
    fatigue_data["awake_since"] = now
    save_fatigue()
    print("😊 Систмка проснулась")
    return True, "Доброе утро! ☀️"

def is_sleeping():
    update_fatigue()
    return fatigue_data["last_sleep_start"] is not None

def get_fatigue_level():
    update_fatigue()
    return fatigue_data["level"]

# ============================================================
# 6. ГЛАВНЫЕ ФУНКЦИИ (ЭТИ ИСПОЛЬЗУЮТСЯ В handlers_main.py!)
# ============================================================

def increase_fatigue(amount=1):
    """Увеличить усталость — ЭТУ ФУНКЦИЮ ИЩЕТ handlers_main.py!"""
    update_fatigue()
    fatigue_data["level"] = min(MAX_FATIGUE, fatigue_data["level"] + amount)
    save_fatigue()
    return fatigue_data["level"]

def decrease_fatigue(amount=1):
    """Уменьшить усталость"""
    update_fatigue()
    fatigue_data["level"] = max(0, fatigue_data["level"] - amount)
    save_fatigue()
    return fatigue_data["level"]

def reset_fatigue():
    """Сбросить усталость"""
    fatigue_data["level"] = 0
    fatigue_data["awake_since"] = datetime.now()
    save_fatigue()
    return True

def is_tired():
    """Проверить, устала ли Систмка"""
    level = get_fatigue_level()
    return level >= 50

def is_very_tired():
    """Проверить, очень ли устала"""
    level = get_fatigue_level()
    return level >= 70

def is_exhausted():
    """Проверить, полностью ли вымотана"""
    level = get_fatigue_level()
    return level >= 90

def apply_fatigue_to_text(text):
    """Применить эффекты усталости к тексту"""
    level = get_fatigue_level()
    
    if level < 40:
        return text
    
    # Опечатки
    if random.random() < (level / 100):
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 3 and random.random() < 0.2:
                chars = list(word)
                if len(chars) > 1:
                    pos = random.randint(0, len(chars) - 2)
                    chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
                    words[i] = ''.join(chars)
        text = ' '.join(words)
    
    # Пропуск знаков препинания
    if level > 60 and random.random() < 0.3:
        text = text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")
    
    # Нижний регистр
    if level > 80 and random.random() < 0.4:
        text = text.lower()
    
    return text

# ============================================================
# 7. СТАТУС И ИНФОРМАЦИЯ
# ============================================================

def get_fatigue_status():
    level = get_fatigue_level()
    
    if is_sleeping():
        return "💤 Спит"
    elif level >= 90:
        return "😫 Полный раздрай"
    elif level >= 70:
        return "😩 Очень устала"
    elif level >= 50:
        return "😐 Устала"
    elif level >= 30:
        return "🙂 Немного устала"
    else:
        return "😊 Полна энергии"

def format_fatigue_info():
    level = get_fatigue_level()
    status = get_fatigue_status()
    
    lines = [
        "😴 УСТАЛОСТЬ:",
        f"Уровень: {level:.0f}/100",
        f"Статус: {status}",
    ]
    
    if is_sleeping():
        lines.append(f"💤 Спит: {fatigue_data['sleep_duration']:.1f} часов")
    elif fatigue_data["awake_since"]:
        awake_hours = (datetime.now() - fatigue_data["awake_since"]).total_seconds() / 3600
        lines.append(f"⏰ Бодрствует: {awake_hours:.1f} часов")
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

level = get_fatigue_level()
status = get_fatigue_status()
print(f"😴 Усталость: {level:.0f}/100 — {status}")