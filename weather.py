"""Погода — с прогнозом на завтра и поиском по области"""

import json
import os
import random
import requests
from datetime import datetime, timedelta
from consciousness import feel

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

WEATHER_CACHE_FILE = "weather_cache.json"
CACHE_TTL = 1800  # 30 минут
DEFAULT_CITY = "Moscow"

# ============================================================
# 2. КЭШИРОВАНИЕ
# ============================================================

weather_cache = {
    "current": None,
    "forecast": None,
    "cached_at": None,
    "city": DEFAULT_CITY
}

def load_weather_cache():
    global weather_cache
    try:
        if os.path.exists(WEATHER_CACHE_FILE):
            with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                weather_cache.update(loaded)
        return True
    except:
        return False

def save_weather_cache():
    try:
        with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(weather_cache, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

load_weather_cache()

# ============================================================
# 3. НОРМАЛИЗАЦИЯ ГОРОДА
# ============================================================

CITY_ALIASES = {
    "саратовская область": "Saratov",
    "саратов": "Saratov",
    "спб": "Saint Petersburg",
    "питер": "Saint Petersburg",
    "санкт-петербург": "Saint Petersburg",
    "мск": "Moscow",
    "москва": "Moscow",
    "екб": "Yekaterinburg",
    "екатеринбург": "Yekaterinburg",
    "нск": "Novosibirsk",
    "новосибирск": "Novosibirsk",
    "крд": "Krasnodar",
    "краснодар": "Krasnodar",
    "нн": "Nizhny Novgorod",
    "нижний новгород": "Nizhny Novgorod",
    "рнд": "Rostov-on-Don",
    "ростов": "Rostov-on-Don",
    "уфа": "Ufa",
    "кзн": "Kazan",
    "казань": "Kazan",
    "члб": "Chelyabinsk",
    "челябинск": "Chelyabinsk",
    "омск": "Omsk",
    "самара": "Samara",
    "пермь": "Perm",
}

def normalize_city(city):
    """Нормализовать название города"""
    city_lower = city.lower().strip()
    
    # Проверяем алиасы
    for alias, real in CITY_ALIASES.items():
        if alias in city_lower or city_lower == alias:
            return real
    
    # Если область — возвращаем центр
    if "область" in city_lower:
        # Берём первую часть
        parts = city_lower.split()
        for part in parts:
            if part not in ["область", "обл", "район", "р-н"]:
                if part in CITY_ALIASES:
                    return CITY_ALIASES[part]
                return part.capitalize()
    
    return city.capitalize()

# ============================================================
# 4. ПОЛУЧЕНИЕ ПОГОДЫ
# ============================================================

def get_weather(city=None, days=0):
    """
    Получить погоду
    days=0 — сегодня, days=1 — завтра, days=2 — послезавтра
    """
    if city is None:
        city = DEFAULT_CITY
    
    city = normalize_city(city)
    
    # Проверяем кэш
    cache_key = f"{city}_{days}"
    if weather_cache.get("cached_at"):
        try:
            cached_time = datetime.fromisoformat(weather_cache["cached_at"])
            if (datetime.now() - cached_time).total_seconds() < CACHE_TTL:
                if days == 0 and weather_cache.get("current"):
                    return weather_cache["current"]
                elif days > 0 and weather_cache.get("forecast"):
                    return weather_cache["forecast"]
        except:
            pass
    
    # Получаем погоду
    if days == 0:
        weather_data = _fetch_current_weather(city)
    else:
        weather_data = _fetch_forecast_weather(city, days)
    
    if weather_data:
        weather_cache["cached_at"] = datetime.now().isoformat()
        if days == 0:
            weather_cache["current"] = weather_data
        else:
            weather_cache["forecast"] = weather_data
        save_weather_cache()
    
    return weather_data

def _fetch_current_weather(city):
    """Запросить текущую погоду"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=ru"
        response = requests.get(url, timeout=15, headers={"User-Agent": "curl"})
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        current = data.get("current_condition", [{}])[0]
        
        if not current:
            return None
        
        return {
            "temp": int(current.get("temp_C", 0)),
            "weather": current.get("weatherDesc", [{}])[0].get("value", "Неизвестно"),
            "humidity": current.get("humidity", "0"),
            "wind": current.get("windspeedKmph", "0"),
            "city": city,
            "updated": datetime.now().isoformat(),
            "type": "current"
        }
    except:
        return None

def _fetch_forecast_weather(city, days):
    """Запросить прогноз на days дней вперёд"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=ru"
        response = requests.get(url, timeout=15, headers={"User-Agent": "curl"})
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        forecast = data.get("weather", [])
        
        if not forecast or len(forecast) <= days:
            return None
        
        day_data = forecast[days]
        
        # Берём среднюю температуру за день
        temp_min = int(day_data.get("mintempC", 0))
        temp_max = int(day_data.get("maxtempC", 0))
        temp_avg = (temp_min + temp_max) // 2
        
        weather_desc = day_data.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "Неизвестно")
        
        # Определяем дату
        date_str = day_data.get("date", "")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_label = date_obj.strftime("%d.%m")
        except:
            date_label = f"+{days} дн."
        
        return {
            "temp": temp_avg,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "weather": weather_desc,
            "city": city,
            "date": date_label,
            "updated": datetime.now().isoformat(),
            "type": "forecast",
            "days": days
        }
    except:
        return None

# ============================================================
# 5. НАСТРОЕНИЕ ОТ ПОГОДЫ
# ============================================================

def get_mood_from_weather(weather):
    if not weather:
        return "neutral"
    
    weather_desc = weather.get("weather", "").lower()
    temp = weather.get("temp", 0)
    
    if any(w in weather_desc for w in ["солн", "ясно", "sunny"]):
        return "happy"
    if any(w in weather_desc for w in ["дожд", "rain", "ливень"]):
        return "sad"
    if any(w in weather_desc for w in ["снег", "snow", "метель"]):
        return "excited"
    if any(w in weather_desc for w in ["гроз", "thunder", "молния"]):
        return "scared"
    if any(w in weather_desc for w in ["облач", "cloud", "пасмурно"]):
        return "calm"
    
    try:
        temp_int = int(temp)
        if temp_int > 30: return "hot"
        if temp_int > 25: return "warm"
        if temp_int < -10: return "cold"
        if temp_int < 0: return "cool"
    except:
        pass
    
    return "neutral"

def apply_weather_mood(bot, chat_id=None):
    weather = get_weather()
    if not weather:
        return None, None
    
    mood = get_mood_from_weather(weather)
    
    mood_to_emotion = {
        "happy": ("happiness", 2),
        "sad": ("sadness", 2),
        "excited": ("excitement", 2),
        "calm": ("happiness", 1),
        "cold": ("nostalgia", 1),
        "hot": ("tiredness", 1),
        "scared": ("fear", 1),
    }
    
    if mood in mood_to_emotion:
        emotion, value = mood_to_emotion[mood]
        feel(emotion, value)
    
    return mood, weather

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_weather(weather):
    if not weather:
        return "❌ Не удалось получить погоду"
    
    city = weather.get("city", "Неизвестно")
    temp = weather.get("temp", "?")
    desc = weather.get("weather", "Неизвестно")
    humidity = weather.get("humidity", "?")
    wind = weather.get("wind", "?")
    
    if weather.get("type") == "forecast":
        date = weather.get("date", "")
        temp_min = weather.get("temp_min", "?")
        temp_max = weather.get("temp_max", "?")
        return f"""🌤 ПРОГНОЗ ПОГОДЫ В {city.upper()} НА {date}:

🌡 Температура: от {temp_min}°C до {temp_max}°C (средняя {temp}°C)
☁️ {desc}
💧 Влажность: {humidity}%
💨 Ветер: {wind} км/ч

🕐 Обновлено: {weather.get('updated', '?')[:16]}"""
    
    return f"""🌤 ПОГОДА В {city.upper()}:

🌡 Температура: {temp}°C
☁️ {desc}
💧 Влажность: {humidity}%
💨 Ветер: {wind} км/ч

🕐 Обновлено: {weather.get('updated', '?')[:16]}"""

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🌤 Модуль погоды загружен (с прогнозом на завтра)")