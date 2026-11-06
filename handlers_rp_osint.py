"""Обработка РП-команд (односложные действия) и автоопределение РП игры"""

import telebot
import re
import time
import random
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS
import database as db

# ============================================================
# 2. ОПРЕДЕЛЕНИЕ НАЧАЛА РП ИГРЫ
# ============================================================

def is_rp_game_text(text, user_id=None):
    """
    Определить, является ли текст частью РП игры (НЕ командой!).
    
    Отличает РП игру от РП команд.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Признаки РП игры
    rp_game_markers = [
        "*", "—", "-",
        "действие", "местность", "вокруг",
        "☾", "☽", "𖤓", "♡", "✪", "❂", "✦",
        "——", "─", "⋆", "✧",
    ]
    
    for marker in rp_game_markers:
        if marker in text:
            if not is_rp_command(text):
                return True
    
    # Проверка на действия в звёздочках
    if re.search(r'\*[^*]+\*', text):
        if not is_rp_command(text):
            return True
    
    # Проверка на речь с тире
    if re.search(r'[—\-]\s*"[^"]+"', text) or re.search(r'[—\-]\s*[А-Яа-я]', text):
        if not is_rp_command(text):
            return True
    
    # Длинные сообщения с описанием
    if len(text) > 80 and ("." in text or "!" in text or "?" in text):
        if not is_rp_command(text):
            if any(marker in text for marker in ["я ", "ты ", "он ", "она ", "мы ", "они "]):
                return True
    
    return False

def is_rp_command(text):
    """Проверить, является ли текст РП командой (погладить, поцеловать и тд)"""
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    # Список РП команд (односложные действия)
    rp_commands_list = [
        "кусь", "чмок", "обнять", "поцеловать", "ударить", "погладить",
        "укусить", "засосать", "выебать", "трахнуть", "отшлепать",
        "прижать", "лизнуть", "убить", "воскресить", "вылечить",
        "обнять крепко", "поцеловать в шею", "поцеловать в губы",
        "взять за руку", "прижать к себе", "повалить", "защекотать",
    ]
    
    for cmd in rp_commands_list:
        if text_lower == cmd or text_lower.startswith(cmd + " ") or text_lower.startswith(cmd + " @"):
            return True
    
    return False

# ============================================================
# 3. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def handle_rp_osint_commands(bot, message, text, chat_id, user, profile,
                             pending_battles, bot_status):
    """
    Обработать РП и OSINT команды.
    
    Returns:
        bool: True если команда обработана
    """
    
    # ============================================================
    # 3.1 РП ИГРА vs РП КОМАНДА
    # ============================================================
    
    if is_rp_game_text(text, user.id):
        return _handle_rp_game(bot, message, text, chat_id, user)
    
    # ============================================================
    # 3.2 РП КОМАНДЫ (ОДНОСЛОЖНЫЕ ДЕЙСТВИЯ)
    # ============================================================
    
    if text:
        # Кастомные команды
        try:
            from rp_commands import get_rp_command
            custom_action = get_rp_command(text.lower(), user.id)
            if custom_action:
                return _handle_custom_rp(bot, message, user, custom_action)
        except Exception:
            pass
        
        # Стандартные команды
        for trigger, action in db.rp_commands.items():
            if trigger.lower() == text.lower():
                return _handle_standard_rp(bot, message, user, action)
    
    # ============================================================
    # 3.3 РП-КОМАНДЫ В ЛС (С ЗАПРОСОМ)
    # ============================================================
    
    try:
        from rp_commands import get_all_rp_commands, handle_rp_command_with_request
        all_rp_commands = get_all_rp_commands()
        
        for trigger, action_template in all_rp_commands.items():
            if text.lower().startswith(trigger.lower()) or text.lower() == trigger.lower():
                return _handle_rp_with_request(
                    bot, message, text, user, trigger,
                    action_template, handle_rp_command_with_request
                )
    except Exception:
        pass
    
    # ============================================================
    # 3.4 ПРОСМОТР ЗАПРОСОВ
    # ============================================================
    
    if "💟Мои запросы" in text or text.lower() == "мои запросы":
        return _handle_my_requests(bot, message, user)
    
    # ============================================================
    # 3.5 ПРИНЯТИЕ ЗАПРОСА
    # ============================================================
    
    if text.startswith("/rp_accept"):
        return _handle_accept_request(bot, message, text, user)
    
    # ============================================================
    # 3.6 ОТКЛОНЕНИЕ ЗАПРОСА
    # ============================================================
    
    if text.startswith("/rp_decline"):
        return _handle_decline_request(bot, message, text, user)
    
    # ============================================================
    # 3.7 ДОКС
    # ============================================================
    
    if "💟Докс" in text:
        return _handle_dox(bot, message, text, chat_id, user)
    
    # ============================================================
    # 3.8 УРОН
    # ============================================================
    
    if "💟Урон" in text:
        return _handle_damage(bot, message, text, chat_id, user)
    
    return False

# ============================================================
# 4. ОБРАБОТЧИКИ
# ============================================================

def _handle_rp_game(bot, message, text, chat_id, user):
    """Обработка РП игры"""
    try:
        from roleplay import generate_rp_post, rp_data, auto_join_rp_if_needed
        
        # Систмка может присоединиться
        auto_join_rp_if_needed(bot, message, text, chat_id, user.id)
        
        # Если Систмка в РП — генерируем ответ
        chat_id_str = str(chat_id)
        if chat_id_str in rp_data.get("systmka_in_rp", {}) and rp_data["systmka_in_rp"][chat_id_str]:
            post, error = generate_rp_post(user.id, text, chat_id, bot)
            if post:
                bot.send_message(chat_id, post)
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка РП игры: {e}")
        return True

def _handle_custom_rp(bot, message, user, custom_action):
    """Обработка кастомной РП команды"""
    target_name = "никого"
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_name = target_user.first_name
    
    response = custom_action.replace("<Ты>", user.first_name).replace("<Пользователь>", target_name)
    bot.reply_to(message, response)
    return True

def _handle_standard_rp(bot, message, user, action):
    """Обработка стандартной РП команды"""
    target_name = "никого"
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_name = target_user.first_name
    
    response = action.replace("<Ты>", user.first_name).replace("<Пользователь>", target_name)
    bot.reply_to(message, response)
    return True

def _handle_rp_with_request(bot, message, text, user, trigger, action_template, handle_func):
    """Обработка РП команды с запросом в ЛС"""
    try:
        anonymous = False
        clean_text = text
        
        if text.endswith('*'):
            anonymous = True
            clean_text = text[:-1].strip()
        
        target_user = None
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            mention = re.search(r'@(\w+)', clean_text)
            if mention:
                username = mention.group(1)
                for uid, p in db.user_profiles.items():
                    if p.get("username", "").replace("@", "") == username:
                        try:
                            target_user = bot.get_chat(uid)
                        except Exception:
                            pass
                        break
        
        if target_user and message.chat.type == "private":
            success, msg = handle_func(
                bot, message, trigger, target_user, action_template, anonymous
            )
            bot.reply_to(message, msg)
            return True
        
        elif target_user and message.chat.type != "private":
            action = action_template.replace("<Ты>", user.first_name).replace(
                "<Пользователь>", target_user.first_name
            )
            bot.reply_to(message, action)
            return True
        
        else:
            action = action_template.replace("<Ты>", user.first_name).replace(
                "<Пользователь>", "никого"
            )
            bot.reply_to(message, action)
            return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True

def _handle_my_requests(bot, message, user):
    """Просмотр запросов пользователя"""
    try:
        from database import get_pending_requests
        
        pending = get_pending_requests(user.id)
        
        if not pending:
            bot.reply_to(message, "📭 У тебя нет ожидающих запросов")
            return True
        
        response = "📋 ТВОИ ЗАПРОСЫ:\n\n"
        for req in pending:
            try:
                from_user = bot.get_chat(req["from_user"])
                name = from_user.first_name or "Неизвестный"
            except Exception:
                name = f"User {req['from_user']}"
            
            response += f"• {name} хочет {req['action']}\n"
            response += f"  ID: {req['id']}\n\n"
        
        response += "Чтобы принять: /rp_accept <ID>\n"
        response += "Чтобы отклонить: /rp_decline <ID>"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_accept_request(bot, message, text, user):
    """Принятие РП-запроса"""
    try:
        from database import accept_rp_request, rp_requests
        from rp_commands import get_all_rp_commands
        
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используй: /rp_accept <ID>")
            return True
        
        try:
            request_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Неверный ID")
            return True
        
        success, error = accept_rp_request(request_id, user.id)
        
        if success:
            req = rp_requests[str(request_id)]
            from_user = bot.get_chat(req["from_user"])
            
            all_commands = get_all_rp_commands()
            action_template = all_commands.get(req["action"], f"{req['action']}")
            action = action_template.replace("<Ты>", from_user.first_name).replace(
                "<Пользователь>", user.first_name
            )
            
            bot.send_message(user.id, f"✅ Запрос принят!\n\n{action}")
            
            try:
                bot.send_message(
                    from_user.id,
                    f"✅ {user.first_name} принял(а) твой запрос!\n\n{action}"
                )
            except Exception:
                pass
        else:
            bot.reply_to(message, f"❌ {error}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_decline_request(bot, message, text, user):
    """Отклонение РП-запроса"""
    try:
        from database import decline_rp_request, rp_requests
        
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используй: /rp_decline <ID>")
            return True
        
        try:
            request_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Неверный ID")
            return True
        
        success, error = decline_rp_request(request_id, user.id)
        
        if success:
            req = rp_requests[str(request_id)]
            from_user = bot.get_chat(req["from_user"])
            
            bot.send_message(user.id, "❌ Запрос отклонён")
            
            try:
                bot.send_message(
                    from_user.id,
                    f"❌ {user.first_name} отклонил(а) твой запрос"
                )
            except Exception:
                pass
        else:
            bot.reply_to(message, f"❌ {error}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_dox(bot, message, text, chat_id, user):
    """Реальный докс (только владелец)"""
    try:
        from osint_engine import full_dox_real, format_dox_result_real
        from progress import show_loading_animation, delete_progress_message
        
        if user.id not in OWNER_IDS:
            bot.reply_to(message, "❌ Только владелец может использовать докс!")
            return True
        
        query = text.replace("💟Докс", "").strip()
        if not query:
            bot.reply_to(message, "❌ Укажи цель: 💟Докс @юзер / номер / почта / IP")
            return True
        
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            query = target.username or str(target.id)
        
        progress_msg = show_loading_animation(bot, chat_id, 30)
        
        try:
            result = full_dox_real(query)
            response = format_dox_result_real(result)
        except Exception as e:
            response = f"❌ Ошибка докса: {e}"
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                bot.send_message(chat_id, part)
        else:
            bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_damage(bot, message, text, chat_id, user):
    """Урон (только владелец)"""
    try:
        from osint_engine import execute_damage, format_damage_result
        from progress import show_loading_animation, delete_progress_message
        
        if user.id not in OWNER_IDS:
            bot.reply_to(message, "❌ Только владелец может наносить урон!")
            return True
        
        parts = text.replace("💟Урон", "").strip().split()
        if not parts:
            bot.reply_to(message, "❌ Укажи цель: 💟Урон @юзер")
            return True
        
        target = parts[0]
        count = int(parts[1]) if len(parts) > 1 else 10
        cycles = int(parts[2]) if len(parts) > 2 else 3
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target = target_user.username or str(target_user.id)
        
        bot.reply_to(
            message,
            f"💥 Начинаю урон по {target}...\n📊 Аккаунтов: {count}, циклов: {cycles}"
        )
        
        progress_msg = show_loading_animation(bot, chat_id, 60 * cycles)
        result = execute_damage(target, count=count, cycles=cycles)
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        bot.reply_to(message, format_damage_result(result))
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("🎭 Обработчик РП и OSINT команд загружен")
print("📌 РП игра и РП команды разделены")
print(f"👑 Владельцев: {len(OWNER_IDS)}")