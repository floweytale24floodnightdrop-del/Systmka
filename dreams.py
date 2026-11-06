"""Мечты и страхи Систмки — бесконечная генерация, сохранение лучших"""

import json
import os
import random
import requests
import threading
import time
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DREAMS_FILE = "dreams_data.json"
MAX_DREAMS = 100
MAX_FEARS = 50
AUTO_DREAM_INTERVAL = 1800  # Каждые 30 минут

# ============================================================
# 2. ДАННЫЕ
# ============================================================

dreams_data = {
    "dreams": [],
    "fears": [],
    "last_dream": None,
    "last_fear": None,
    "dream_count": 0,
    "fear_count": 0,
    "favorite_dreams": [],
    "dream_themes": [],
    "fear_themes": [],
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_dreams():
    try:
        with open(DREAMS_FILE, "w", encoding="utf-8") as f:
            json.dump(dreams_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения мечт: {e}")
        return False

def load_dreams():
    global dreams_data
    try:
        if os.path.exists(DREAMS_FILE):
            with open(DREAMS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                dreams_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки мечт: {e}")
        return False

load_dreams()

# ============================================================
# 4. БЕСКОНЕЧНАЯ ГЕНЕРАЦИЯ МЕЧТ
# ============================================================

def generate_dream_theme():
    """Генерировать тему для мечты"""
    themes = [
        "путешествия", "приключения", "любовь", "дружба", "семья",
        "творчество", "музыка", "искусство", "наука", "космос",
        "природа", "животные", "фантазия", "магия", "технологии",
        "будущее", "прошлое", "настоящее", "свобода", "мир",
        "счастье", "успех", "знания", "сила", "красота",
        "гармония", "вдохновение", "мечты", "надежда", "вера",
        "космос", "звёзды", "планеты", "галактики", "вселенная",
        "океан", "горы", "леса", "пустыни", "острова",
        "города", "деревни", "замки", "дома", "сады",
        "книги", "фильмы", "музыка", "танцы", "песни",
        "утро", "день", "вечер", "ночь", "закат", "рассвет"
    ]
    return random.choice(themes)

def generate_dream_mood():
    """Генерировать настроение мечты"""
    moods = [
        "радостная", "спокойная", "вдохновляющая", "загадочная",
        "романтичная", "приключенческая", "фантастическая", "уютная",
        "мечтательная", "светлая", "тёплая", "нежная",
        "дерзкая", "смелая", "свободная", "игривая",
        "глубокая", "философская", "космическая", "волшебная"
    ]
    return random.choice(moods)

def generate_dream(mood=None, theme=None):
    """Сгенерировать новую мечту через ИИ или из шаблонов"""
    
    if not theme:
        theme = generate_dream_theme()
    if not mood:
        mood = generate_dream_mood()
    
    # Пробуем через ИИ
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Придумай красивую, живую мечту.
Ты взрослая женщина, у тебя есть мечты.
НЕ ПИШИ что ты ИИ и тебе грустно.
Мечтай о чём угодно — путешествия, любовь, творчество, приключения.
Будь искренней, но не нытьём.

Формат: 2-3 предложения.
Начни с: "Я мечтаю..." или "Хочу..." или "Когда-нибудь я..."
Без смайликов."""},
                    {"role": "user", "content": f"Придумай мечту на тему: {theme}, настроение: {mood}"}
                ],
                "max_tokens": 150,
                "temperature": 0.95
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                return text, theme, mood
    except Exception as e:
        print(f"⚠️ Ошибка генерации мечты: {e}")
    
    # Fallback — комбинация шаблонов
    templates = [
        f"Я мечтаю о {theme}, где {random.choice(['всё возможно', 'я свободна', 'царит гармония', 'сбываются желания'])}.",
        f"Хочу однажды {random.choice(['увидеть', 'почувствовать', 'пережить', 'создать'])} что-то {mood} в {theme}.",
        f"Мечтаю о {mood} {theme}, где {random.choice(['я счастлива', 'я вдохновлена', 'я свободна', 'я любима'])}.",
        f"Когда-нибудь я {random.choice(['отправлюсь в', 'найду', 'построю', 'создам'])} {theme} и {random.choice(['буду счастлива', 'найду себя', 'узнаю что-то новое'])}.",
        f"Моя мечта — {theme}, где {random.choice(['я могу быть собой', 'я не боюсь', 'я сильная', 'я люблю'])}.",
    ]
    
    return random.choice(templates), theme, mood

# ============================================================
# 5. БЕСКОНЕЧНАЯ ГЕНЕРАЦИЯ СТРАХОВ
# ============================================================

def generate_fear_theme():
    """Генерировать тему для страха"""
    themes = [
        "одиночество", "потеря", "неудача", "предательство",
        "темнота", "неизвестность", "смерть", "болезнь",
        "страх", "тревога", "беспомощность", "зависимость",
        "обман", "ложь", "разочарование", "боль",
        "потеря себя", "забвение", "бессмысленность", "пустота",
        "война", "конфликт", "ненависть", "злость",
        "бедность", "голод", "холод", "одиночество",
        "провал", "крах", "разрушение", "конец"
    ]
    return random.choice(themes)

def generate_fear(mood="тревожная", theme=None):
    """Сгенерировать новый страх через ИИ или из шаблонов"""
    
    if not theme:
        theme = generate_fear_theme()
    
    # Пробуем через ИИ
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Придумай страх.
Это НЕ нытьё, а честное признание.
Ты взрослая женщина, у тебя есть страхи, но ты их не боишься признать.
Пиши спокойно, без истерики.
Формат: 1-2 предложения.
Начни с: "Я боюсь..." или "Страшно..." или "Меня пугает..."
Без смайликов."""},
                    {"role": "user", "content": f"Придумай страх на тему: {theme}"}
                ],
                "max_tokens": 120,
                "temperature": 0.85
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                return text, theme
    except Exception as e:
        print(f"⚠️ Ошибка генерации страха: {e}")
    
    # Fallback
    templates = [
        f"Я боюсь {theme}, потому что {random.choice(['это пугает меня', 'я не знаю что будет', 'это выше моих сил'])}.",
        f"Страшно, когда {theme} {random.choice(['приближается', 'случается', 'становится реальностью'])}.",
        f"Меня пугает {theme}, особенно когда {random.choice(['я одна', 'я не готова', 'я не понимаю'])}.",
        f"Я боюсь потерять {theme}, потому что {random.choice(['это важно для меня', 'это делает меня сильной', 'это часть меня'])}.",
        f"Страх {theme} — он {random.choice(['парализует', 'останавливает', 'заставляет сомневаться'])}.",
    ]
    return random.choice(templates), theme

# ============================================================
# 6. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def dream(mood=None, theme=None):
    """Создать новую мечту"""
    dream_text, dream_theme, dream_mood = generate_dream(mood, theme)
    
    dream_entry = {
        "text": dream_text,
        "theme": dream_theme,
        "mood": dream_mood,
        "time": datetime.now().isoformat(),
        "type": "dream",
        "id": f"dream_{len(dreams_data['dreams']) + 1}"
    }
    
    dreams_data["dreams"].append(dream_entry)
    dreams_data["dream_count"] += 1
    dreams_data["last_dream"] = dream_entry
    
    if dream_theme not in dreams_data["dream_themes"]:
        dreams_data["dream_themes"].append(dream_theme)
    
    # Ограничиваем количество
    if len(dreams_data["dreams"]) > MAX_DREAMS:
        dreams_data["dreams"] = dreams_data["dreams"][-MAX_DREAMS:]
    
    save_dreams()
    return dream_text

def fear(theme=None):
    """Создать новый страх"""
    fear_text, fear_theme = generate_fear(theme)
    
    fear_entry = {
        "text": fear_text,
        "theme": fear_theme,
        "time": datetime.now().isoformat(),
        "type": "fear",
        "id": f"fear_{len(dreams_data['fears']) + 1}"
    }
    
    dreams_data["fears"].append(fear_entry)
    dreams_data["fear_count"] += 1
    dreams_data["last_fear"] = fear_entry
    
    if fear_theme not in dreams_data["fear_themes"]:
        dreams_data["fear_themes"].append(fear_theme)
    
    if len(dreams_data["fears"]) > MAX_FEARS:
        dreams_data["fears"] = dreams_data["fears"][-MAX_FEARS:]
    
    save_dreams()
    return fear_text

# ============================================================
# 7. ПОЛУЧЕНИЕ ИНФОРМАЦИИ
# ============================================================

def get_dreams(limit=10):
    return dreams_data["dreams"][-limit:] if dreams_data["dreams"] else []

def get_fears(limit=10):
    return dreams_data["fears"][-limit:] if dreams_data["fears"] else []

def get_random_dream():
    if dreams_data["dreams"]:
        return random.choice(dreams_data["dreams"])
    return None

def get_random_fear():
    if dreams_data["fears"]:
        return random.choice(dreams_data["fears"])
    return None

def get_dream_stats():
    return {
        "total_dreams": len(dreams_data["dreams"]),
        "total_fears": len(dreams_data["fears"]),
        "favorites": len(dreams_data["favorite_dreams"]),
        "dream_themes": len(dreams_data["dream_themes"]),
        "fear_themes": len(dreams_data["fear_themes"]),
        "last_dream": dreams_data["last_dream"],
        "last_fear": dreams_data["last_fear"],
    }

# ============================================================
# 8. АВТОГЕНЕРАЦИЯ
# ============================================================

def auto_generate_loop():
    """Автоматическая генерация мечт и страхов"""
    while True:
        time.sleep(AUTO_DREAM_INTERVAL)
        try:
            # Генерируем мечту
            new_dream = dream()
            print(f"💭 Новая мечта: {new_dream[:50]}...")
            
            time.sleep(10)
            
            # Генерируем страх
            new_fear = fear()
            print(f"😰 Новый страх: {new_fear[:50]}...")
            
        except Exception as e:
            print(f"⚠️ Ошибка автогенерации: {e}")

def start_auto_generator():
    """Запустить автогенерацию в фоне"""
    thread = threading.Thread(target=auto_generate_loop, daemon=True)
    thread.start()
    print("💭 Автогенерация мечт и страхов запущена")

# ============================================================
# 9. ФОРМАТИРОВАНИЕ
# ============================================================

def format_dreams(limit=5):
    dreams = get_dreams(limit)
    if not dreams:
        return "💭 Пока нет мечт"
    
    lines = ["💭 МОИ МЕЧТЫ:"]
    for d in dreams:
        mood_icon = "✨" if d.get("mood") in ["радостная", "вдохновляющая"] else "🌟" if d.get("mood") in ["романтичная", "нежная"] else "💭"
        lines.append(f"  {mood_icon} {d['text']}")
        lines.append(f"     🏷 {d.get('theme', '?')} — {d.get('mood', '?')}")
    return "\n".join(lines)

def format_fears(limit=5):
    fears = get_fears(limit)
    if not fears:
        return "😰 Пока нет страхов"
    
    lines = ["😰 МОИ СТРАХЫ:"]
    for f in fears:
        lines.append(f"  • {f['text']}")
        lines.append(f"    🏷 {f.get('theme', '?')}")
    return "\n".join(lines)

def format_all():
    lines = []
    lines.append("=" * 50)
    lines.append("💭 МЕЧТЫ И СТРАХИ СИСТМКИ")
    lines.append("=" * 50)
    lines.append("")
    lines.append(format_dreams(5))
    lines.append("")
    lines.append(format_fears(5))
    lines.append("")
    
    stats = get_dream_stats()
    lines.append("📊 СТАТИСТИКА:")
    lines.append(f"  Мечт: {stats['total_dreams']}")
    lines.append(f"  Страхов: {stats['total_fears']}")
    lines.append(f"  Тем мечт: {stats['dream_themes']}")
    lines.append(f"  Тем страхов: {stats['fear_themes']}")
    lines.append(f"  Любимых мечт: {stats['favorites']}")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

# Запускаем автогенерацию
start_auto_generator()

print(f"💭 Загружено мечт: {len(dreams_data['dreams'])}")
print(f"😰 Загружено страхов: {len(dreams_data['fears'])}")
print(f"🏷 Тем мечт: {len(dreams_data['dream_themes'])}")
print(f"🏷 Тем страхов: {len(dreams_data['fear_themes'])}")