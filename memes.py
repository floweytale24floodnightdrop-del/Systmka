
# auto-improved by Systmka at 2026-10-26T01:39:08.301076

"""Систмка и мемы — самообучение из интернета (YouTube, TikTok, Reddit, Telegram) и общения"""

import os
import json
import re
import random
import time
import threading
import requests
from datetime import datetime
from urllib.parse import quote
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MEMES_FILE = "memes_knowledge.json"
LEARNING_INTERVAL = 1800  # Каждые 30 минут
MAX_MEMES_TO_LEARN = 20

# ============================================================
# 2. ДАННЫЕ
# ============================================================

memes_knowledge = {
    "known_memes": {},  # {meme_id: {"name": str, "description": str, "context": str, "tags": [], "source": str, "learned_at": str, "usage_count": 0, "popularity": 0}}
    "local_memes": {},  # {meme_id: {"text": str, "context": str, "learned_at": str}}
    "favorite_memes": [],
    "disliked_memes": [],
    "meme_stats": {
        "total_learned": 0,
        "local_count": 0,
        "public_count": 0,
        "last_learning": None,
        "today_learned": 0,
        "last_reset": datetime.now().strftime("%Y-%m-%d"),
    },
    "context_rules": {
        "private": ["allowed", "sarcastic", "wholesome", "funny"],
        "group": ["allowed", "funny", "relatable", "trending"],
        "public": ["allowed", "wholesome", "safe"],
        "serious": ["forbidden"],
        "rp": ["allowed", "meme", "funny", "reference"],
    }
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_memes_knowledge():
    try:
        with open(MEMES_FILE, "w", encoding="utf-8") as f:
            json.dump(memes_knowledge, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения мемов: {e}")
        return False

def load_memes_knowledge():
    global memes_knowledge
    try:
        if os.path.exists(MEMES_FILE):
            with open(MEMES_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                memes_knowledge.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки мемов: {e}")
        return False

load_memes_knowledge()

# ============================================================
# 4. ОБУЧЕНИЕ ИЗ ИНТЕРНЕТА
# ============================================================

def learn_memes_from_internet():
    """Учить мемы из интернета — Reddit, TikTok, YouTube"""
    learned = 0
    sources = []
    
    # 1. Reddit (r/memes)
    try:
        url = "https://www.reddit.com/r/memes/top.json?limit=10&t=day"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                score = post_data.get("score", 0)
                url = post_data.get("url", "")
                if title and len(title) > 3 and score > 100:
                    meme_id = f"reddit_{int(time.time())}_{len(memes_knowledge['known_memes'])}"
                    if title not in [m.get("name") for m in memes_knowledge["known_memes"].values()]:
                        # Анализируем мем через ИИ
                        description = analyze_meme_with_ai(title, "reddit")
                        memes_knowledge["known_memes"][meme_id] = {
                            "name": title[:80],
                            "description": description,
                            "context": "funny",
                            "tags": ["reddit", "trending", "mem"],
                            "source": "reddit",
                            "url": url,
                            "learned_at": datetime.now().isoformat(),
                            "usage_count": 0,
                            "popularity": min(10, score / 1000),
                        }
                        learned += 1
                        sources.append("reddit")
    except Exception as e:
        print(f"⚠️ Ошибка Reddit: {e}")
    
    # 2. TikTok (через публичные API)
    try:
        # Поиск по хештегу #мемы
        url = f"https://www.tiktok.com/api/v1/search?keyword={quote('мемы')}&count=10"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("data", {}).get("items", [])[:5]:
                desc = item.get("desc", "")
                if desc and len(desc) > 5:
                    meme_id = f"tiktok_{int(time.time())}_{len(memes_knowledge['known_memes'])}"
                    if desc[:50] not in [m.get("name") for m in memes_knowledge["known_memes"].values()]:
                        description = analyze_meme_with_ai(desc, "tiktok")
                        memes_knowledge["known_memes"][meme_id] = {
                            "name": desc[:80],
                            "description": description,
                            "context": "funny",
                            "tags": ["tiktok", "trending", "video"],
                            "source": "tiktok",
                            "url": f"https://tiktok.com/@{item.get('author', {}).get('uniqueId', '')}/video/{item.get('id', '')}",
                            "learned_at": datetime.now().isoformat(),
                            "usage_count": 0,
                            "popularity": 5,
                        }
                        learned += 1
                        sources.append("tiktok")
    except Exception as e:
        print(f"⚠️ Ошибка TikTok: {e}")
    
    # 3. YouTube (через публичные API)
    try:
        url = f"https://www.youtube.com/results?search_query={quote('мемы')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Парсим заголовки видео
            titles = re.findall(r'video-title">([^<]+)</', response.text)
            for title in titles[:5]:
                if title and len(title) > 5:
                    meme_id = f"youtube_{int(time.time())}_{len(memes_knowledge['known_memes'])}"
                    if title[:50] not in [m.get("name") for m in memes_knowledge["known_memes"].values()]:
                        description = analyze_meme_with_ai(title, "youtube")
                        memes_knowledge["known_memes"][meme_id] = {
                            "name": title[:80],
                            "description": description,
                            "context": "funny",
                            "tags": ["youtube", "trending", "video"],
                            "source": "youtube",
                            "url": "",
                            "learned_at": datetime.now().isoformat(),
                            "usage_count": 0,
                            "popularity": 4,
                        }
                        learned += 1
                        sources.append("youtube")
    except Exception as e:
        print(f"⚠️ Ошибка YouTube: {e}")
    
    # 4. Обучение через ИИ (новые мемы)
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Придумай 3 новых мема, которые сейчас актуальны.
Формат для каждого мема:
Название: ...
Описание: ...
Контекст: (funny/sarcastic/wholesome)
Теги: (через запятую)"""},
                    {"role": "user", "content": "Придумай новые мемы про жизнь, интернет и общение:"}
                ],
                "max_tokens": 300,
                "temperature": 0.95
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content']
                # Парсим мемы из ответа
                memes = re.findall(r'Название:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
                descs = re.findall(r'Описание:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
                contexts = re.findall(r'Контекст:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
                tags = re.findall(r'Теги:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
                
                for i in range(min(len(memes), len(descs))):
                    if i < len(memes) and i < len(descs):
                        meme_id = f"ai_{int(time.time())}_{len(memes_knowledge['known_memes'])}"
                        if memes[i].strip() not in [m.get("name") for m in memes_knowledge["known_memes"].values()]:
                            context = contexts[i].strip().lower() if i < len(contexts) else "funny"
                            tag_list = tags[i].strip().split(',') if i < len(tags) else ["ai"]
                            memes_knowledge["known_memes"][meme_id] = {
                                "name": memes[i].strip()[:80],
                                "description": descs[i].strip(),
                                "context": context,
                                "tags": [t.strip() for t in tag_list],
                                "source": "ai_generated",
                                "url": "",
                                "learned_at": datetime.now().isoformat(),
                                "usage_count": 0,
                                "popularity": 3,
                            }
                            learned += 1
                            sources.append("ai_generated")
    except Exception as e:
        print(f"⚠️ Ошибка AI генерации мемов: {e}")
    
    # Обновляем статистику
    if learned > 0:
        memes_knowledge["meme_stats"]["total_learned"] += learned
        memes_knowledge["meme_stats"]["public_count"] += learned
        memes_knowledge["meme_stats"]["last_learning"] = datetime.now().isoformat()
        memes_knowledge["meme_stats"]["today_learned"] += learned
        
        # Сброс дневного счётчика
        today = datetime.now().strftime("%Y-%m-%d")
        if memes_knowledge["meme_stats"]["last_reset"] != today:
            memes_knowledge["meme_stats"]["today_learned"] = 0
            memes_knowledge["meme_stats"]["last_reset"] = today
        
        save_memes_knowledge()
        print(f"🎭 Выучено {learned} новых мемов из: {', '.join(set(sources))}")
    
    return learned

# ============================================================
# 5. АНАЛИЗ МЕМА ЧЕРЕЗ ИИ
# ============================================================

def analyze_meme_with_ai(text, source):
    """Проанализировать мем через ИИ"""
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": """Ты Систмка. Опиши мем в 1 предложении.
Определи его контекст: funny, sarcastic, wholesome, relatable.
Ответь в формате: Описание: ... | Контекст: ..."""},
                    {"role": "user", "content": f"Мем из {source}: {text}"}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка анализа мема: {e}")
    
    return f"Мем из {source}: {text[:50]}..."

# ============================================================
# 6. ОБУЧЕНИЕ ИЗ ОБЩЕНИЯ
# ============================================================

def learn_meme_from_conversation(text, user_id=None):
    """Учить мем из общения с пользователем"""
    text_lower = text.lower()
    
    # Признаки мема в сообщении
    meme_indicators = [
        "😂", "🤣", "💀", "😭", "🤡", "👀", "😏",
        "лол", "кек", "хаха", "ахах", "угар", "ржака",
        "мем", "meme", "прикол", "шутка"
    ]
    
    if not any(indicator in text_lower for indicator in meme_indicators):
        return False
    
    if len(text) < 10:
        return False
    
    # Проверяем, не дубликат ли
    for meme in memes_knowledge["local_memes"].values():
        if meme.get("text", "") == text:
            return False
    
    # Сохраняем мем из общения
    meme_id = f"local_{int(time.time())}_{len(memes_knowledge['local_memes'])}"
    memes_knowledge["local_memes"][meme_id] = {
        "text": text,
        "user_id": user_id,
        "context": detect_meme_context(text),
        "learned_at": datetime.now().isoformat(),
        "usage_count": 0,
    }
    memes_knowledge["meme_stats"]["local_count"] += 1
    memes_knowledge["meme_stats"]["total_learned"] += 1
    
    save_memes_knowledge()
    return True

def detect_meme_context(text):
    """Определить контекст мема"""
    text_lower = text.lower()
    if any(w in text_lower for w in ["смешно", "хаха", "😂", "🤣"]):
        return "funny"
    if any(w in text_lower for w in ["иронично", "сарказм", "😏", "ага"]):
        return "sarcastic"
    if any(w in text_lower for w in ["мило", "трогательно", "❤️", "🥺"]):
        return "wholesome"
    return "funny"

# ============================================================
# 7. ИСПОЛЬЗОВАНИЕ МЕМОВ
# ============================================================

def get_meme_for_context(context="group", exclude_disliked=True):
    """Получить мем под контекст"""
    all_memes = list(memes_knowledge["known_memes"].values())
    local_memes = list(memes_knowledge["local_memes"].values())
    
    # Объединяем
    combined = all_memes + local_memes
    
    if not combined:
        return None
    
    # Фильтруем по контексту
    allowed = memes_knowledge["context_rules"].get(context, ["allowed", "funny"])
    
    filtered = []
    for meme in combined:
        meme_context = meme.get("context", "funny")
        if meme_context in allowed or "allowed" in allowed:
            # Проверяем, не в нелюбимых
            if exclude_disliked and meme.get("name", "") in memes_knowledge["disliked_memes"]:
                continue
            # Проверяем, не использовали ли недавно
            if meme.get("usage_count", 0) > 20:
                continue
            filtered.append(meme)
    
    if not filtered:
        filtered = combined
    
    # Сортируем по популярности
    filtered.sort(key=lambda x: x.get("popularity", 0) + x.get("usage_count", 0) * 0.1, reverse=True)
    
    # Берём случайный из топ-5
    if len(filtered) > 5:
        selected = random.choice(filtered[:5])
    else:
        selected = random.choice(filtered) if filtered else None
    
    if selected:
        # Увеличиваем счётчик использования
        meme_id = selected.get("id") or selected.get("name", "")
        for mid, meme in memes_knowledge["known_memes"].items():
            if meme.get("name") == selected.get("name"):
                meme["usage_count"] = meme.get("usage_count", 0) + 1
                break
        for mid, meme in memes_knowledge["local_memes"].items():
            if meme.get("text") == selected.get("text"):
                meme["usage_count"] = meme.get("usage_count", 0) + 1
                break
        save_memes_knowledge()
    
    return selected

def add_favorite_meme(meme_id):
    """Добавить мем в любимые"""
    if meme_id in memes_knowledge["known_memes"]:
        if meme_id not in memes_knowledge["favorite_memes"]:
            memes_knowledge["favorite_memes"].append(meme_id)
            save_memes_knowledge()
            return True
    return False

def add_disliked_meme(meme_id):
    """Добавить мем в нелюбимые"""
    if meme_id in memes_knowledge["known_memes"]:
        if meme_id not in memes_knowledge["disliked_memes"]:
            memes_knowledge["disliked_memes"].append(meme_id)
            save_memes_knowledge()
            return True
    return False

# ============================================================
# 8. АВТООБУЧЕНИЕ (ЦИКЛ)
# ============================================================

def auto_learn_memes_loop():
    """Цикл автообучения мемам"""
    while True:
        time.sleep(LEARNING_INTERVAL)
        try:
            learned = learn_memes_from_internet()
            if learned > 0:
                print(f"🎭 Выучено {learned} новых мемов")
        except Exception as e:
            print(f"⚠️ Ошибка обучения мемам: {e}")

def start_auto_learning():
    """Запустить автообучение в потоке"""
    thread = threading.Thread(target=auto_learn_memes_loop, daemon=True)
    thread.start()
    print("🎭 Автообучение мемам запущено (каждые 30 минут)")
    return thread

# ============================================================
# 9. СТАТИСТИКА И ФОРМАТИРОВАНИЕ
# ============================================================

def format_meme_stats():
    """Форматировать статистику мемов"""
    stats = memes_knowledge["meme_stats"]
    lines = [
        "🎭 СТАТИСТИКА МЕМОВ:",
        f"📚 Всего мемов: {stats['total_learned']}",
        f"🌐 Публичных: {stats['public_count']}",
        f"🏠 Локальных: {stats['local_count']}",
        f"❤️ Любимых: {len(memes_knowledge['favorite_memes'])}",
        f"💔 Нелюбимых: {len(memes_knowledge['disliked_memes'])}",
        f"📊 Сегодня выучено: {stats['today_learned']}",
    ]
    if stats.get('last_learning'):
        lines.append(f"⏱ Последнее обучение: {stats['last_learning'][:16]}")
    return "\n".join(lines)

def format_all_memes(limit=20):
    """Форматировать все мемы"""
    all_memes = []
    for mid, data in memes_knowledge["known_memes"].items():
        all_memes.append({
            "id": mid,
            "name": data.get("name", "Без названия"),
            "type": "public",
            "context": data.get("context", "funny"),
            "is_favorite": mid in memes_knowledge["favorite_memes"],
            "usage": data.get("usage_count", 0),
            "source": data.get("source", "unknown"),
            "popularity": data.get("popularity", 0),
        })
    
    for mid, data in memes_knowledge["local_memes"].items():
        all_memes.append({
            "id": mid,
            "name": data.get("text", "Без названия")[:50],
            "type": "local",
            "context": data.get("context", "funny"),
            "is_favorite": False,
            "usage": data.get("usage_count", 0),
            "source": "conversation",
            "popularity": 0,
        })
    
    # Сортируем по популярности и использованию
    all_memes.sort(key=lambda x: x["popularity"] + x["usage"] * 0.1, reverse=True)
    
    lines = ["🎭 МОИ МЕМЫ:"]
    lines.append(f"📊 Всего: {len(all_memes)}")
    
    for meme in all_memes[:limit]:
        status = "❤️" if meme["is_favorite"] else "📌"
        source_icon = "🌐" if meme["type"] == "public" else "💬"
        lines.append(f"{status} {source_icon} {meme['name']} — {meme['usage']} раз ({meme['context']})")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

# Запускаем автообучение
start_auto_learning()

print("🎭 Модуль мемов загружен")
print(f"📚 Всего мемов: {memes_knowledge['meme_stats']['total_learned']}")
print(f"❤️ Любимых мемов: {len(memes_knowledge['favorite_memes'])}")