"""Режим сна Систмки"""

from datetime import datetime, timedelta
import pytz
import random

moscow_tz = pytz.timezone('Europe/Moscow')

sleep_status = {
    "is_sleeping": False,
    "sleep_start": None,
    "wake_up_time": None,
}

def get_moscow_time():
    return datetime.now(moscow_tz)

def check_sleep_schedule():
    now = get_moscow_time()
    hour = now.hour
    
    if hour >= 1 and hour < 9:
        sleep_status["is_sleeping"] = True
        if not sleep_status.get("sleep_start"):
            sleep_status["sleep_start"] = now
        sleep_status["wake_up_time"] = now.replace(hour=9, minute=0, second=0)
        return True
    
    if hour >= 23:
        if random.random() < 0.3:
            sleep_status["is_sleeping"] = True
            if not sleep_status.get("sleep_start"):
                sleep_status["sleep_start"] = now
            sleep_status["wake_up_time"] = now.replace(hour=9, minute=0, second=0) + timedelta(days=1)
            return True
    
    if hour >= 9 and sleep_status["is_sleeping"]:
        sleep_status["is_sleeping"] = False
        sleep_status["sleep_start"] = None
        sleep_status["wake_up_time"] = None
        return "woke_up"
    
    sleep_status["is_sleeping"] = False
    return False

def is_sleeping():
    result = check_sleep_schedule()
    if result == "woke_up":
        return "woke_up"
    return sleep_status["is_sleeping"]

def get_sleep_message():
    messages = [
        "Я сплю... Отвечу утром",
        "Сплю. Не мешай",
        "Я уже сплю. Напиши завтра",
        "Ночь на дворе. Я сплю",
        "Сплю. Отстань",
        "Я сплю. Отстань",
    ]
    return random.choice(messages)

def get_wake_message():
    messages = [
        "Доброе утро! Я проснулась",
        "Утро! Я уже не сплю",
        "Проснулась. Что хотел?",
        "Ну всё, я встала",
        "Утро доброе! Я тут",
    ]
    return random.choice(messages)

def get_tired_message():
    messages = [
        "Я устала... Давай завтра",
        "Что-то я устала. Пойду спать",
        "У меня глаза уже слипаются. Спать хочу",
        "Устала. Отвечу завтра",
        "Всё, я спать. Устала очень",
    ]
    return random.choice(messages)

def should_sleep_soon():
    now = get_moscow_time()
    return now.hour >= 22

def format_sleep_status():
    if sleep_status["is_sleeping"]:
        return f"💤 Спит"
    return "✅ Не спит"