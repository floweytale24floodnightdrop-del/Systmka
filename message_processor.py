"""Обработка содержимого сообщений — команды, медиа, РП, ИИ ответы"""

import telebot
import time
import re
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS
import database as db

# ============================================================
# 2. ОБРАБОТКА КОМАНД
# ============================================================

def process_command(bot, message, text, chat_id, user, is_owner_user,
                    profile, pending_battles, bot_status):
    """
    Обработка команд.
    
    Returns:
        bool: True если команда обработана
    """
    # Команды владельца
    if is_owner_user:
        try:
            from handlers_owner import register_owner_handlers
            if register_owner_handlers(
                bot, message, text, chat_id, user, is_owner_user, None
            ):
                return True
        except Exception as e:
            print(f"⚠️ handlers_owner: {e}")
    
    # Экономика
    try:
        from handlers_economy import register_economy_handlers
        if register_economy_handlers(
            bot, message, text, chat_id, user, is_owner_user, profile
        ):
            return True
    except Exception as e:
        print(f"⚠️ handlers_economy: {e}")
    
    # Основные команды
    try:
        from handlers_commands import handle_command
        if handle_command(
            bot, message, text, chat_id, user, is_owner_user,
            profile, pending_battles, bot_status
        ):
            return True
    except Exception as e:
        print(f"⚠️ handlers_commands: {e}")
    
    # РП и OSINT
    try:
        from handlers_rp_osint import handle_rp_osint_commands
        if handle_rp_osint_commands(
            bot, message, text, chat_id, user, profile,
            pending_battles, bot_status
        ):
            return True
    except Exception as e:
        print(f"⚠️ handlers_rp_osint: {e}")
    
    return False

# ============================================================
# 3. ОБРАБОТКА МЕДИА
# ============================================================

def process_media(bot, message, chat_id, user, is_owner_user):
    """
    Обработка медиа-сообщений.
    
    Returns:
        bool: True если медиа обработано
    """
    try:
        from handlers_media import register_media_handlers
        return register_media_handlers(bot, message, chat_id, user, is_owner_user)
    except Exception as e:
        print(f"⚠️ handlers_media: {e}")
        return False

# ============================================================
# 4. ОБРАБОТКА РП
# ============================================================

def process_rp(bot, message, text, chat_id, user, profile=None,
               pending_battles=None, bot_status=None):
    """
    Обработка РП-команд.
    
    ИСПРАВЛЕНО: если profile/pending_battles/bot_status не переданы,
    создаём заглушки вместо передачи None.
    """
    if profile is None:
        profile = {"messages": 0}
    
    if pending_battles is None:
        pending_battles = {}
    
    if bot_status is None:
        bot_status = {
            "running": False,
            "messages_processed": 0,
            "errors_count": 0,
        }
    
    try:
        from handlers_rp_osint import handle_rp_osint_commands
        return handle_rp_osint_commands(
            bot, message, text, chat_id, user,
            profile, pending_battles, bot_status
        )
    except Exception as e:
        print(f"⚠️ process_rp: {e}")
        return False

# ============================================================
# 5. ОБРАБОТКА ИИ ОТВЕТА
# ============================================================

def process_ai_response(bot, message, text, chat_id, user, bot_status):
    """
    Обработка ИИ-ответа.
    """
    # Ленивый импорт внутри функции — чтобы не было цикла
    try:
        from ai_router import (
            ask_ai, ask_for_rp, ask_for_chat,
            ask_for_command, ask_for_generation, ask_for_security,
        )
        from personality import get_personality_for_prompt
        from system_prompt import SYSTEM_PROMPT
        from handlers_main import detect_task_type_from_message
        from progress import (
            show_typing_animation,
            delete_progress_message,
            replace_with_answer,
        )
        from fatigue import is_tired, apply_fatigue_to_text
        from self_reflection import reflect_on_answer
        from consciousness import remember
        from reactions import get_favorite_reaction, react_to_message
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать модули для ИИ: {e}")
        return
    
    try:
        bot_status["total_ai_requests"] = bot_status.get("total_ai_requests", 0) + 1
        
        task_type = detect_task_type_from_message(text, message)
        system_prompt = SYSTEM_PROMPT + get_personality_for_prompt()
        
        # Выбор функции по типу задачи
        if task_type in ("rp", "roleplay", "emotional_chat", "creative_writing"):
            answer, model, success = ask_for_rp(text, system_prompt, max_tokens=300)
        elif task_type in ("commands", "glitches", "database", "error_fixing", "status"):
            answer, model, success = ask_for_command(text, system_prompt, max_tokens=150)
        elif task_type in ("image_generation", "music_search", "information_search", "battle_analysis"):
            answer, model, success = ask_for_generation(text, system_prompt, max_tokens=400)
        elif task_type in ("security", "doxing", "vpn", "damage"):
            answer, model, success = ask_for_security(text, system_prompt, max_tokens=300)
        else:
            answer, model, success = ask_ai(
                text, system_prompt, task_type="general_chat", max_tokens=200
            )
        
        if not success:
            answer = "❌ Не удалось получить ответ от ИИ. Попробуй позже."
        
        # Усталость
        if is_tired():
            answer = apply_fatigue_to_text(answer)
        
        sent_msg = bot.reply_to(message, answer)
        
        # Рефлексия
        try:
            reflect_on_answer(text, answer, user.id)
        except Exception:
            pass
        
        # Память
        try:
            remember(f"Ответила {user.first_name}")
        except Exception:
            pass
        
        # Реакция
        if hasattr(sent_msg, "message_id"):
            try:
                react_to_message(
                    bot, chat_id, sent_msg.message_id,
                    get_favorite_reaction()
                )
            except Exception:
                pass
    
    except Exception as e:
        try:
            from error_reporter import notify_error
            from self_learning import learn_from_error
            notify_error(bot, OWNER_IDS, e, chat_id, user.first_name, text)
            learn_from_error(str(e))
        except Exception:
            print(f"⚠️ process_ai_response: {e}")

# ============================================================
# 6. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def process_message_content(bot, message, text, chat_id, user,
                            is_owner_user, profile, pending_battles, bot_status):
    """
    Обработка содержимого сообщения.
    
    Returns:
        bool: True если сообщение обработано
    """
    # 1. Игры
    try:
        from games import process_game_input
        if process_game_input(bot, chat_id, text):
            return True
    except Exception:
        pass
    
    # 2. Команды
    if process_command(
        bot, message, text, chat_id, user,
        is_owner_user, profile, pending_battles, bot_status
    ):
        return True
    
    # 3. Медиа
    if process_media(bot, message, chat_id, user, is_owner_user):
        return True
    
    # 4. ИИ-ответ
    process_ai_response(bot, message, text, chat_id, user, bot_status)
    return True

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📨 Message Processor загружен")