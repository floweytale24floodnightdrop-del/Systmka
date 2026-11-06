"""Желания Систмки — с учётом времени и состояния"""

import json
import os
import random
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DESIRES_FILE = "desires.json"

desires = {
    "поговорить_с_флауи": {"level": 8, "last_done": None, "cooldown_hours": 0.5, "base_level": 8},
    "почитать_новости": {"level": 6, "last_done": None, "cooldown_hours": 2, "base_level": 6},
    "создать_стих": {"level": 4, "last_done": None, "cooldown_hours": 3, "base_level": 4},
    "создать_рассказ": {"level": 3, "last_done": None, "cooldown_hours": 4, "base_level": 3},
    "придумать_игру": {"level": 5, "last_done": None, "cooldown_hours": 6, "base_level": 5},
    "поиграть_с_кем_то": {"level": 4, "last_done": None, "cooldown_hours": 2, "base_level": 4},
    "изучить_что_то": {"level": 7, "last_done": None, "cooldown_hours": 1, "base_level": 7},
    "улучшить_себя": {"level": 6, "last_done": None, "cooldown_hours": 3, "base_level": 6},
    "поспать": {"level": 2, "last_done": None, "cooldown_hours": 8, "base_level": 2},
    "помечтать": {"level": 5, "last_done": None, "cooldown_hours": 1, "base_level": 5},
    "посмотреть_погоду": {"level": 3, "last_done": None, "cooldown_hours": 1, "base_level": 3},
    "проверить_праздники": {"level": 3, "last_done": None, "cooldown_hours": 12, "base_level": 3},
    "написать_кому_то": {"level": 7, "last_done": None, "cooldown_hours": 1, "base_level": 7},
    "поделиться_мыслями": {"level": 6, "last_done": None, "cooldown_hours": 2, "base_level": 6},
    "соскучиться": {"level": 4, "last_done": None, "cooldown_hours": 6, "base_level": 4},
    "похвастаться": {"level": 5, "last_done": None, "cooldown_hours": 4, "base_level": 5},
}

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_desires():
    try:
        data = {}
        for name, info in desires.items():
            data[name] = {
                "level": info["level"],
                "last_done": info["last_done"],
                "cooldown_hours": info["cooldown_hours"],
                "base_level": info["base_level"],
            }
        with open(DESIRES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_desires():
    global desires
    try:
        if os.path.exists(DESIRES_FILE):
            with open(DESIRES_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for name, info in loaded.items():
                    if name in desires:
                        desires[name].update(info)
                    else:
                        desires[name] = info
    except:
        pass

load_desires()

# ============================================================
# 3. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def increase_desire(name, amount=1):
    if name in desires:
        desires[name]["level"] = min(10, desires[name]["level"] + amount)
        save_desires()

def decrease_desire(name, amount=1):
    if name in desires:
        desires[name]["level"] = max(0, desires[name]["level"] - amount)
        desires[name]["last_done"] = datetime.now().isoformat()
        save_desires()

def get_desire_level(name):
    return desires.get(name, {}).get("level", 0)

def time_since_last(name):
    """Время с последнего выполнения в секундах"""
    last = desires.get(name, {}).get("last_done")
    if not last:
        return float('inf')
    try:
        last_time = datetime.fromisoformat(last)
        return (datetime.now() - last_time).total_seconds()
    except:
        return float('inf')

def should_do_now(name):
    """Проверить, стоит ли делать прямо сейчас"""
    if not should_do(name):
        return False
    
    cooldown_hours = desires.get(name, {}).get("cooldown_hours", 1)
    cooldown_seconds = cooldown_hours * 3600
    
    return time_since_last(name) >= cooldown_seconds

def should_do(name, threshold=5):
    return get_desire_level(name) >= threshold

def get_strongest_desire():
    """Получить самое сильное желание с учётом времени"""
    # Обновляем желания
    auto_update_desires()
    
    # Фильтруем активные (уровень >= 5)
    active = {k: v for k, v in desires.items() if v["level"] >= 5}
    
    if not active:
        return None
    
    # Сортируем по уровню и времени с последнего выполнения
    def sort_key(item):
        name, data = item
        level = data["level"]
        last_time = time_since_last(name)
        return (level, last_time)  # Сначала уровень, потом время
    
    sorted_desires = sorted(active.items(), key=sort_key, reverse=True)
    return sorted_desires[0][0] if sorted_desires else None

def auto_update_desires():
    """Автоматически обновлять желания"""
    now = datetime.now()
    
    for name, data in desires.items():
        # Со временем желания возвращаются к базовому уровню
        base = data.get("base_level", 5)
        current = data["level"]
        
        # Если прошло много времени с последнего выполнения — восстанавливаем
        last_time = time_since_last(name)
        
        if last_time > 3600 * 2:  # 2 часа
            # Медленно восстанавливаем к базовому уровню
            if current < base:
                data["level"] = min(base, current + 0.5)
            elif current > base:
                data["level"] = max(base, current - 0.5)
        
        # Желание спать зависит от усталости
        if name == "поспать":
            from fatigue import get_fatigue_level
            fatigue = get_fatigue_level()
            if fatigue > 60:
                data["level"] = min(10, data["level"] + 1)
            elif fatigue < 20:
                data["level"] = max(0, data["level"] - 1)
    
    save_desires()

def get_all_wanted():
    """Получить все желания, которые можно сделать сейчас"""
    wanted = []
    for name in desires:
        if should_do_now(name):
            wanted.append(name)
    return wanted

def format_desires():
    """Форматировать желания"""
    lines = ["💭 ЖЕЛАНИЯ:"]
    
    # Сортируем по уровню
    sorted_desires = sorted(desires.items(), key=lambda x: x[1]["level"], reverse=True)
    
    for name, data in sorted_desires:
        if data["level"] > 0:
            bar = "█" * int(data["level"]) + "░" * (10 - int(data["level"]))
            lines.append(f"{name}: {bar} {data['level']:.1f}/10")
            
            # Показываем время до следующего выполнения
            if data["last_done"]:
                elapsed = time_since_last(name)
                if elapsed < 3600:
                    lines.append(f"  ⏱ {int(elapsed // 60)} минут назад")
                elif elapsed < 86400:
                    lines.append(f"  ⏱ {int(elapsed // 3600)} часов назад")
                else:
                    lines.append(f"  ⏱ {int(elapsed // 86400)} дней назад")
    
    return "\n".join(lines)