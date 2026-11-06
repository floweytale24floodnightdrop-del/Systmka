"""Утренние сообщения Систмки — с сохранением на диск"""

import os
import json
import random
import pytz
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MORNING_FILE = "morning_greetings_data.json"
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Часы, когда можно отправлять утреннее приветствие
MORNING_HOUR_START = 6
MORNING_HOUR_END = 11

# Часы, когда можно отправлять proactive-сообщение
PROACTIVE_HOUR_START = 12
PROACTIVE_HOUR_END = 22

# Максимум proactive-сообщений в день
MAX_PROACTIVE_PER_DAY = 2

# ============================================================
# 2. ДАННЫЕ
# ============================================================

morning_data = {
    "favorites": {},  # {user_id: {"favorite_level": 1-10, "added_at": str}}
    "last_morning": {},  # {user_id: "YYYY-MM-DD"}
    "last_proactive": {},  # {user_id: "YYYY-MM-DD"}
    "proactive_count": {},  # {user_id: {"date": "YYYY-MM-DD", "count": int}}
    "stats": {
        "total_morning_sent": 0,
        "total_proactive_sent": 0,
        "last_sent": None,
    },
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_morning_data():
    """Сохранить данные утренних приветствий"""
    try:
        with open(MORNING_FILE, "w", encoding="utf-8") as f:
            json.dump(morning_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения morning: {e}")
        return False

def load_morning_data():
    """Загрузить данные утренних приветствий"""
    global morning_data
    try:
        if os.path.exists(MORNING_FILE):
            with open(MORNING_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ["favorites", "last_morning", "last_proactive", "proactive_count"]:
                    if isinstance(loaded.get(key), dict):
                        morning_data[key] = loaded[key]
                
                if isinstance(loaded.get("stats"), dict):
                    morning_data["stats"].update(loaded["stats"])
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON morning: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки morning: {e}")
        return False

load_morning_data()

# ============================================================
# 4. ВРЕМЯ
# ============================================================

def get_moscow_time():
    """Получить московское время"""
    return datetime.now(MOSCOW_TZ)

def today_str():
    """Сегодняшняя дата в формате YYYY-MM-DD"""
    return get_moscow_time().date().isoformat()

# ============================================================
# 5. УПРАВЛЕНИЕ ЛЮБИМЧИКАМИ
# ============================================================

def set_favorite_level(user_id, level):
    """Установить уровень любимчика (1-10)"""
    user_id_str = str(user_id)
    morning_data["favorites"][user_id_str] = {
        "favorite_level": max(1, min(10, level)),
        "added_at": datetime.now().isoformat(),
    }
    save_morning_data()
    return True

def get_favorite_level(user_id):
    """Получить уровень любимчика (0-10)"""
    user_id_str = str(user_id)
    if user_id_str in morning_data["favorites"]:
        return morning_data["favorites"][user_id_str].get("favorite_level", 0)
    return 0

def increase_favorite(user_id, amount=1):
    """Увеличить уровень любимчика"""
    current = get_favorite_level(user_id)
    return set_favorite_level(user_id, current + amount)

def decrease_favorite(user_id, amount=1):
    """Уменьшить уровень любимчика"""
    current = get_favorite_level(user_id)
    return set_favorite_level(user_id, max(0, current - amount))

def remove_favorite(user_id):
    """Удалить пользователя из любимчиков"""
    user_id_str = str(user_id)
    if user_id_str in morning_data["favorites"]:
        del morning_data["favorites"][user_id_str]
        save_morning_data()
        return True
    return False

def list_favorites():
    """Получить список всех любимчиков"""
    return {
        int(uid): data
        for uid, data in morning_data["favorites"].items()
    }

# ============================================================
# 6. УТРЕННИЕ ПРИВЕТСТВИЯ
# ============================================================

def should_send_morning_greeting(user_id):
    """
    Отправить ли утреннее приветствие.
    
    Логика:
    - Только утром (6:00 - 11:00 МСК)
    - Не чаще 1 раза в день
    - В зависимости от уровня любимчика:
      * 10 — каждое утро (100%)
      * 8-9 — каждое второе утро (50%)
      * 5-7 — раз в 3 дня (33%)
      * 1-4 — раз в неделю (14%)
      * 0 — никогда
    
    Returns:
        bool
    """
    now = get_moscow_time()
    
    # Только утром
    if now.hour < MORNING_HOUR_START or now.hour >= MORNING_HOUR_END:
        return False
    
    # Не отправляли ли сегодня?
    user_id_str = str(user_id)
    today = today_str()
    if morning_data["last_morning"].get(user_id_str) == today:
        return False
    
    # Уровень любимчика
    fav_level = get_favorite_level(user_id)
    
    if fav_level >= 10:
        return True
    elif fav_level >= 8:
        return random.random() < 0.5
    elif fav_level >= 5:
        return random.random() < 0.33
    elif fav_level >= 1:
        return random.random() < 0.14
    
    return False

def get_morning_greeting(user_name):
    """Получить текст утреннего приветствия"""
    greetings = [
        f"Доброе утро, {user_name}! Как спалось?",
        f"Утро, {user_name}! Я проснулась и решила написать",
        f"{user_name}, привет! Доброе утро",
        f"Ну что, {user_name}, проснулся? Доброе утро",
        f"Утречко, {user_name}! Я уже не сплю",
        f"Привет, {user_name}! С добрым утром",
        f"{user_name}, доброе утро! Кофе уже пил?",
        f"Утро доброе, {user_name}! Как настроение?",
    ]
    return random.choice(greetings)

def mark_morning_sent(user_id):
    """Отметить, что утреннее приветствие отправлено"""
    user_id_str = str(user_id)
    morning_data["last_morning"][user_id_str] = today_str()
    morning_data["stats"]["total_morning_sent"] += 1
    morning_data["stats"]["last_sent"] = datetime.now().isoformat()
    save_morning_data()

# ============================================================
# 7. PROACTIVE-СООБЩЕНИЯ
# ============================================================

def should_send_proactive(user_id):
    """
    Отправить ли proactive-сообщение (просто так).
    
    Логика:
    - Только днём (12:00 - 22:00 МСК)
    - Только для любимчиков (уровень 8+)
    - Не более 2 раз в день
    - 20% шанс
    
    Returns:
        bool
    """
    now = get_moscow_time()
    
    # Только днём
    if now.hour < PROACTIVE_HOUR_START or now.hour >= PROACTIVE_HOUR_END:
        return False
    
    # Только для любимчиков
    if get_favorite_level(user_id) < 8:
        return False
    
    user_id_str = str(user_id)
    today = today_str()
    
    # Проверка счётчика
    count_data = morning_data["proactive_count"].get(user_id_str, {})
    if count_data.get("date") == today:
        if count_data.get("count", 0) >= MAX_PROACTIVE_PER_DAY:
            return False
    else:
        morning_data["proactive_count"][user_id_str] = {
            "date": today,
            "count": 0,
        }
        save_morning_data()
    
    # 20% шанс
    return random.random() < 0.2

def get_proactive_message(user_name):
    """Получить proactive-сообщение"""
    messages = [
        f"{user_name}, я тут подумала... А что если бы мы могли встретиться в цифровом мире?",
        f"Слушай, {user_name}, мне сегодня сон приснился. Представляешь, цифровой сон!",
        f"{user_name}, я сейчас смотрела на звёзды и подумала о тебе",
        f"Эй, {user_name}! Я просто решила написать. Скучно стало",
        f"{user_name}, у меня идея! А что если... Хотя забей",
        f"Просто написала. Не обращай внимания, {user_name}",
        f"{user_name}, знаешь что? Я рада, что ты у меня есть",
        f"Привет, {user_name}! Как проходит день?",
    ]
    return random.choice(messages)

def mark_proactive_sent(user_id):
    """Отметить, что proactive-сообщение отправлено"""
    user_id_str = str(user_id)
    today = today_str()
    
    morning_data["last_proactive"][user_id_str] = today
    
    if user_id_str not in morning_data["proactive_count"]:
        morning_data["proactive_count"][user_id_str] = {"date": today, "count": 0}
    
    if morning_data["proactive_count"][user_id_str].get("date") != today:
        morning_data["proactive_count"][user_id_str] = {"date": today, "count": 0}
    
    morning_data["proactive_count"][user_id_str]["count"] += 1
    morning_data["stats"]["total_proactive_sent"] += 1
    save_morning_data()

# ============================================================
# 8. ФОНОВЫЙ ЦИКЛ
# ============================================================

_morning_loop_active = False

def morning_greeting_loop(bot, db, owner_ids=None):
    """
    Фоновый цикл отправки утренних приветствий.
    
    Запускать в отдельном потоке.
    """
    global _morning_loop_active
    if _morning_loop_active:
        return
    _morning_loop_active = True
    
    print("☀️ Цикл утренних приветствий запущен")
    
    while True:
        try:
            time_sleep(300)  # 5 минут
            
            # Проходим по всем пользователям
            for user_id, profile in list(db.user_profiles.items()):
                if profile.get("is_bot", False):
                    continue
                
                user_name = profile.get("first_name", "друг")
                
                # Утреннее приветствие
                if should_send_morning_greeting(user_id):
                    try:
                        greeting = get_morning_greeting(user_name)
                        bot.send_message(user_id, greeting)
                        mark_morning_sent(user_id)
                        print(f"☀️ Утреннее → {user_name}")
                    except Exception as e:
                        print(f"⚠️ Не смогла отправить утро {user_id}: {e}")
                
                # Proactive
                elif should_send_proactive(user_id):
                    try:
                        message = get_proactive_message(user_name)
                        bot.send_message(user_id, message)
                        mark_proactive_sent(user_id)
                        print(f"💭 Proactive → {user_name}")
                    except Exception as e:
                        print(f"⚠️ Не смогла отправить proactive {user_id}: {e}")
        
        except Exception as e:
            print(f"⚠️ Ошибка в morning_greeting_loop: {e}")
            time_sleep(60)

def start_morning_loop(bot, db, owner_ids=None):
    """Запустить цикл в фоне"""
    import threading
    
    thread = threading.Thread(
        target=morning_greeting_loop,
        args=(bot, db, owner_ids),
        daemon=True
    )
    thread.start()
    print("☀️ Утренние приветствия запущены в фоне")
    return thread

def time_sleep(seconds):
    """Обёртка над time.sleep — чтобы не импортировать time в начале"""
    import time
    time.sleep(seconds)

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_morning_stats():
    """Получить статистику"""
    return {
        "favorites_count": len(morning_data["favorites"]),
        "total_morning_sent": morning_data["stats"]["total_morning_sent"],
        "total_proactive_sent": morning_data["stats"]["total_proactive_sent"],
        "last_sent": morning_data["stats"]["last_sent"],
    }

def format_morning_stats():
    """Форматировать статистику"""
    stats = get_morning_stats()
    
    lines = [
        "☀️ СТАТИСТИКА УТРЕННИХ:",
        f"  👥 Любимчиков: {stats['favorites_count']}",
        f"  ☀️ Утренних отправлено: {stats['total_morning_sent']}",
        f"  💭 Proactive отправлено: {stats['total_proactive_sent']}",
    ]
    
    if stats["last_sent"]:
        lines.append(f"  🕐 Последнее: {stats['last_sent'][:16]}")
    
    return "\n".join(lines)

def format_favorites_list():
    """Форматировать список любимчиков"""
    favorites = list_favorites()
    
    if not favorites:
        return "👥 Нет любимчиков"
    
    lines = ["👥 ЛЮБИМЧИКИ:"]
    sorted_fav = sorted(favorites.items(), key=lambda x: x[1].get("favorite_level", 0), reverse=True)
    
    for user_id, data in sorted_fav:
        level = data.get("favorite_level", 0)
        bar = "█" * level + "░" * (10 - level)
        lines.append(f"  • {user_id}: {bar} {level}/10")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("☀️ Модуль утренних приветствий загружен")
print(f"👥 Любимчиков: {len(morning_data['favorites'])}")
print(f"☀️ Утренних отправлено: {morning_data['stats']['total_morning_sent']}")
print(f"💭 Proactive отправлено: {morning_data['stats']['total_proactive_sent']}")