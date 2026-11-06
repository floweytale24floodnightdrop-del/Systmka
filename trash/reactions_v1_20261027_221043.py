"""Реакции Систмки — ставит, убирает, читает реакции. Работает с brain_decisions."""

import telebot
import random
import json
import os
import time
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

REACTIONS_FILE = "reactions_settings.json"

ALL_REACTIONS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🥱", "😢", "🤡", "👾", "🎉", "😈", "🤗", "😍", "🤩", "😎",
    "😏", "😘", "🥺", "😭", "😡", "🤬", "🫶", "🕊"
]

FAVORITE_REACTIONS = ["👾", "❤️", "🔥", "🥰", "👏", "🫶"]

reaction_settings = {
    "favorite_reaction": "👾",
    "reaction_chance": 0.8,
    "max_reactions_per_minute": 10,
    "use_favorite_for_liked": True,
    "use_favorite_for_greetings": True,
    "auto_react_to_mentions": True,
    "last_reactions": [],
}


# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_reaction_settings():
    try:
        data = {
            "favorite_reaction": reaction_settings["favorite_reaction"],
            "reaction_chance": reaction_settings["reaction_chance"],
            "max_reactions_per_minute": reaction_settings["max_reactions_per_minute"],
            "use_favorite_for_liked": reaction_settings["use_favorite_for_liked"],
            "use_favorite_for_greetings": reaction_settings["use_favorite_for_greetings"],
            "auto_react_to_mentions": reaction_settings["auto_react_to_mentions"],
        }
        with open(REACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения настроек реакций: {e}")
        return False


def load_reaction_settings():
    global reaction_settings
    try:
        if os.path.exists(REACTIONS_FILE):
            with open(REACTIONS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                reaction_settings.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки настроек реакций: {e}")
        return False


load_reaction_settings()


# ============================================================
# 3. ПРОВЕРКА РЕАКЦИЙ
# ============================================================

def is_valid_reaction(emoji):
    """Проверить, валидна ли реакция."""
    return emoji in ALL_REACTIONS or emoji in ["👾"]


def get_valid_reaction(emoji):
    """Получить валидную реакцию (или любимую)."""
    if is_valid_reaction(emoji):
        return emoji
    return random.choice(FAVORITE_REACTIONS)


# ============================================================
# 4. УПРАВЛЕНИЕ ЛЮБИМОЙ РЕАКЦИЕЙ
# ============================================================

def set_favorite_reaction(emoji):
    """Установить любимую реакцию."""
    valid_emoji = get_valid_reaction(emoji)
    reaction_settings["favorite_reaction"] = valid_emoji
    save_reaction_settings()
    return True


def get_favorite_reaction():
    """Получить любимую реакцию."""
    return reaction_settings["favorite_reaction"]


# ============================================================
# 5. ПОСТАВИТЬ РЕАКЦИЮ
# ============================================================

def react_to_message(bot, chat_id, message_id, reaction):
    """
    Поставить реакцию на сообщение.
    
    Args:
        bot: telebot instance
        chat_id: ID чата
        message_id: ID сообщения
        reaction: эмодзи (или список эмодзи)
    
    Returns:
        bool: успех
    """
    if not reaction:
        return False
    
    # Если список — берём первый
    if isinstance(reaction, list):
        if not reaction:
            return False
        reaction = reaction[0]
    
    # Валидация
    if not is_valid_reaction(reaction):
        reaction = reaction_settings["favorite_reaction"]
    
    try:
        bot.set_message_reaction(
            chat_id,
            message_id,
            [telebot.types.ReactionTypeEmoji(reaction)]
        )
        
        # Запоминаем
        reaction_settings["last_reactions"].append(time.time())
        if len(reaction_settings["last_reactions"]) > 100:
            reaction_settings["last_reactions"] = reaction_settings["last_reactions"][-100:]
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка установки реакции: {e}")
        return False


def react_to_message_multi(bot, chat_id, message_id, reactions):
    """
    Поставить несколько реакций на сообщение.
    
    Args:
        reactions: список эмодзи (максимум 3)
    """
    if not reactions:
        return False
    
    try:
        # Telegram позволяет до 3 реакций
        reactions = reactions[:3]
        
        # Валидация
        valid_reactions = []
        for r in reactions:
            if is_valid_reaction(r):
                valid_reactions.append(r)
            else:
                valid_reactions.append(reaction_settings["favorite_reaction"])
        
        if not valid_reactions:
            return False
        
        bot.set_message_reaction(
            chat_id,
            message_id,
            [telebot.types.ReactionTypeEmoji(r) for r in valid_reactions]
        )
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка установки реакций: {e}")
        return False


# ============================================================
# 6. УБРАТЬ РЕАКЦИЮ
# ============================================================

def remove_reaction(bot, chat_id, message_id):
    """
    Убрать реакцию с сообщения.
    
    Args:
        bot: telebot instance
        chat_id: ID чата
        message_id: ID сообщения
    
    Returns:
        bool: успех
    """
    try:
        bot.set_message_reaction(
            chat_id,
            message_id,
            []  # пустой список = убрать
        )
        return True
    except Exception as e:
        print(f"⚠️ Ошибка удаления реакции: {e}")
        return False


# ============================================================
# 7. ПОЛУЧИТЬ РЕАКЦИИ
# ============================================================

def get_reactions_on_message(bot, chat_id, message_id):
    """
    Получить реакции на сообщении.
    
    Returns:
        list: список реакций
    """
    try:
        message = bot.get_message(chat_id, message_id)
        if hasattr(message, 'reactions'):
            return message.reactions
    except Exception as e:
        print(f"⚠️ Ошибка получения реакций: {e}")
    return []


def has_our_reaction(bot, chat_id, message_id):
    """
    Проверить, есть ли наша реакция на сообщении.
    
    Returns:
        bool
    """
    reactions = get_reactions_on_message(bot, chat_id, message_id)
    if not reactions:
        return False
    
    bot_id = bot.get_me().id
    for reaction in reactions:
        try:
            if hasattr(reaction, 'recent_reactions'):
                for recent in reaction.recent_reactions:
                    if recent.user and recent.user.id == bot_id:
                        return True
        except Exception:
            pass
    
    return False


def format_reactions(reactions):
    """Форматировать реакции."""
    if not reactions:
        return "Нет реакций"
    
    result = ""
    for reaction in reactions:
        emoji = getattr(reaction, 'emoji', '?')
        count = getattr(reaction, 'count', 0)
        result += f"{emoji} x{count}\n"
    
    return result.strip()


# ============================================================
# 8. ПРОВЕРКА ЛИМИТОВ
# ============================================================

def check_reaction_limit():
    """
    Проверить, не превышен ли лимит реакций в минуту.
    
    Returns:
        bool: можно ли ставить реакцию
    """
    now = time.time()
    
    # Очищаем старые (старше 60 секунд)
    reaction_settings["last_reactions"] = [
        t for t in reaction_settings["last_reactions"]
        if now - t < 60
    ]
    
    return len(reaction_settings["last_reactions"]) < reaction_settings["max_reactions_per_minute"]


# ============================================================
# 9. СТАРЫЕ ФУНКЦИИ (ДЛЯ СОВМЕСТИМОСТИ)
# ============================================================

def detect_emotion_from_text(text):
    """Определить эмоцию из текста (для совместимости)."""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["люблю", "обожаю", "💜", "милый", "милая", "кавай", "ня", "мур"]):
        return "love"
    
    if any(w in text_lower for w in ["😂", "ахах", "лол", "кек", "смешно", "ржака", "ору", "🤣"]):
        return "funny"
    
    if any(w in text_lower for w in ["😭", "грустно", "жаль", "плачу", "печаль", "обидно", "💔"]):
        return "sad"
    
    if any(w in text_lower for w in ["блять", "сука", "пиздец", "злюсь", "бесит", "ненавижу", "😡"]):
        return "angry"
    
    if any(w in text_lower for w in ["😱", "вау", "ого", "нифига", "офигет", "невероятно", "🤯"]):
        return "shock"
    
    if any(w in text_lower for w in ["🔥", "круто", "топ", "класс", "огонь", "супер", "😎"]):
        return "cool"
    
    if any(w in text_lower for w in ["ага", "ну-ну", "конечно", "ясно", "😏"]):
        return "sarcastic"
    
    if any(w in text_lower for w in ["скучно", "нудно", "😴", "🥱"]):
        return "boring"
    
    if any(w in text_lower for w in ["привет", "прив", "здарова", "ку", "hello", "hi"]):
        return "happy"
    
    return "happy"


def choose_reaction(text, user_id=None, user_profiles=None):
    """
    Выбрать реакцию (СТАРАЯ функция, для совместимости).
    
    НЕ ИСПОЛЬЗУЕТСЯ в новой системе — заменена brain_decisions.should_react().
    """
    # Проверяем лимит
    if not check_reaction_limit():
        return None
    
    text_lower = text.lower()
    
    # Приветствие
    if any(w in text_lower for w in ["привет", "прив", "здарова", "ку", "hello", "hi"]):
        if reaction_settings["use_favorite_for_greetings"]:
            return reaction_settings["favorite_reaction"]
        return random.choice(["👋", "❤️", "🔥"])
    
    # Любимые слова
    liked_words = ["люблю", "обожаю", "💜", "спасибо", "спс", "благодарю", "ты лучшая", "ты топ"]
    if any(w in text_lower for w in liked_words):
        if reaction_settings["use_favorite_for_liked"]:
            return reaction_settings["favorite_reaction"]
        return random.choice(["❤️", "🥰", "🫶"])
    
    # По эмоции
    emotion = detect_emotion_from_text(text)
    
    emotion_reactions = {
        "happy": ["❤️", "🔥", "🥰", "😁", "🎉"],
        "sad": ["😢", "🥺", "🫶"],
        "angry": ["😡", "🤬", "👎"],
        "funny": ["😂", "😁", "🤡", "👏"],
        "love": ["❤️", "🥰", "🫶", "😍"],
        "shock": ["😱", "🤯", "😮"],
        "cool": ["😎", "🔥", "👏"],
        "sarcastic": ["😏", "🤔", "👀"],
        "boring": ["🥱", "😴"],
    }
    
    reactions = emotion_reactions.get(emotion, ["❤️", "👏", "🔥"])
    
    if random.random() < 0.3:
        reactions.append(reaction_settings["favorite_reaction"])
    
    reaction = random.choice(reactions)
    return get_valid_reaction(reaction)


def should_react(message, bot, user_profiles):
    """
    Проверить, нужно ли ставить реакцию (СТАРАЯ функция).
    
    НЕ ИСПОЛЬЗУЕТСЯ в новой системе — заменена brain_decisions.should_react().
    """
    # Проверяем лимит
    if not check_reaction_limit():
        return False
    
    # Случайный шанс
    if random.random() > reaction_settings["reaction_chance"]:
        return False
    
    # Не реагируем на свои
    try:
        if message.from_user and message.from_user.id == bot.get_me().id:
            return False
    except Exception:
        pass
    
    # Не реагируем на команды
    text = message.text or ""
    if text.startswith('/') or text.startswith('💟'):
        return False
    
    # Упоминания
    if reaction_settings["auto_react_to_mentions"]:
        try:
            if f"@{bot.get_me().username}" in text or "систмка" in text.lower():
                return True
        except Exception:
            pass
    
    return True


# ============================================================
# 10. НАСТРОЙКИ
# ============================================================

def get_reaction_settings():
    """Получить настройки реакций."""
    return reaction_settings


def format_reaction_settings():
    """Форматировать настройки реакций."""
    lines = [
        "📊 НАСТРОЙКИ РЕАКЦИЙ:",
        f"❤️ Любимая реакция: {reaction_settings['favorite_reaction']}",
        f"🎯 Шанс реакции (старое): {int(reaction_settings['reaction_chance'] * 100)}%",
        f"⏱ Максимум реакций в минуту: {reaction_settings['max_reactions_per_minute']}",
        f"💜 Реагировать на приветствия: {'✅' if reaction_settings['use_favorite_for_greetings'] else '❌'}",
        f"❤️ Любимая на приятные слова: {'✅' if reaction_settings['use_favorite_for_liked'] else '❌'}",
        f"👀 Реагировать на упоминания: {'✅' if reaction_settings['auto_react_to_mentions'] else '❌'}",
        "",
        f"📋 ДОСТУПНО РЕАКЦИЙ: {len(ALL_REACTIONS)}",
        f"❤️ ЛЮБИМЫХ: {', '.join(FAVORITE_REACTIONS)}",
        "",
        "💡 Новая система: реакции решает мозг (brain_decisions)",
    ]
    
    return "\n".join(lines)


# ============================================================
# 11. ЗАГРУЗКА
# ============================================================

print("📊 Модуль реакций загружен")
print(f"❤️ Любимая реакция: {reaction_settings['favorite_reaction']}")
print(f"📋 Доступно реакций: {len(ALL_REACTIONS)}")
print(f"⏱ Лимит: {reaction_settings['max_reactions_per_minute']}/мин")
print(f"💡 Новая система: reactions решает brain_decisions")