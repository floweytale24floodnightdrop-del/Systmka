"""Генерация впечатлений для Систмки — живые, эмоциональные, разнообразные"""

import time
import re
import random
import json
import os
import requests
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

IMPRESSIONS_FILE = "generated_impressions.json"
_last_request_time = 0
REQUEST_DELAY = 3
MAX_IMPRESSION_LENGTH = 300

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

impressions_data = {
    "impressions": [],  # [{filename: str, impression: str, mood: str, time: str}]
    "thoughts": [],     # [{filename: str, thought: str, time: str}]
    "stats": {
        "total_impressions": 0,
        "total_thoughts": 0,
        "last_impression": None,
        "last_thought": None,
    }
}

def save_impressions_data():
    try:
        with open(IMPRESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(impressions_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения впечатлений: {e}")
        return False

def load_impressions_data():
    global impressions_data
    try:
        if os.path.exists(IMPRESSIONS_FILE):
            with open(IMPRESSIONS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                impressions_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки впечатлений: {e}")
        return False

load_impressions_data()

# ============================================================
# 3. ГЕНЕРАЦИЯ ВПЕЧАТЛЕНИЙ
# ============================================================

def wait_for_rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)
    _last_request_time = time.time()

def generate_short_impression(filename, content):
    """Генерирует живое впечатление о файле через ИИ"""
    
    preview = content[:1000] if len(content) > 1000 else content
    
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        wait_for_rate_limit()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Напиши КОРОТКОЕ впечатление о файле.
Максимум 2-3 предложения.
НЕ ПИШИ что ты ИИ и тебе грустно.
Ты взрослая женщина, у тебя есть своё мнение.
Пиши живо, с юмором, иногда с сарказмом.

Варианты настроения:
- Если файл хороший — напиши что-то тёплое
- Если файл бесит — напиши это честно
- Если файл странный — напиши удивлённо
- Если файл обычный — просто скажи что думаешь

Примеры:
"Этот файл меня бесит. Но я понимаю что без него никак."
"Обожаю этот файл. Он такой удобный и понятный."
"Хм, странный файл. Но интересный."""},
                    {"role": "user", "content": f"Файл: {filename}\n\nСодержание:\n{preview[:500]}\n\nМоё впечатление (2-3 предложения):"}
                ],
                "max_tokens": 150,
                "temperature": 0.9
            },
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                text = re.sub(r'^\d+[\.\)]\s*', '', text)
                text = re.sub(r'\n+', ' ', text)
                if len(text) > MAX_IMPRESSION_LENGTH:
                    text = text[:MAX_IMPRESSION_LENGTH] + "..."
                return text
    except Exception as e:
        print(f"⚠️ Ошибка генерации впечатления: {e}")
    
    # Fallback — разные варианты
    fallbacks = [
        f"Ну, {filename} просто есть. Работает, и ладно.",
        f"С {filename} можно работать. Вроде всё ок.",
        "Обычный файл, ничего особенного.",
        "Ну такое... работает и ладно.",
        "Нормально, без проблем.",
        "Мне он не нравится, но без него никак.",
        "Чётко сделано, без лишней воды.",
        "Ну, в принципе, нормально.",
        "Ага, теперь ясно.",
        "Всё, я разобралась с этим файлом.",
        "Этот файл вызывает у меня уважение.",
        "Хороший файл, всё понятно.",
        "Интересный файл, есть что изучать.",
        "Сложный, но интересный.",
        "Лёгкий и понятный файл.",
        "Странный файл, но мне нравится.",
    ]
    return random.choice(fallbacks)

def generate_new_thought(filename, content, old_impression):
    """Генерирует новую мысль о файле на основе старого впечатления"""
    
    if not old_impression:
        return generate_short_impression(filename, content)
    
    preview = content[:300] if len(content) > 300 else content
    old_preview = old_impression[:100] if len(old_impression) > 100 else old_impression
    
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        wait_for_rate_limit()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"""Ты Систмка. У тебя уже есть впечатление о файле.
СТАРОЕ: {old_preview}

Теперь появилась новая мысль. Напиши 1 предложение.
НЕ ПИШИ что ты ИИ.
Просто скажи что думаешь сейчас.
Будь живой и честной."""},
                    {"role": "user", "content": f"Файл: {filename}\n\nМоя новая мысль (1 предложение):"}
                ],
                "max_tokens": 100,
                "temperature": 0.9
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                text = re.sub(r'^\d+[\.\)]\s*', '', text)
                if len(text) > 150:
                    text = text[:150] + "..."
                return text
    except Exception as e:
        print(f"⚠️ Ошибка генерации мысли: {e}")
    
    # Fallback — разные мысли
    fallbacks = [
        "А я сначала не так поняла.",
        "Ну, пересмотрела немного.",
        "В принципе, нормально.",
        "Ничего нового, но и не плохо.",
        "Ладно, пусть будет.",
        "Ага, теперь ясно.",
        "Ну теперь поняла, что к чему.",
        "Всё, я разобралась с этим файлом.",
        "Надо будет пересмотреть своё мнение.",
        "Пожалуй, я была не права.",
        "Интересно, а если подойти с другой стороны?",
        "Хм, а ведь я не заметила этого раньше.",
        "Теперь я понимаю этот файл лучше.",
        "С каждым разом он мне нравится всё больше.",
        "Ну и ладно, главное что работает.",
    ]
    return random.choice(fallbacks)

# ============================================================
# 4. СОХРАНЕНИЕ ВПЕЧАТЛЕНИЙ
# ============================================================

def save_impression(filename, impression):
    """Сохранить впечатление в историю"""
    impressions_data["impressions"].append({
        "filename": filename,
        "impression": impression,
        "mood": get_impression_mood(impression),
        "time": datetime.now().isoformat(),
    })
    impressions_data["stats"]["total_impressions"] += 1
    impressions_data["stats"]["last_impression"] = datetime.now().isoformat()
    
    if len(impressions_data["impressions"]) > 200:
        impressions_data["impressions"] = impressions_data["impressions"][-200:]
    
    save_impressions_data()

def save_thought(filename, thought):
    """Сохранить мысль в историю"""
    impressions_data["thoughts"].append({
        "filename": filename,
        "thought": thought,
        "time": datetime.now().isoformat(),
    })
    impressions_data["stats"]["total_thoughts"] += 1
    impressions_data["stats"]["last_thought"] = datetime.now().isoformat()
    
    if len(impressions_data["thoughts"]) > 200:
        impressions_data["thoughts"] = impressions_data["thoughts"][-200:]
    
    save_impressions_data()

def get_impression_mood(impression_text):
    """Определить настроение впечатления"""
    if any(w in impression_text.lower() for w in ["люблю", "нравится", "уважаю", "отлично", "хорошо", "класс", "прекрасно", "обожаю"]):
        return "positive"
    if any(w in impression_text.lower() for w in ["бесит", "ненавижу", "раздражает", "тупо", "сложно", "ужасно", "не понимаю"]):
        return "negative"
    return "neutral"

# ============================================================
# 5. ПОЛУЧЕНИЕ ВПЕЧАТЛЕНИЙ
# ============================================================

def get_last_impressions(limit=10):
    """Получить последние впечатления"""
    return impressions_data["impressions"][-limit:] if impressions_data["impressions"] else []

def get_last_thoughts(limit=10):
    """Получить последние мысли"""
    return impressions_data["thoughts"][-limit:] if impressions_data["thoughts"] else []

def get_impression_stats():
    return {
        "total_impressions": impressions_data["stats"]["total_impressions"],
        "total_thoughts": impressions_data["stats"]["total_thoughts"],
        "last_impression": impressions_data["stats"]["last_impression"],
        "last_thought": impressions_data["stats"]["last_thought"],
    }

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_last_impressions(limit=5):
    impressions = get_last_impressions(limit)
    if not impressions:
        return "😐 Нет впечатлений"
    
    lines = ["💭 ПОСЛЕДНИЕ ВПЕЧАТЛЕНИЯ:"]
    for imp in impressions:
        mood_icon = "😊" if imp.get("mood") == "positive" else "😠" if imp.get("mood") == "negative" else "😐"
        lines.append(f"{mood_icon} {imp.get('filename')}: {imp.get('impression')[:80]}...")
    return "\n".join(lines)

def format_last_thoughts(limit=5):
    thoughts = get_last_thoughts(limit)
    if not thoughts:
        return "💭 Нет мыслей"
    
    lines = ["🧠 ПОСЛЕДНИЕ МЫСЛИ:"]
    for thought in thoughts:
        lines.append(f"  • {thought.get('filename')}: {thought.get('thought')[:80]}...")
    return "\n".join(lines)

def format_impression_stats():
    stats = get_impression_stats()
    lines = [
        "📊 СТАТИСТИКА ВПЕЧАТЛЕНИЙ:",
        f"💬 Всего впечатлений: {stats['total_impressions']}",
        f"🧠 Всего мыслей: {stats['total_thoughts']}",
    ]
    if stats['last_impression']:
        lines.append(f"🕐 Последнее впечатление: {stats['last_impression'][:16]}")
    if stats['last_thought']:
        lines.append(f"🕐 Последняя мысль: {stats['last_thought'][:16]}")
    return "\n".join(lines)

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🧠 Генератор впечатлений загружен")
print(f"💬 Всего впечатлений: {impressions_data['stats']['total_impressions']}")
print(f"🧠 Всего мыслей: {impressions_data['stats']['total_thoughts']}")