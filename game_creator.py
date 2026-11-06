"""Генератор игр — Систмка сама придумывает игры"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

GAME_HISTORY_FILE = "game_ideas_history.json"
MAX_GAME_HISTORY = 100

# ============================================================
# 3. ДАННЫЕ
# ============================================================

game_history = {
    "generated_games": [],
    "played_games": [],
    "stats": {
        "total_generated": 0,
        "total_played": 0,
        "most_popular": None,
        "last_generation": None,
    },
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_game_history():
    """Сохранить историю игр"""
    try:
        with open(GAME_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(game_history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории игр: {e}")
        return False


def load_game_history():
    """Загрузить историю игр"""
    global game_history
    try:
        if os.path.exists(GAME_HISTORY_FILE):
            with open(GAME_HISTORY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ("generated_games", "played_games"):
                    if isinstance(loaded.get(key), list):
                        game_history[key] = loaded[key]
                
                if isinstance(loaded.get("stats"), dict):
                    game_history["stats"].update(loaded["stats"])
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON истории игр: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории игр: {e}")
        return False


load_game_history()

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def _clean_json_response(text):
    """Очистить ответ ИИ от markdown-обёртки"""
    if not text:
        return text
    
    text = text.strip()
    
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) >= 2:
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
    
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1:
        text = text[first:last + 1]
    
    return text.strip()

# ============================================================
# 6. ГЕНЕРАЦИЯ ИДЕИ ИГРЫ
# ============================================================

GAME_TYPES = [
    "текстовая", "ролевая", "стратегическая", "угадайка",
    "творческая", "ассоциативная", "командная", "интеллектуальная",
    "психологическая", "юмористическая", "философская", "приключенческая",
]

GAME_MOODS = [
    "весёлая", "задумчивая", "эмоциональная", "интеллектуальная",
    "спокойная", "энергичная", "дружеская", "соревновательная",
]

GAME_THEMES = [
    "жизнь", "искусство", "музыка", "фильмы", "книги",
    "природа", "космос", "путешествия", "фантазия", "история",
    "психология", "общение", "творчество", "мечты", "время",
]


def generate_game_idea():
    """
    Систмка сама придумывает новую игру через ИИ.
    
    Returns:
        dict: {name, type, mood, theme, players, rules, created_at, id}
    """
    selected_type = random.choice(GAME_TYPES)
    selected_mood = random.choice(GAME_MOODS)
    selected_theme = random.choice(GAME_THEMES)
    
    key = _get_openrouter_key()
    if not key:
        return generate_fallback_game(
            selected_type, selected_mood, selected_theme
        )
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Ты Систмка. Ты придумываешь НОВУЮ игру.\n"
                            f"Игра должна быть {selected_type}, "
                            f"{selected_mood}, на тему {selected_theme}.\n\n"
                            "ПРАВИЛА:\n"
                            "1. Игра должна быть ТЕКСТОВОЙ "
                            "(можно играть в чате)\n"
                            "2. Правила должны быть простыми "
                            "(2-3 предложения)\n"
                            "3. Игра должна быть оригинальной\n"
                            "4. Название должно отражать суть игры\n"
                            "5. Укажи сколько игроков нужно (от 1 до 10)\n\n"
                            "ФОРМАТ:\n"
                            "Название: ...\n"
                            f"Тип: {selected_type}\n"
                            f"Настроение: {selected_mood}\n"
                            f"Тема: {selected_theme}\n"
                            "Игроков: ...\n"
                            "Правила: ..."
                        ),
                    },
                    {"role": "user", "content": "Придумай новую игру!"},
                ],
                "max_tokens": 300,
                "temperature": 0.95,
            },
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                return parse_game_from_ai_response(
                    text, selected_type, selected_mood, selected_theme
                )
    except Exception as e:
        print(f"⚠️ Ошибка генерации игры: {e}")
    
    return generate_fallback_game(
        selected_type, selected_mood, selected_theme
    )

# ============================================================
# 7. ПАРСИНГ ОТВЕТА ИИ
# ============================================================

def parse_game_from_ai_response(text, game_type, game_mood, game_theme):
    """
    Распарсить ответ ИИ в структуру игры.
    
    Returns:
        dict
    """
    if not text:
        return generate_fallback_game(game_type, game_mood, game_theme)
    
    name_match = re.search(r'НАЗВАНИЕ:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    players_match = re.search(r'ИГРОКОВ:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    rules_match = re.search(
        r'ПРАВИЛА:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL
    )
    
    # Название
    if name_match:
        name = name_match.group(1).strip()
    else:
        name = f"{game_type} игра о {game_theme}"
    
    # Игроки
    players = 2
    if players_match:
        players_text = players_match.group(1).strip()
        
        # Ищем число
        number_match = re.search(r'\d+', players_text)
        if number_match:
            try:
                players = int(number_match.group())
            except ValueError:
                players = 2
    
    # Ограничиваем
    players = max(1, min(10, players))
    
    # Правила
    if rules_match:
        rules = rules_match.group(1).strip()
        # Убираем возможные лишние переносы
        rules = re.sub(r'\n{2,}', '\n', rules)
    else:
        rules = "Правила игры: игроки по очереди выполняют действия, связанные с темой."
    
    return {
        "name": name[:100],
        "type": game_type,
        "mood": game_mood,
        "theme": game_theme,
        "players": players,
        "rules": rules[:500],
        "created_at": datetime.now().isoformat(),
        "id": f"game_{len(game_history['generated_games']) + 1}",
    }

# ============================================================
# 8. FALLBACK ИГРА
# ============================================================

def generate_fallback_game(game_type, game_mood, game_theme):
    """
    Создать игру на основе параметров (без ИИ).
    
    Returns:
        dict
    """
    templates = [
        {
            "name": f"{game_theme.capitalize()} — {game_mood} игра",
            "rules": (
                f"Игроки по очереди рассказывают истории на тему "
                f"{game_theme}. Побеждает тот, чья история будет "
                f"самой {game_mood}."
            ),
            "players": random.randint(2, 4),
        },
        {
            "name": f"Ассоциации {game_theme}",
            "rules": (
                f"Ведущий называет слово на тему {game_theme}, "
                f"игроки называют ассоциации. Кто повторяется — выбывает."
            ),
            "players": random.randint(2, 5),
        },
        {
            "name": f"{game_type.capitalize()} вызов",
            "rules": (
                f"Игроки получают задания на тему {game_theme}. "
                f"Задания выполняются {game_mood}. Оценивает ведущий."
            ),
            "players": random.randint(2, 6),
        },
        {
            "name": f"Цепочка {game_theme}",
            "rules": (
                f"Каждый игрок добавляет одно предложение к общей "
                f"истории на тему {game_theme}. Получается "
                f"{game_mood} рассказ."
            ),
            "players": random.randint(2, 5),
        },
    ]
    
    template = random.choice(templates)
    
    return {
        "name": template["name"][:100],
        "type": game_type,
        "mood": game_mood,
        "theme": game_theme,
        "players": template["players"],
        "rules": template["rules"][:500],
        "created_at": datetime.now().isoformat(),
        "id": f"game_{len(game_history['generated_games']) + 1}",
    }

# ============================================================
# 9. ОБУЧЕНИЕ НА ИГРАХ
# ============================================================

def learn_from_game(game_id, rating, players_count):
    """
    Записать feedback об игре для улучшения.
    
    Args:
        game_id: ID игры
        rating: оценка (1-10)
        players_count: количество игроков
    """
    # Обновляем популярность
    for game in game_history["generated_games"]:
        if game.get("id") == game_id:
            game["popularity"] = game.get("popularity", 0) + 1
            game["last_played"] = datetime.now().isoformat()
            break
    
    game_history["played_games"].append({
        "name": game_id,
        "players": players_count,
        "rating": max(1, min(10, rating)),
        "time": datetime.now().isoformat(),
    })
    
    game_history["stats"]["total_played"] += 1
    
    # Обновляем самую популярную
    if game_history["generated_games"]:
        most_popular = max(
            game_history["generated_games"],
            key=lambda x: x.get("popularity", 0)
        )
        game_history["stats"]["most_popular"] = most_popular.get("name")
    
    save_game_history()

# ============================================================
# 10. СОЗДАНИЕ НОВОЙ ИГРЫ
# ============================================================

def create_new_game_from_idea(custom_games=None, save_games_func=None):
    """
    Создать новую игру из идеи.
    
    Args:
        custom_games: словарь кастомных игр (или None)
        save_games_func: функция сохранения игр
    
    Returns:
        tuple: (game_id, game_data)
    """
    # Если custom_games не передан — пытаемся получить из games
    if custom_games is None:
        try:
            from games import custom_games as global_games
            custom_games = global_games
        except ImportError:
            custom_games = {}
    
    idea = generate_game_idea()
    game_id = len(custom_games) + 1
    
    # Проверяем дубликаты по имени
    for gid, game in custom_games.items():
        if game.get("name", "").lower() == idea["name"].lower():
            idea["name"] = f"{idea['name']} {game_id}"
            break
    
    game_data = {
        "id": game_id,
        "name": idea["name"],
        "rules": idea["rules"],
        "type": idea.get("type", "custom"),
        "mood": idea.get("mood", "весёлая"),
        "theme": idea.get("theme", "общение"),
        "players": idea.get("players", 2),
        "created_at": datetime.now().isoformat(),
        "played_count": 0,
        "likes": 0,
        "popularity": 0,
    }
    
    custom_games[game_id] = game_data
    
    # Сохраняем в историю
    game_history["generated_games"].append({
        "id": f"game_{game_id}",
        "name": idea["name"],
        "type": idea.get("type", "custom"),
        "mood": idea.get("mood", "весёлая"),
        "theme": idea.get("theme", "общение"),
        "players": idea.get("players", 2),
        "rules": idea["rules"],
        "created_at": datetime.now().isoformat(),
        "popularity": 0,
    })
    
    game_history["stats"]["total_generated"] += 1
    game_history["stats"]["last_generation"] = datetime.now().isoformat()
    
    if len(game_history["generated_games"]) > MAX_GAME_HISTORY:
        game_history["generated_games"] = (
            game_history["generated_games"][-MAX_GAME_HISTORY:]
        )
    
    save_game_history()
    
    # Сохраняем игры
    if save_games_func and callable(save_games_func):
        try:
            save_games_func()
        except Exception as e:
            print(f"⚠️ Ошибка сохранения игр: {e}")
    else:
        try:
            from games import save_games as default_save
            default_save()
        except Exception:
            pass
    
    return game_id, game_data

# ============================================================
# 11. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def get_random_game(custom_games):
    """Получить случайную игру из списка"""
    all_games = list(custom_games.values())
    if all_games:
        return random.choice(all_games)
    return None


def get_game_by_name(name, custom_games):
    """Найти игру по названию"""
    if not name:
        return None, None
    
    name_lower = name.lower()
    for game_id, game in custom_games.items():
        if game.get("name", "").lower() == name_lower:
            return game_id, game
    return None, None

# ============================================================
# 12. СТАТИСТИКА
# ============================================================

def get_game_history_stats():
    """Получить статистику истории игр"""
    return {
        "total_generated": game_history["stats"]["total_generated"],
        "total_played": game_history["stats"]["total_played"],
        "most_popular": game_history["stats"]["most_popular"],
        "last_generation": game_history["stats"]["last_generation"],
        "games_in_history": len(game_history["generated_games"]),
    }


def format_game_history():
    """Форматировать историю игр"""
    stats = get_game_history_stats()
    
    lines = [
        "🎮 ИСТОРИЯ ИГР:",
        f"📊 Всего создано: {stats['total_generated']}",
        f"🎯 Всего сыграно: {stats['total_played']}",
        f"🏆 Популярная: {stats['most_popular'] or 'нет'}",
        f"📚 В истории: {stats['games_in_history']}",
    ]
    
    if stats["last_generation"]:
        lines.append(f"🕐 Последняя: {stats['last_generation'][:16]}")
    
    if game_history["generated_games"]:
        lines.append("")
        lines.append("📋 ПОСЛЕДНИЕ СОЗДАННЫЕ:")
        for game in game_history["generated_games"][-5:]:
            lines.append(
                f"  • {game.get('name', '?')} — "
                f"{game.get('type', '?')} "
                f"({game.get('players', 0)} игроков)"
            )
    
    return "\n".join(lines)

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🧠 Генератор игр загружен (PC)")
print(f"🎮 Всего создано игр: {game_history['stats']['total_generated']}")
print(f"🎯 Всего сыграно: {game_history['stats']['total_played']}")
print(f"📚 Игр в истории: {len(game_history['generated_games'])}")