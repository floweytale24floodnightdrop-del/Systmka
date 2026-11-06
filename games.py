"""Игры Систмки — основная логика и управление"""

import os
import json
import random
import time
import threading
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

GAMES_FILE = "custom_games.json"

# ============================================================
# 2. ДАННЫЕ
# ============================================================

custom_games = {}
active_games = {}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА ИГР
# ============================================================

def save_games():
    """Сохранить кастомные игры"""
    try:
        with open(GAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_games, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения игр: {e}")
        return False


def load_games():
    """Загрузить кастомные игры"""
    global custom_games
    try:
        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    custom_games = loaded
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON игр: {e}")
        custom_games = {}
    except Exception as e:
        print(f"⚠️ Ошибка загрузки игр: {e}")
        custom_games = {}
    return custom_games


load_games()

# ============================================================
# 4. ПОЛУЧЕНИЕ СПИСКА ИГР
# ============================================================

def get_all_games():
    """
    Получить все игры (базовые + кастомные).
    
    Returns:
        dict
    """
    try:
        from game_engine import BASE_GAMES
        all_games = BASE_GAMES.copy()
    except ImportError:
        all_games = {}
    
    for gid, game in custom_games.items():
        all_games[f"custom_{gid}"] = {
            "description": game.get("name", "Кастомная игра"),
            "type": "custom",
            "game_id": gid,
            "rules": game.get("rules", ""),
        }
    
    return all_games

# ============================================================
# 5. ЗАПУСК ИГРЫ
# ============================================================

def start_game(bot, chat_id, game_id):
    """
    Запустить игру.
    
    Args:
        bot: telebot instance
        chat_id: ID чата
        game_id: ID игры (int для кастомной, str для базовой)
    
    Returns:
        bool: успех
    """
    # Кастомная игра
    if isinstance(game_id, int) and game_id in custom_games:
        game = custom_games[game_id]
        bot.send_message(
            chat_id,
            f"🎮 {game.get('name', 'Игра')}\n\n"
            f"📜 {game.get('rules', 'Игра без правил')}\n\n"
            f"Готов? Напиши 'готов' чтобы начать!",
        )
        active_games[chat_id] = {
            "type": "custom",
            "game_id": game_id,
            "stage": "waiting",
            "data": {},
        }
        return True
    
    # Базовая игра — по ключу или по типу
    try:
        from game_engine import BASE_GAMES, start_base_game
    except ImportError:
        return False
    
    # Если game_id — ключ из BASE_GAMES
    if isinstance(game_id, str) and game_id in BASE_GAMES:
        game_type = BASE_GAMES[game_id]["type"]
        return start_base_game(bot, chat_id, game_type, active_games)
    
    # Если game_id — тип ("number_guess", "rps" и т.д.)
    if isinstance(game_id, str):
        return start_base_game(bot, chat_id, game_id, active_games)
    
    return False

# ============================================================
# 6. ОБРАБОТКА ВВОДА
# ============================================================

def process_game_input(bot, chat_id, text):
    """
    Обработка ввода в игре.
    
    Returns:
        bool: True если игра обработала
    """
    if chat_id not in active_games:
        return False
    
    game = active_games.get(chat_id, {})
    text_lower = text.lower().strip() if text else ""
    
    # Выход
    if text_lower in ("выход", "стоп", "хватит", "конец"):
        del active_games[chat_id]
        bot.send_message(chat_id, "Игра окончена")
        return True
    
    game_type = game.get("type")
    
    # Кастомная
    if game_type == "custom":
        return process_custom_game(bot, chat_id, text, game)
    
    # Базовая — делегируем в game_engine
    try:
        from game_engine import (
            process_number_guess,
            process_rps,
            process_hangman,
            process_tic_tac_toe,
        )
    except ImportError:
        return False
    
    if game_type == "number_guess":
        return process_number_guess(bot, chat_id, text, active_games)
    
    if game_type == "rps":
        return process_rps(bot, chat_id, text, active_games)
    
    if game_type == "hangman":
        return process_hangman(bot, chat_id, text, active_games)
    
    if game_type == "tic_tac_toe":
        return process_tic_tac_toe(bot, chat_id, text, active_games)
    
    return False

# ============================================================
# 7. КАСТОМНАЯ ИГРА
# ============================================================

def process_custom_game(bot, chat_id, text, game):
    """
    Обработать кастомную игру.
    
    Returns:
        bool
    """
    # Ожидание "готов"
    if game.get("stage") == "waiting":
        if text and text.lower().strip() == "готов":
            game["stage"] = "playing"
            bot.send_message(chat_id, "Отлично! Начинаем! 🎉")
            return True
        else:
            bot.send_message(chat_id, "Напиши 'готов' чтобы начать!")
            return True
    
    game_id = game.get("game_id")
    if game_id not in custom_games:
        return False
    
    game_data = custom_games[game_id]
    
    # Идём к ИИ
    try:
        from config import OPENROUTER_KEY, OPENROUTER_KEYS
        import requests
        
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        if not key:
            bot.send_message(chat_id, "❌ ИИ недоступен")
            return True
        
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
                            f"Ты Систмка. Вы играете в игру.\n\n"
                            f"НАЗВАНИЕ: {game_data.get('name', '?')}\n"
                            f"ПРАВИЛА: {game_data.get('rules', '?')}\n\n"
                            "Ты ведёшь игру. Отвечай естественно.\n"
                            "Будь дружелюбной, игривой, иногда подкалывай.\n"
                            "Если игра закончилась — скажи об этом."
                        ),
                    },
                    {"role": "user", "content": text or ""},
                ],
                "max_tokens": 300,
                "temperature": 0.9,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                answer = data['choices'][0]['message']['content'].strip()
                bot.send_message(chat_id, answer)
                
                # Проверяем конец игры
                answer_lower = answer.lower()
                if any(w in answer_lower for w in ["победил", "проиграл", "конец", "финиш"]):
                    custom_games[game_id]["played_count"] = (
                        custom_games[game_id].get("played_count", 0) + 1
                    )
                    save_games()
                    del active_games[chat_id]
                
                return True
    except Exception as e:
        print(f"⚠️ Ошибка кастомной игры: {e}")
        bot.send_message(chat_id, "❌ Ошибка в игре... Давай попробуем ещё раз.")
    
    return False

# ============================================================
# 8. АВТО-ЦИКЛЫ (обёртки над game_manager)
# ============================================================

def auto_create_game_loop(bot, owner_ids, db):
    """
    Обёртка над game_manager.auto_create_game_loop.
    
    Оставлена для совместимости с bot_loops.py.
    """
    try:
        from game_manager import auto_create_game_loop as _loop
        _loop(bot, owner_ids, db, custom_games, save_games)
    except Exception as e:
        print(f"⚠️ Ошибка auto_create_game_loop: {e}")


def auto_offer_game_loop(bot, db):
    """
    Обёртка над game_manager.auto_offer_game_loop.
    
    Оставлена для совместимости с bot_loops.py.
    """
    try:
        from game_manager import auto_offer_game_loop as _loop
        _loop(bot, db, custom_games, save_games)
    except Exception as e:
        print(f"⚠️ Ошибка auto_offer_game_loop: {e}")

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_games_stats():
    """Получить статистику игр"""
    try:
        from game_engine import BASE_GAMES
        base_count = len(BASE_GAMES)
    except ImportError:
        base_count = 0
    
    return {
        "base_games": base_count,
        "custom_games": len(custom_games),
        "active_games": len(active_games),
    }


def format_games_stats():
    """Форматировать статистику"""
    stats = get_games_stats()
    
    lines = [
        "🎮 СТАТИСТИКА ИГР:",
        f"📦 Базовых игр: {stats['base_games']}",
        f"✨ Кастомных игр: {stats['custom_games']}",
        f"🟢 Активных игр: {stats['active_games']}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print(f"🎮 Загружено кастомных игр: {len(custom_games)}")

try:
    from game_engine import BASE_GAMES
    print(f"🎮 Базовых игр: {len(BASE_GAMES)}")
except ImportError:
    print("⚠️ game_engine недоступен")

try:
    from game_manager import format_mood_stats
    mood_lines = format_mood_stats().split("\n")
    if len(mood_lines) > 1:
        print(f"😊 {mood_lines[1]}")
except Exception:
    pass