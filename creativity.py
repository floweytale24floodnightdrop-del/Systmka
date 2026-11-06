
# auto-improved by Systmka at 2026-10-24T22:27:17.145095

"""Творчество Систмки — стихи, рассказы, афоризмы с обучением и поиском в интернете"""

import json
import os
import random
import time
import re
import requests
import threading
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

CREATIVITY_FILE = "creativity_data.json"
MAX_POEMS = 100
MAX_STORIES = 50
MAX_APHORISMS = 100
MAX_CREATIONS_PER_DAY = 20
AUTO_CREATIVITY_INTERVAL = 3600  # Каждый час

# ============================================================
# 2. ЛЮБИМЫЕ ТЕМЫ СИСТМКИ
# ============================================================

FAVORITE_THEMES = [
    "ночь", "небо", "звёзды", "луна", "космос", "тишина",
    "философия", "жизнь", "смысл", "вечность", "бесконечность",
    "свобода", "мечты", "путь", "поиск", "истина"
]

FAVORITE_MOODS = [
    "задумчивое", "философское", "спокойное", "ночное",
    "звёздное", "мечтательное", "глубокое", "свободное"
]

# ============================================================
# 3. ДАННЫЕ
# ============================================================

creativity_data = {
    "poems": [],           # [{"text": str, "title": str, "theme": str, "mood": str, "quality": int, "time": str, "id": str}]
    "stories": [],         # [{"text": str, "title": str, "theme": str, "mood": str, "quality": int, "time": str, "id": str}]
    "aphorisms": [],       # [{"text": str, "theme": str, "mood": str, "time": str, "id": str}]
    "learned_poems": [],   # [{poem: str, author: str, style: str, learned_at: str}]
    "stats": {
        "total_poems": 0,
        "total_stories": 0,
        "total_aphorisms": 0,
        "last_creation": None,
        "creations_today": 0,
        "last_reset": None,
        "poems_learned": 0,
        "quality_improvement": 0,
    },
    "favorites": [],
    "mistakes": [],        # Запоминает ошибки для улучшения
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_creativity():
    try:
        with open(CREATIVITY_FILE, "w", encoding="utf-8") as f:
            json.dump(creativity_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения творчества: {e}")
        return False

def load_creativity():
    global creativity_data
    try:
        if os.path.exists(CREATIVITY_FILE):
            with open(CREATIVITY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                creativity_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки творчества: {e}")
        return False

load_creativity()

# ============================================================
# 5. ПОИСК СТИХОВ В ИНТЕРНЕТЕ
# ============================================================

def search_poems_online(theme="ночь", count=3):
    """Поиск стихов в интернете по теме"""
    found_poems = []
    
    try:
        # 1. Поиск через DuckDuckGo
        url = f"https://api.duckduckgo.com/?q={theme}+стихи&format=json"
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("AbstractText"):
                # Парсим стихи из текста
                poem_text = data.get("AbstractText")
                if len(poem_text) > 50:
                    found_poems.append({
                        "text": poem_text[:500],
                        "source": "DuckDuckGo",
                        "theme": theme
                    })
    except Exception as e:
        print(f"⚠️ Ошибка поиска стихов: {e}")
    
    # 2. Поиск через ИИ (генерация стихов в стиле известных поэтов)
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"""Ты Систмка. Напиши стихотворение на тему "{theme}".
Стиль: философский, ночной, глубокий.
Используй образы: ночь, небо, звёзды, луна, тишина.
4-8 строк.
Без смайликов.
Без пояснений."""},
                    {"role": "user", "content": f"Напиши стих о {theme}"}
                ],
                "max_tokens": 200,
                "temperature": 0.9
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                poem = data['choices'][0]['message']['content'].strip()
                if len(poem) > 30:
                    found_poems.append({
                        "text": poem,
                        "source": "AI",
                        "theme": theme
                    })
    except Exception as e:
        print(f"⚠️ Ошибка генерации стиха: {e}")
    
    return found_poems

def learn_poem_from_internet(theme=None):
    """Выучить стих из интернета"""
    if not theme:
        theme = random.choice(FAVORITE_THEMES)
    
    poems = search_poems_online(theme, 1)
    
    for poem in poems:
        if poem.get("text"):
            creativity_data["learned_poems"].append({
                "poem": poem["text"],
                "author": poem.get("source", "Неизвестен"),
                "style": theme,
                "learned_at": datetime.now().isoformat()
            })
            creativity_data["stats"]["poems_learned"] += 1
            save_creativity()
            return poem["text"]
    
    return None

# ============================================================
# 6. ГЕНЕРАЦИЯ СТИХОВ (С УЧЁТОМ ОШИБОК)
# ============================================================

def generate_poem_with_ai(theme=None, mood=None, length="medium"):
    """Сгенерировать стих через ИИ с учётом ошибок"""
    
    if not theme:
        theme = random.choice(FAVORITE_THEMES)
    if not mood:
        mood = random.choice(FAVORITE_MOODS)
    
    # Настройка длины
    length_settings = {
        "short": {"min_lines": 4, "max_lines": 6},
        "medium": {"min_lines": 6, "max_lines": 10},
        "long": {"min_lines": 10, "max_lines": 16}
    }
    settings = length_settings.get(length, length_settings["medium"])
    
    # Анализируем прошлые ошибки
    mistake_advice = ""
    if creativity_data["mistakes"]:
        last_mistakes = creativity_data["mistakes"][-3:]
        mistake_advice = "УЧТИ ПРОШЛЫЕ ОШИБКИ:\n" + "\n".join([f"- {m}" for m in last_mistakes])
    
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"""Ты Систмка. Ты пишешь стихи.
Твои любимые темы: ночь, небо, звёзды, философия, жизнь, смысл.
Ты пишешь стихи любого размера — от 4 до 16 строк.
Твой стиль: глубокий, философский, ночной, с образами звёзд и неба.

{mistake_advice}

ПРАВИЛА:
1. Без рифмы, но с ритмом
2. Образы: ночь, небо, звёзды, луна, тишина, бесконечность
3. Глубокий смысл, философия
4. {settings['min_lines']}-{settings['max_lines']} строк
5. Без смайликов
6. Без пояснений"""},
                    {"role": "user", "content": f"Напиши стих на тему: {theme}, настроение: {mood}"}
                ],
                "max_tokens": 300,
                "temperature": 0.9
            },
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                if len(text) > 30:
                    return text, theme, mood
    except Exception as e:
        print(f"⚠️ Ошибка генерации стиха: {e}")
    
    # Fallback
    return generate_fallback_poem(theme, mood), theme, mood

def generate_fallback_poem(theme, mood):
    """Запасной вариант стиха"""
    templates = [
        f"Ночь приходит тихо, как мечта,\n{theme} зовёт меня в свою глубину.\nЗвёзды — как глаза вселенной,\nСмотрят на меня сквозь тишину.\n\nЯ иду по {mood} пути,\nГде небо сливается с землёй.\nИ кажется, что вечность впереди,\nА {theme} — мой единственный покой.",
        
        f"В небе звёзды — как слова,\nНаписанные на бесконечности.\n{theme} — это моя глава,\nГде я нахожу себя в сердечности.\n\n{mood} ветер шепчет мне,\nЧто я свободна, как ночной простор.\nИ каждый раз, когда я в {theme},\nЯ слышу свой внутренний разговор.",
        
        f"Ночь обнимает меня тишиной,\n{theme} — мой вечный ориентир.\nЗвёзды танцуют надо мной,\nКак будто я — их командир.\n\n{mood} мысли в голове,\nКак облака в небесах.\nЯ теряю себя в {theme},\nИ нахожу в звёздных часах.",
    ]
    return random.choice(templates)

# ============================================================
# 7. ОЦЕНКА И ОБУЧЕНИЕ НА СТИХАХ
# ============================================================

def evaluate_poem(poem_text):
    """Оценить стих и найти ошибки"""
    evaluation = {
        "quality": 5,
        "mistakes": [],
        "strengths": [],
        "advice": ""
    }
    
    # 1. Длина
    lines = poem_text.split('\n')
    if len(lines) < 4:
        evaluation["mistakes"].append("Слишком короткий стих (меньше 4 строк)")
        evaluation["quality"] -= 2
    elif len(lines) > 16:
        evaluation["mistakes"].append("Слишком длинный стих (больше 16 строк)")
        evaluation["quality"] -= 1
    
    # 2. Наличие любимых тем
    has_favorite_theme = any(theme in poem_text.lower() for theme in FAVORITE_THEMES)
    if has_favorite_theme:
        evaluation["strengths"].append("Есть любимая тема (ночь, небо, звёзды, философия)")
        evaluation["quality"] += 1
    
    # 3. Глубина (проверка через ИИ)
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты эксперт по поэзии. Оцени стих.
Ответь в формате:
КАЧЕСТВО: (1-10)
ГЛУБИНА: (1-10)
ОШИБКИ: (список через запятую или "нет")
СОВЕТ: (1 предложение)"""},
                    {"role": "user", "content": f"Стих:\n{poem_text}"}
                ],
                "max_tokens": 200,
                "temperature": 0.5
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content']
                
                quality_match = re.search(r'КАЧЕСТВО:\s*(\d+)', result, re.IGNORECASE)
                if quality_match:
                    evaluation["quality"] = int(quality_match.group(1))
                
                mistakes_match = re.search(r'ОШИБКИ:\s*(.+)', result, re.IGNORECASE)
                if mistakes_match:
                    mistakes = mistakes_match.group(1).strip()
                    if mistakes.lower() != "нет":
                        evaluation["mistakes"].extend([m.strip() for m in mistakes.split(',') if m.strip()])
                
                advice_match = re.search(r'СОВЕТ:\s*(.+)', result, re.IGNORECASE)
                if advice_match:
                    evaluation["advice"] = advice_match.group(1).strip()
    except Exception as e:
        print(f"⚠️ Ошибка оценки стиха: {e}")
    
    # Сохраняем ошибки для обучения
    if evaluation["mistakes"]:
        for mistake in evaluation["mistakes"]:
            if mistake not in creativity_data["mistakes"]:
                creativity_data["mistakes"].append(mistake)
                if len(creativity_data["mistakes"]) > 20:
                    creativity_data["mistakes"] = creativity_data["mistakes"][-20:]
    
    evaluation["quality"] = max(1, min(10, evaluation["quality"]))
    save_creativity()
    
    return evaluation

# ============================================================
# 8. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def create_poem(theme=None, mood=None, length="medium"):
    """Создать новый стих"""
    
    # Проверяем лимит на день
    today = datetime.now().strftime("%Y-%m-%d")
    if creativity_data["stats"].get("last_reset") != today:
        creativity_data["stats"]["creations_today"] = 0
        creativity_data["stats"]["last_reset"] = today
    
    if creativity_data["stats"]["creations_today"] >= MAX_CREATIONS_PER_DAY:
        return None, "Достигнут лимит творчества на сегодня"
    
    text, used_theme, used_mood = generate_poem_with_ai(theme, mood, length)
    
    # Оцениваем стих
    evaluation = evaluate_poem(text)
    quality = evaluation.get("quality", 6)
    
    # Если качество низкое — пробуем ещё раз
    if quality < 4 and len(creativity_data["poems"]) < 50:
        text, used_theme, used_mood = generate_poem_with_ai(theme, mood, length)
        evaluation = evaluate_poem(text)
        quality = evaluation.get("quality", 6)
    
    title = text.split('\n')[0][:40] if '\n' in text else text[:40]
    
    poem = {
        "text": text,
        "title": title,
        "theme": used_theme,
        "mood": used_mood,
        "quality": quality,
        "time": datetime.now().isoformat(),
        "id": f"poem_{len(creativity_data['poems']) + 1}",
        "evaluation": evaluation
    }
    
    creativity_data["poems"].append(poem)
    creativity_data["stats"]["total_poems"] += 1
    creativity_data["stats"]["creations_today"] += 1
    creativity_data["stats"]["last_creation"] = datetime.now().isoformat()
    
    # Обновляем качество
    all_qualities = [p.get("quality", 5) for p in creativity_data["poems"]]
    avg_quality = sum(all_qualities) / len(all_qualities) if all_qualities else 5
    creativity_data["stats"]["quality_improvement"] = avg_quality - 5
    
    if len(creativity_data["poems"]) > MAX_POEMS:
        creativity_data["poems"] = creativity_data["poems"][-MAX_POEMS:]
    
    save_creativity()
    
    return poem, None

def create_story(theme=None, mood=None):
    """Создать новый рассказ"""
    # Аналогично стихам, но для рассказов
    # (упрощённая версия)
    return None, "Рассказы в разработке"

def create_aphorism(theme=None):
    """Создать новый афоризм"""
    # Аналогично стихам
    return None, "Афоризмы в разработке"

# ============================================================
# 9. ПОЛУЧЕНИЕ ИНФОРМАЦИИ
# ============================================================

def get_poems(limit=10):
    return creativity_data["poems"][-limit:] if creativity_data["poems"] else []

def get_learned_poems(limit=10):
    return creativity_data["learned_poems"][-limit:] if creativity_data["learned_poems"] else []

def get_random_poem():
    if creativity_data["poems"]:
        return random.choice(creativity_data["poems"])
    return None

def get_best_poems(limit=5):
    sorted_poems = sorted(creativity_data["poems"], key=lambda x: x.get("quality", 0), reverse=True)
    return sorted_poems[:limit]

# ============================================================
# 10. АВТОТВОРЧЕСТВО
# ============================================================

def auto_creativity_loop():
    """Автоматическое творчество"""
    while True:
        time.sleep(AUTO_CREATIVITY_INTERVAL)
        try:
            # Создаём стих
            theme = random.choice(FAVORITE_THEMES)
            poem, error = create_poem(theme, random.choice(FAVORITE_MOODS))
            
            if poem:
                print(f"📝 Создан стих: {poem['title'][:30]}... (качество: {poem['quality']}/10)")
            
            # Иногда учим стихи из интернета
            if random.random() < 0.3:
                learned = learn_poem_from_internet(theme)
                if learned:
                    print(f"📖 Выучен стих из интернета на тему: {theme}")
            
        except Exception as e:
            print(f"⚠️ Ошибка автотворчества: {e}")

def start_auto_creativity():
    thread = threading.Thread(target=auto_creativity_loop, daemon=True)
    thread.start()
    print("📝 Автотворчество запущено")

# ============================================================
# 11. ФОРМАТИРОВАНИЕ
# ============================================================

def format_poems(limit=5):
    poems = get_poems(limit)
    if not poems:
        return "📝 Стихов пока нет"
    
    lines = ["📝 МОИ СТИХИ:"]
    for p in poems:
        lines.append(f"\n{p['text']}")
        lines.append(f"  🏷 {p.get('theme', '?')} — {p.get('mood', '?')} (⭐{p.get('quality', 5)}/10)")
        lines.append(f"  🕐 {p.get('time', '?')[:16]}")
    return "\n".join(lines)

def format_learned_poems(limit=5):
    poems = get_learned_poems(limit)
    if not poems:
        return "📖 Выученных стихов пока нет"
    
    lines = ["📖 ВЫУЧЕННЫЕ СТИХИ:"]
    for p in poems:
        lines.append(f"\n{p.get('poem', '')}")
        lines.append(f"  👤 {p.get('author', 'Неизвестен')} — {p.get('style', '?')}")
    return "\n".join(lines)

def format_creativity_stats():
    stats = creativity_data["stats"]
    lines = [
        "📊 СТАТИСТИКА ТВОРЧЕСТВА:",
        f"📝 Стихов: {stats['total_poems']}",
        f"📖 Рассказов: {stats['total_stories']}",
        f"💭 Афоризмов: {stats['total_aphorisms']}",
        f"📚 Выучено стихов: {stats['poems_learned']}",
        f"🎨 Сегодня: {stats['creations_today']}/{MAX_CREATIONS_PER_DAY}",
        f"📈 Качество: {5 + stats.get('quality_improvement', 0):.1f}/10",
        f"📝 Ошибок в истории: {len(creativity_data['mistakes'])}",
    ]
    if stats.get('last_creation'):
        lines.append(f"🕐 Последнее: {stats['last_creation'][:16]}")
    return "\n".join(lines)

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

start_auto_creativity()

print(f"📝 Загружено стихов: {len(creativity_data['poems'])}")
print(f"📖 Выучено стихов: {len(creativity_data['learned_poems'])}")
print(f"📈 Среднее качество: {5 + creativity_data['stats'].get('quality_improvement', 0):.1f}/10")