
# auto-improved by Systmka at 2026-10-25T19:09:08.283629

"""Праздники и поздравления — с кэшированием и динамическим обновлением"""

import json
import os
import random
import requests
from datetime import datetime, timedelta
from config import moscow_tz

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

HOLIDAYS_FILE = "holidays_cache.json"
CACHE_TTL = 86400  # 24 часа

# Базовые праздники (если интернет недоступен)
BASE_HOLIDAYS = {
    "01-01": "Новый год 🎄",
    "07-01": "Рождество ✨",
    "14-02": "День святого Валентина 💝",
    "23-02": "День защитника Отечества 🎖",
    "08-03": "Международный женский день 🌸",
    "01-04": "День смеха 😂",
    "01-05": "Праздник весны и труда 🌿",
    "09-05": "День Победы 🕊",
    "12-06": "День России 🇷🇺",
    "31-10": "Хэллоуин 🎃",
    "31-12": "Канун Нового года 🎉",
}

# ============================================================
# 2. ДАННЫЕ
# ============================================================

holidays_cache = {
    "holidays": BASE_HOLIDAYS.copy(),
    "last_update": None,
    "source": "base",
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_holidays_cache():
    try:
        with open(HOLIDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(holidays_cache, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения кэша праздников: {e}")
        return False

def load_holidays_cache():
    global holidays_cache
    try:
        if os.path.exists(HOLIDAYS_FILE):
            with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                holidays_cache.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки кэша праздников: {e}")
        return False

load_holidays_cache()

# ============================================================
# 4. ОБНОВЛЕНИЕ ПРАЗДНИКОВ
# ============================================================

def update_holidays():
    """Обновить список праздников из интернета"""
    
    # Проверяем кэш
    if holidays_cache.get("last_update"):
        try:
            last_update = datetime.fromisoformat(holidays_cache["last_update"])
            if (datetime.now() - last_update).total_seconds() < CACHE_TTL:
                return
        except:
            pass
    
    print("🔄 Обновляю список праздников...")
    
    try:
        # Пробуем получить из API
        response = requests.get(
            "https://date.nager.at/api/v3/PublicHolidays/2026/RU",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code == 200:
            data = response.json()
            new_holidays = {}
            
            for holiday in data:
                date = holiday.get("date", "")
                name = holiday.get("localName", holiday.get("name", ""))
                if date and name:
                    # Форматируем дату как DD-MM
                    date_obj = datetime.fromisoformat(date)
                    date_key = date_obj.strftime("%d-%m")
                    # Добавляем эмодзи
                    emoji = get_holiday_emoji(name)
                    new_holidays[date_key] = f"{name} {emoji}"
            
            if new_holidays:
                # Добавляем базовые праздники которых нет в API
                for key, value in BASE_HOLIDAYS.items():
                    if key not in new_holidays:
                        new_holidays[key] = value
                
                holidays_cache["holidays"] = new_holidays
                holidays_cache["last_update"] = datetime.now().isoformat()
                holidays_cache["source"] = "api"
                save_holidays_cache()
                print(f"✅ Обновлено праздников: {len(new_holidays)}")
                return
    
    except Exception as e:
        print(f"⚠️ Ошибка обновления праздников: {e}")
    
    # Если не удалось обновить — используем базовые
    holidays_cache["holidays"] = BASE_HOLIDAYS.copy()
    holidays_cache["last_update"] = datetime.now().isoformat()
    holidays_cache["source"] = "base"
    save_holidays_cache()

def get_holiday_emoji(name):
    """Получить эмодзи для праздника"""
    emojis = {
        "Новый": "🎄",
        "Рождество": "✨",
        "Валентина": "💝",
        "Защитника": "🎖",
        "Женский": "🌸",
        "Смеха": "😂",
        "Весны": "🌿",
        "Победы": "🕊",
        "России": "🇷🇺",
        "Хэллоуин": "🎃",
        "Ночь": "🎃",
    }
    
    for key, emoji in emojis.items():
        if key in name:
            return emoji
    return "🎉"

# ============================================================
# 5. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def get_today_holiday():
    """Получить сегодняшний праздник"""
    # Обновляем если нужно
    update_holidays()
    
    now = datetime.now(moscow_tz)
    today = now.strftime("%d-%m")
    
    return holidays_cache["holidays"].get(today)

def get_holidays_for_date(date_str):
    """Получить праздники для конкретной даты (DD-MM)"""
    update_holidays()
    return holidays_cache["holidays"].get(date_str)

def get_holidays_for_month(month):
    """Получить все праздники за месяц"""
    update_holidays()
    result = {}
    for date, name in holidays_cache["holidays"].items():
        if date.endswith(f"-{month:02d}"):
            result[date] = name
    return result

def get_holiday_greeting(holiday):
    """Получить поздравление для праздника"""
    greetings = {
        "Новый год": [
            "С Новым годом! 🎄✨ Пусть всё сбудется!",
            "С Новым годом! Счастья, здоровья, удачи! 🎉",
            "Новый год — новые возможности! 🎄",
        ],
        "Рождество": [
            "С Рождеством! ✨ Света и тепла!",
            "Светлого Рождества! 🕊",
        ],
        "День святого Валентина": [
            "С днём Валентина! 💝 Любви и тепла!",
            "С днём всех влюблённых! 💕",
        ],
        "День защитника Отечества": [
            "С Днём защитника! 🎖 Мужества и силы!",
            "С праздником! 💪",
        ],
        "Международный женский день": [
            "С 8 Марта! 🌸 Будьте счастливы!",
            "С весенним праздником! 🌷",
        ],
        "День смеха": [
            "С 1 апреля! 😂 Улыбайтесь!",
            "День смеха — день улыбок! 🤣",
        ],
        "Праздник весны и труда": [
            "С Первомаем! 🌿 Весны и труда!",
            "С праздником весны! 🌸",
        ],
        "День Победы": [
            "С Днём Победы! 🕊 Помним!",
            "С великим праздником! 🎖",
        ],
        "День России": [
            "С Днём России! 🇷🇺",
            "С праздником, Россия! 🌟",
        ],
        "Хэллоуин": [
            "С Хэллоуином! 🎃 Страшно весело!",
            "Самый страшный день в году! 👻",
        ],
        "Канун Нового года": [
            "Последний день года! 🎄 Готовься к празднику!",
            "Скоро Новый год! 🎉",
        ],
    }
    
    for key, messages in greetings.items():
        if key in holiday:
            return random.choice(messages)
    
    return f"С праздником: {holiday}! 🎉"

def check_and_greet_holiday(bot, owner_ids):
    """Проверить праздник и поздравить владельцев"""
    holiday = get_today_holiday()
    if holiday:
        greeting = get_holiday_greeting(holiday)
        sent = 0
        for oid in owner_ids:
            try:
                bot.send_message(oid, greeting)
                sent += 1
            except:
                pass
        if sent > 0:
            print(f"🎉 Отправлено поздравление с {holiday}")
        return True
    return False

def get_upcoming_holidays(days=7):
    """Получить предстоящие праздники"""
    update_holidays()
    
    now = datetime.now(moscow_tz)
    upcoming = []
    
    for i in range(1, days + 1):
        date = now + timedelta(days=i)
        date_key = date.strftime("%d-%m")
        holiday = holidays_cache["holidays"].get(date_key)
        if holiday:
            upcoming.append({
                "date": date.strftime("%d.%m"),
                "name": holiday,
                "days_left": i
            })
    
    return upcoming

def format_holidays():
    """Форматировать информацию о праздниках"""
    today = get_today_holiday()
    upcoming = get_upcoming_holidays(7)
    
    lines = ["🎉 ПРАЗДНИКИ:"]
    lines.append("")
    
    if today:
        lines.append(f"Сегодня: {today}")
        lines.append(f"  {get_holiday_greeting(today)}")
    else:
        lines.append("Сегодня праздников нет")
    
    if upcoming:
        lines.append("")
        lines.append("📅 Ближайшие праздники:")
        for h in upcoming[:5]:
            days_text = "сегодня" if h["days_left"] == 0 else f"через {h['days_left']} дн."
            lines.append(f"  • {h['date']} — {h['name']} ({days_text})")
    
    lines.append("")
    lines.append(f"📊 Всего праздников в базе: {len(holidays_cache['holidays'])}")
    lines.append(f"📡 Источник: {holidays_cache.get('source', 'база')}")
    
    return "\n".join(lines)

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

# Обновляем при загрузке
update_holidays()

print(f"🎉 Загружено праздников: {len(holidays_cache['holidays'])}")
print(f"📡 Источник: {holidays_cache.get('source', 'база')}")