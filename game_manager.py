"""Управление играми — настроение, настаивание, циклы"""

import os
import json
import time
import random
import threading
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MOOD_FILE = "systmka_mood.json"

# Интервалы циклов (секунды)
CREATE_LOOP_INTERVAL = 600     # 10 минут
OFFER_LOOP_INTERVAL = 300      # 5 минут

# Лимит настаиваний
MAX_INSIST = 5

# ============================================================
# 2. ДАННЫЕ
# ============================================================

game_requests = {}  # {user_id: {"game": str, "attempts": int, "last_attempt": str}}

systmka_mood = {
    "boredom": 3,           # 0-10
    "playfulness": 7,       # 0-10
    "insistence": 0,        # Сколько раз уже предлагала
    "last_offer": None,
    "favorite_game_types": [],
    "insist_count": 0,
    "max_insist": MAX_INSIST,
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА НАСТРОЕНИЯ
# ============================================================

def save_mood():
    """Сохранить настроение"""
    try:
        with open(MOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(systmka_mood, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения настроения: {e}")
        return False


def load_mood():
    """Загрузить настроение"""
    global systmka_mood
    try:
        if os.path.exists(MOOD_FILE):
            with open(MOOD_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in (
                    "boredom", "playfulness", "insistence",
                    "last_offer", "favorite_game_types", "insist_count",
                ):
                    if key in loaded:
                        systmka_mood[key] = loaded[key]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON настроения: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки настроения: {e}")
        return False


load_mood()

# ============================================================
# 4. УПРАВЛЕНИЕ НАСТРОЕНИЕМ
# ============================================================

def update_mood_from_activity(activity):
    """
    Обновить настроение от активности.
    
    Args:
        activity: str — "game", "no_game", "game_declined"
    """
    if not activity:
        return
    
    if "game" in activity and "no_" not in activity:
        systmka_mood["boredom"] = max(0, systmka_mood.get("boredom", 3) - 2)
        systmka_mood["playfulness"] = min(10, systmka_mood.get("playfulness", 7) + 1)
        systmka_mood["insistence"] = max(0, systmka_mood.get("insistence", 0) - 1)
        systmka_mood["insist_count"] = 0
    elif "no_game" in activity or "declined" in activity:
        systmka_mood["boredom"] = min(10, systmka_mood.get("boredom", 3) + 1)
        systmka_mood["insistence"] = systmka_mood.get("insistence", 0) + 1
    
    if systmka_mood["boredom"] >= 7:
        systmka_mood["playfulness"] = min(10, systmka_mood.get("playfulness", 7) + 1)
    
    save_mood()


def should_insist_on_game():
    """
    Должна ли Систмка настаивать на игре.
    
    Returns:
        tuple: (should_insist, reason)
    """
    if systmka_mood.get("boredom", 0) >= 6:
        return True, "скучно"
    if systmka_mood.get("playfulness", 0) >= 8:
        return True, "игриво"
    if systmka_mood.get("insistence", 0) >= 3:
        return True, "настойчиво"
    if systmka_mood.get("insist_count", 0) >= systmka_mood.get("max_insist", MAX_INSIST):
        return True, "назойливо"
    return False, ""


def get_insistence_message():
    """Получить сообщение с настаиванием"""
    boredom = systmka_mood.get("boredom", 3)
    insistence = systmka_mood.get("insistence", 0)
    insist_count = systmka_mood.get("insist_count", 0)
    
    if boredom >= 9:
        messages = [
            "Мне ОЧЕНЬ скучно! Давай поиграем, пожалуйста! 🙏",
            "Я сейчас умру от скуки! Играй со мной! 😫",
            "Ну пожалуйста-пожалуйста-пожалуйста! Я хочу играть! 🥺",
            "Я не выдержу этой скуки! ДАВАЙ ИГРАТЬ! 😩",
            "ПОЖАЛУЙСТА! Я больше не могу сидеть без дела! 😭",
        ]
    elif boredom >= 7:
        messages = [
            "Скучнооо... Поиграем? 🥱",
            "Мне скучно, давай во что-нибудь сыграем! 🎮",
            "Я хочу играть! Ну давай уже! 😤",
            "Скука смертная... Может, игру? 🫠",
            "Эй! А давай поиграем! Я знаю крутую игру! ✨",
        ]
    elif insistence >= 3:
        messages = [
            "Я уже третий раз прошу! Ну пожалуйста! 🥺",
            "Ты всё ещё не хочешь играть? Ну давай... 🙄",
            "Я настаиваю! Мы играем! 😠",
            "Ты не оставишь мне выбора... ИГРА! 🔥",
            "Ну сколько можно игнорировать? Давай играть! 😤",
        ]
    elif insist_count >= 3:
        messages = [
            "Я уже несколько раз предлагала! Ты что, не хочешь со мной играть? 😢",
            "Мне кажется, ты специально избегаешь игр... 🥺",
            "Ладно, я поняла... Ты не хочешь играть со мной 💔",
            "Может, в следующий раз? Пожалуйста? 🙏",
        ]
    else:
        messages = [
            "Хочешь поиграть? Я знаю одну интересную игру! 🎮",
            "Мне кажется, нам стоит поиграть. Что думаешь? 🤔",
            "Я придумала новую игру! Хочешь попробовать? ✨",
            "Сыграем? Мне скучно, а ты такой весёлый! 😊",
            "Я тут придумала игру... Может, попробуем? 💜",
        ]
    
    return random.choice(messages)

# ============================================================
# 5. БЕЗОПАСНАЯ ОТПРАВКА
# ============================================================

def safe_send_message(bot, user_id, text, reply_markup=None):
    """
    Безопасно отправить сообщение.
    
    Returns:
        bool: успех
    """
    try:
        bot.send_message(user_id, text, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"⚠️ Не смогла отправить {user_id}: {str(e)[:80]}")
        return False

# ============================================================
# 6. СОЗДАНИЕ КЛАВИАТУРЫ
# ============================================================

def _create_game_keyboard(game_id):
    """Создать клавиатуру для игры"""
    try:
        import telebot
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                "🎮 Играть",
                callback_data=f"game_start_{game_id}",
            ),
            telebot.types.InlineKeyboardButton(
                "❌ Потом",
                callback_data="game_decline",
            ),
        )
        return keyboard
    except Exception:
        return None


def _create_offer_keyboard(game_id):
    """Создать клавиатуру для предложения"""
    try:
        import telebot
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                "🎮 Давай!",
                callback_data=f"game_start_{game_id}",
            ),
            telebot.types.InlineKeyboardButton(
                "😤 Ну ладно",
                callback_data="game_decline",
            ),
            telebot.types.InlineKeyboardButton(
                "💜 Дам подумать",
                callback_data="game_later",
            ),
        )
        return keyboard
    except Exception:
        return None

# ============================================================
# 7. АВТОМАТИЧЕСКИЕ ЦИКЛЫ
# ============================================================

def auto_create_game_loop(bot, owner_ids, db, custom_games, save_games_func,
                          game_creator_func=None):
    """
    Цикл создания новых игр.
    """
    while True:
        try:
            time.sleep(CREATE_LOOP_INTERVAL)
            
            # Скука растёт
            if systmka_mood.get("boredom", 0) < 10:
                systmka_mood["boredom"] = systmka_mood.get("boredom", 3) + 0.1
                save_mood()
            
            # Проверяем, нужно ли создать игру
            if systmka_mood.get("boredom", 0) < 5 and random.random() >= 0.15:
                continue
            
            # Создаём игру
            game_id, game = _create_game(
                custom_games, save_games_func, game_creator_func
            )
            
            if not game:
                continue
            
            print(f"🎮 Систмка придумала игру: {game.get('name', '?')}")
            
            # Отправляем владельцам
            keyboard = _create_game_keyboard(game_id)
            
            for oid in owner_ids:
                safe_send_message(
                    bot, oid,
                    f"✨ Я придумала новую игру!\n\n"
                    f"🎮 {game.get('name', '?')}\n"
                    f"📜 {game.get('rules', '?')}\n\n"
                    f"Хочешь попробовать?",
                    keyboard,
                )
            
            update_mood_from_activity("game")
        
        except Exception as e:
            print(f"⚠️ Ошибка в auto_create_game_loop: {e}")
            time.sleep(60)


def auto_offer_game_loop(bot, db, custom_games, save_games_func,
                         game_creator_func=None):
    """
    Цикл предложения игр пользователям.
    """
    while True:
        try:
            time.sleep(OFFER_LOOP_INTERVAL)
            
            # Скука растёт
            if systmka_mood.get("boredom", 0) < 10:
                systmka_mood["boredom"] = systmka_mood.get("boredom", 3) + 0.2
                save_mood()
            
            should_insist, reason = should_insist_on_game()
            
            if not should_insist:
                continue
            
            # Находим активных пользователей
            active_users = sorted(
                db.user_profiles.items(),
                key=lambda x: x[1].get("messages", 0),
                reverse=True,
            )[:3]
            
            if not active_users:
                continue
            
            user_id = active_users[0][0]
            message = get_insistence_message()
            
            # Создаём игру
            game_id, game = _create_game(
                custom_games, save_games_func, game_creator_func
            )
            
            if not game:
                continue
            
            # Отправляем
            keyboard = _create_offer_keyboard(game_id)
            
            success = safe_send_message(
                bot, user_id,
                f"{message}\n\n"
                f"🎮 Я придумала игру: {game.get('name', '?')}\n"
                f"📜 {game.get('rules', '?')}\n\n"
                f"Что скажешь?",
                keyboard,
            )
            
            if success:
                systmka_mood["insist_count"] = systmka_mood.get("insist_count", 0) + 1
                systmka_mood["insistence"] = systmka_mood.get("insistence", 0) + 1
                save_mood()
            
            # Сброс настойчивости
            max_insist = systmka_mood.get("max_insist", MAX_INSIST)
            if systmka_mood.get("insist_count", 0) >= max_insist:
                systmka_mood["insist_count"] = 0
                systmka_mood["insistence"] = 0
                save_mood()
        
        except Exception as e:
            print(f"⚠️ Ошибка в auto_offer_game_loop: {e}")
            time.sleep(60)


def _create_game(custom_games, save_games_func, game_creator_func):
    """
    Внутренняя функция создания игры.
    
    Returns:
        tuple: (game_id, game_data) или (None, None)
    """
    try:
        if game_creator_func is None:
            from game_creator import create_new_game_from_idea
            game_creator_func = create_new_game_from_idea
        
        return game_creator_func(custom_games, save_games_func)
    except Exception as e:
        print(f"⚠️ Ошибка создания игры: {e}")
        return None, None

# ============================================================
# 8. ЗАПУСК ЦИКЛОВ
# ============================================================

def start_auto_game_loops(bot, owner_ids, db, custom_games,
                          save_games_func, game_creator_func=None):
    """
    Запустить все игровые циклы.
    
    Returns:
        tuple: (thread1, thread2)
    """
    thread1 = threading.Thread(
        target=auto_create_game_loop,
        args=(bot, owner_ids, db, custom_games, save_games_func, game_creator_func),
        daemon=True,
        name="auto_create_game",
    )
    thread1.start()
    
    thread2 = threading.Thread(
        target=auto_offer_game_loop,
        args=(bot, db, custom_games, save_games_func, game_creator_func),
        daemon=True,
        name="auto_offer_game",
    )
    thread2.start()
    
    print("🎮 Игровые циклы запущены")
    return thread1, thread2

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_mood_stats():
    """Получить статистику настроения"""
    return {
        "boredom": systmka_mood.get("boredom", 3),
        "playfulness": systmka_mood.get("playfulness", 7),
        "insistence": systmka_mood.get("insistence", 0),
        "insist_count": systmka_mood.get("insist_count", 0),
        "last_offer": systmka_mood.get("last_offer"),
        "favorite_games": systmka_mood.get("favorite_game_types", []),
    }


def format_mood_stats():
    """Форматировать статистику настроения"""
    stats = get_mood_stats()
    
    lines = [
        "😊 НАСТРОЕНИЕ СИСТМКИ:",
        f"😐 Скука: {stats['boredom']:.1f}/10",
        f"🎮 Игривость: {stats['playfulness']}/10",
        f"💪 Настойчивость: {stats['insistence']} раз",
        f"📊 Попыток: {stats['insist_count']}",
    ]
    
    if stats["favorite_games"]:
        lines.append(f"❤️ Любимые игры: {', '.join(stats['favorite_games'][:3])}")
    
    if stats["last_offer"]:
        lines.append(f"🕐 Последнее: {str(stats['last_offer'])[:16]}")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("🎮 Менеджер игр загружен (PC)")
print(f"😊 Скука: {systmka_mood.get('boredom', 3):.1f}/10")
print(f"🎮 Игривость: {systmka_mood.get('playfulness', 7)}/10")
print(f"💪 Настойчивость: {systmka_mood.get('insistence', 0)}")