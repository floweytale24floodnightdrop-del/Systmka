"""Основной обработчик сообщений — анализ, РП, игры, ИИ + мозг + решения"""

import telebot
import json
import os
import re
import time
import random
import requests
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, OPENROUTER_KEY, OPENROUTER_KEYS
from config_network import check_internet
from system_prompt import SYSTEM_PROMPT
import database as db

# ============================================================
# 1.5 МОЗГ (НОВОЕ!)
# ============================================================

from brain_init import (
    on_user_message,
    on_ai_response,
    format_brain_state_for_prompt,
    get_emotion_hint,
    is_initialized as brain_is_initialized,
)

# ============================================================
# 1.6 РЕШЕНИЯ МОЗГА (НОВОЕ!)
# ============================================================

from brain_decisions import (
    should_respond,
    should_react,
    should_merge_messages,
)

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

BATTLES_FILE = "pending_battles.json"
pending_battles = {}

# Буфер сообщений для объединения (chat_id → список сообщений)
message_buffer = {}
BUFFER_TIMEOUT = 3.0  # секунды

ANALYZE_MESSAGE_CHANCE = 0.3
REFLECT_ON_ANSWER_CHANCE = 0.1
UPDATE_IMPRESSION_CHANCE = 0.05


def load_pending_battles():
    """Загрузить ожидающие битвы"""
    global pending_battles
    try:
        if os.path.exists(BATTLES_FILE):
            with open(BATTLES_FILE, "r", encoding="utf-8") as f:
                pending_battles = json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки битв: {e}")
        pending_battles = {}


def save_pending_battles():
    """Сохранить ожидающие битвы"""
    try:
        with open(BATTLES_FILE, "w", encoding="utf-8") as f:
            json.dump(pending_battles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения битв: {e}")


load_pending_battles()

# ============================================================
# 3. ОПРЕДЕЛЕНИЕ ТИПА ЗАДАЧИ
# ============================================================

def detect_task_type_from_message(text, message):
    """Определить тип задачи по сообщению."""
    if not text:
        return "conversation"
    
    text_lower = text.lower()
    
    rp_keywords = ["*", "действие", "ролевая", "рп", "roleplay"]
    if any(kw in text_lower for kw in rp_keywords) and len(text) > 20:
        return "rp"
    
    if text.startswith('💟') or text.startswith('/'):
        if any(kw in text_lower for kw in ["бой", "топ", "профиль", "список", "статус", "премиум"]):
            return "commands"
        if any(kw in text_lower for kw in ["селфи", "музыка", "картинк"]):
            return "image_generation"
        if any(kw in text_lower for kw in ["докс", "урон", "защита"]):
            return "security"
        return "commands"
    
    if "?" in text:
        return "question_answering"
    
    if len(text) > 50:
        return "general_chat"
    
    return "conversation"


# ============================================================
# 4. ОСНОВНОЙ ОБРАБОТЧИК
# ============================================================

def handle_message(bot, message, debug_settings, bot_status):
    """Обработка входящего сообщения с полной логикой"""
    
    from bot import (
        check_startup_grace, check_rate_limit, is_owner,
        is_private_chat, is_group_chat, check_ftf24,
        send_to_user, get_chat_members, check_owner_present,
        update_chat_info, log_error,
    )
    
    # === 1. Grace-период ===
    if check_startup_grace():
        return
    
    # === 2. Проверка интернета ===
    try:
        internet_state = check_internet()
        if internet_state == "offline":
            if f"@{bot.get_me().username}" in (message.text or ""):
                bot.reply_to(message, "Я занята или сплю. Отвечу позже!🫰")
            return
        elif internet_state == "restored":
            for oid in OWNER_IDS:
                try:
                    bot.send_message(oid, "✅ Интернет восстановлен!")
                except Exception:
                    pass
    except Exception as e:
        try:
            from error_reporter import notify_error
            notify_error(bot, OWNER_IDS, e)
        except Exception:
            pass
        return
    
    # === 3. Rate limit ===
    if not check_rate_limit(message.chat.id):
        return
    
    # === 4. Обновляем инфо о чате ===
    update_chat_info(message)
    
    # === 5. Данные пользователя ===
    user = message.from_user
    text = message.text or ""
    chat_id = message.chat.id
    is_private = is_private_chat(message)
    is_group = is_group_chat(message)
    is_owner_user = is_owner(user.id)
    
    # ============================================================
    # 5.5 МОЗГ: обработка сообщения (НОВОЕ!)
    # ============================================================
    
    brain_hint = ""
    if brain_is_initialized():
        try:
            brain_hint = on_user_message(bot, message, user, text)
        except Exception as e:
            print(f"⚠️ Ошибка мозга (on_user_message): {e}")
    
    # === 6. Фильтр сообщений ===
    try:
        from message_filter import filter_message
        filter_result = filter_message(text)
    except Exception:
        filter_result = {"use_ai": True}
    
    # === 7. Проверка сна ===
    try:
        from sleep import is_sleeping, get_sleep_message, get_wake_message
        sleep_state = is_sleeping()
        if sleep_state == "woke_up":
            for oid in OWNER_IDS:
                try:
                    bot.send_message(oid, get_wake_message())
                except Exception:
                    pass
        elif sleep_state:
            if f"@{bot.get_me().username}" in text or "систмка" in text.lower():
                bot.reply_to(message, get_sleep_message())
            return
    except Exception:
        pass
    
    # === 8. Усталость ===
    try:
        from fatigue import increase_fatigue, apply_fatigue_to_text, is_tired
        increase_fatigue(0.05)
    except Exception:
        def is_tired():
            return False
        def apply_fatigue_to_text(t):
            return t
    
    # === 9. Количество участников ===
    member_count = 0
    if is_group:
        try:
            member_count = bot.get_chat_member_count(chat_id)
        except Exception:
            pass
    
    # === 10. Поведение ===
    try:
        from behavior import get_behavior
        behavior = get_behavior(message.chat.type, member_count, user.id)
    except Exception:
        behavior = {}
    
    # === 11. Профиль пользователя ===
    if user.id not in db.user_profiles:
        db.user_profiles[user.id] = {
            "username": f"@{user.username}" if user.username else "",
            "first_name": user.first_name or "",
            "is_bot": user.is_bot,
            "messages": 0,
            "first_seen": datetime.now().isoformat(),
            "behavior_score": 50,
            "gender": "unknown",
            "last_gift_time": None,
        }
    
    profile = db.user_profiles[user.id]
    profile["messages"] = profile.get("messages", 0) + 1
    db.user_last_seen[user.id] = datetime.now().isoformat()
    
    # === 12. Обновляем пол по речи ===
    try:
        from database import update_user_gender
        update_user_gender(user.id, text)
    except Exception:
        pass
    
    # === 13. Анализ поведения ===
    try:
        from behavior import analyze_user_behavior
        analyze_user_behavior(text, user.id)
    except Exception:
        pass
    
    # === 14. Привязанность ===
    try:
        from attachments import increase_attachment
        increase_attachment(user.id, 0.1)
    except Exception:
        pass
    
    # === 15. Эмоции ===
    try:
        from emotions import react_to_message as process_emotions
        process_emotions(text)
    except Exception:
        pass
    
    # === 16. Анализ сообщений (30%) ===
    if random.random() < ANALYZE_MESSAGE_CHANCE:
        try:
            from message_analyzer import analyze_message, analysis_data, save_analysis
            
            analysis = analyze_message(text, user.id, user.first_name)
            
            user_id_str = str(user.id)
            if user_id_str not in analysis_data["users"]:
                analysis_data["users"][user_id_str] = {
                    "total_score": 0, "count": 0, "avg_score": 0
                }
            
            user_data = analysis_data["users"][user_id_str]
            user_data["total_score"] += analysis.get("score", 5)
            user_data["count"] += 1
            user_data["avg_score"] = user_data["total_score"] / user_data["count"]
            user_data["last_analysis"] = datetime.now().isoformat()
            
            if chat_id not in analysis_data["conversations"]:
                analysis_data["conversations"][chat_id] = []
            
            analysis_data["conversations"][chat_id].append({
                "user_id": user.id,
                "text": text[:200],
                "score": analysis.get("score", 5),
                "time": datetime.now().isoformat(),
            })
            
            if len(analysis_data["conversations"][chat_id]) > 100:
                analysis_data["conversations"][chat_id] = analysis_data["conversations"][chat_id][-100:]
            
            save_analysis()
        except Exception:
            pass
    
    # === 17. Впечатления (5%) ===
    if text and len(text) > 10 and random.random() < UPDATE_IMPRESSION_CHANCE:
        try:
            from impression_manager import update_random_impression_on_chat
            update_random_impression_on_chat(text)
        except Exception:
            pass
    
    # === 18. История ===
    try:
        from history import save_message
        save_message(chat_id, user.id, user.first_name, text, message.chat.type)
    except Exception:
        pass
    
    # === 19. Бонусы ===
    if profile["messages"] % 50 == 0:
        db.add_glitches(user.id, 5, OWNER_IDS)
    if profile["messages"] % 100 == 0:
        db.add_glitches(user.id, 10, OWNER_IDS)
    
    # === 20. Модерация ===
    try:
        from moderation import check_moderation
        from bot import is_admin_or_owner
        
        mod_result = check_moderation(
            message, bot,
            is_admin_or_owner_func=is_admin_or_owner,
            is_owner_func=is_owner,
        )
        
        if mod_result.get("action") != "none":
            return
    except Exception as e:
        print(f"⚠️ Ошибка модерации: {e}")
    
    # === 21. Игра Троян ===
    if text and text.strip() and text.strip().isdigit():
        try:
            from trojan_game import process_trojan_guess
            if process_trojan_guess(message, user, text, bot):
                return
        except Exception as e:
            print(f"⚠️ Ошибка трояна: {e}")
    
    # ============================================================
    # 22. РЕШЕНИЕ МОЗГА: ОТВЕЧАТЬ ИЛИ НЕТ (НОВОЕ!)
    # ============================================================
    
    decision = None
    if brain_is_initialized():
        try:
            decision = should_respond(message, text, user.id)
            
            if not decision["respond"]:
                # Замораживаем запрос
                try:
                    from frozen_requests import freeze_request
                    freeze_request(user.id, user.username, user.first_name, text, chat_id, decision["reason"])
                except Exception:
                    pass
                return
        except Exception as e:
            print(f"⚠️ Ошибка решения мозга: {e}")
            decision = None
    
    # === 23. FTF24 в ЛС ===
    if is_private and not is_owner_user:
        try:
            from premium import check_premium
            has_premium = check_premium(user.id, OWNER_IDS)
            if not check_ftf24(user) and not has_premium:
                if "💟" in text or text.startswith('/'):
                    return
                bot.reply_to(
                    message,
                    "У тебя нет приписки #FTF24 в нике, я не хочу с тобой разговаривать."
                )
                return
        except Exception:
            pass
    
    # ============================================================
    # 24. РЕАКЦИЯ (НОВОЕ!)
    # ============================================================
    
    if brain_is_initialized():
        try:
            from reactions import react_to_message, remove_reaction
            
            react_decision = should_react(message, text, user.id)
            
            if react_decision.get("remove"):
                try:
                    remove_reaction(bot, chat_id, message.message_id)
                except Exception:
                    pass
            elif react_decision["react"] and react_decision["reaction"]:
                if react_decision["target"] == "user_message":
                    react_to_message(bot, chat_id, message.message_id, react_decision["reaction"])
                    print(f"🎭 Реакция: {react_decision['reaction']} (сарказм: {react_decision['sarcastic']})")
        except Exception as e:
            print(f"⚠️ Ошибка реакции: {e}")
    
    # === 25. Опросы ===
    if hasattr(message, 'poll') and message.poll is not None:
        return
    
    # === 26. Безопасность ===
    try:
        from security import security_check
        security_result = security_check(text, user.id, user.username)
        if not security_result.get("is_safe", True):
            return
    except Exception:
        pass
    
    # === 27. Игры ===
    try:
        from games import process_game_input
        if process_game_input(bot, chat_id, text):
            return
    except Exception:
        pass
    
    # === 28. Анимация ===
    from progress import show_typing_animation, delete_progress_message, get_animation_style
    
    animation_msg = None
    if text.startswith('💟') or text.startswith('/'):
        style = get_animation_style(text)
        try:
            if message.reply_to_message:
                animation_msg = show_typing_animation(bot, chat_id, 5, style)
            elif chat_id in db.history and len(db.history[chat_id]) > 1:
                animation_msg = show_typing_animation(bot, chat_id, 5, style)
        except Exception:
            pass
    
    # === 29. Команды ===
    
    if is_owner_user and is_private:
        try:
            from handlers_owner import register_owner_handlers
            if register_owner_handlers(
                bot, message, text, chat_id, user, is_owner_user, debug_settings
            ):
                if animation_msg:
                    delete_progress_message(bot, chat_id, animation_msg.message_id)
                return
        except Exception as e:
            log_error(e, "handlers_owner")
    
    try:
        from handlers_economy import register_economy_handlers
        if register_economy_handlers(
            bot, message, text, chat_id, user, is_owner_user, profile
        ):
            if animation_msg:
                delete_progress_message(bot, chat_id, animation_msg.message_id)
            return
    except Exception as e:
        log_error(e, "handlers_economy")
    
    try:
        from handlers_media import register_media_handlers
        if register_media_handlers(bot, message, chat_id, user, is_owner_user):
            if animation_msg:
                delete_progress_message(bot, chat_id, animation_msg.message_id)
            return
    except Exception as e:
        log_error(e, "handlers_media")
    
    try:
        from handlers_commands import handle_command
        if handle_command(
            bot, message, text, chat_id, user, is_owner_user,
            profile, pending_battles, bot_status
        ):
            if animation_msg:
                delete_progress_message(bot, chat_id, animation_msg.message_id)
            save_pending_battles()
            return
    except Exception as e:
        log_error(e, "handlers_commands")
    
    try:
        from handlers_rp_osint import handle_rp_osint_commands
        if handle_rp_osint_commands(
            bot, message, text, chat_id, user, profile,
            pending_battles, bot_status
        ):
            if animation_msg:
                delete_progress_message(bot, chat_id, animation_msg.message_id)
            save_pending_battles()
            return
    except Exception as e:
        log_error(e, "handlers_rp_osint")
    
    # ============================================================
    # 30. ОТВЕТЫ ЧЕРЕЗ ИИ
    # ============================================================
    
    if not filter_result.get("use_ai", True):
        bot_status["ai_requests_saved"] = bot_status.get("ai_requests_saved", 0) + 1
        return
    
    if chat_id not in db.history:
        db.history[chat_id] = []
    
    context = f"Пользователь: {user.first_name}"
    if user.username:
        context += f" (@{user.username})"
    
    if animation_msg:
        delete_progress_message(bot, chat_id, animation_msg.message_id)
        animation_msg = None
    
    ai_animation_msg = None
    if not text.startswith('/') and not text.startswith('💟'):
        try:
            if message.reply_to_message:
                ai_animation_msg = show_typing_animation(bot, chat_id, 8, "default")
            elif chat_id in db.history and len(db.history[chat_id]) > 1:
                ai_animation_msg = show_typing_animation(bot, chat_id, 8, "default")
        except Exception:
            pass
    
    try:
        bot_status["total_ai_requests"] = bot_status.get("total_ai_requests", 0) + 1
        
        from ai_router import (
            ask_ai, ask_for_rp, ask_for_chat,
            ask_for_command, ask_for_generation, ask_for_security,
        )
        from personality import get_personality_for_prompt
        
        task_type = detect_task_type_from_message(text, message)
        
        # ============================================================
        # 30.1 СБОРКА ПРОМТА (С МОЗГОМ!)
        # ============================================================
        
        system_prompt = SYSTEM_PROMPT + get_personality_for_prompt() + "\n\n" + context
        
        if brain_is_initialized():
            try:
                system_prompt += "\n\n" + format_brain_state_for_prompt()
                if brain_hint:
                    system_prompt += "\n\nПОДСКАЗКА ОТ МОЗГА:\n" + brain_hint
            except Exception as e:
                print(f"⚠️ Ошибка добавления мозга в промт: {e}")
        
        try:
            from answer_evaluator import get_style_for_user, should_adapt_to_user
            if should_adapt_to_user(user.id):
                style = get_style_for_user(user.id)
                system_prompt += (
                    f"\n\nУЧТИ СТИЛЬ ПОЛЬЗОВАТЕЛЯ:\n"
                    f"Теплота: {style.get('warmth', 5)}/10\n"
                    f"Формальность: {style.get('formality', 5)}/10\n"
                    f"Юмор: {style.get('humor', 5)}/10\n"
                    f"Сарказм: {style.get('sarcasm', 5)}/10"
                )
        except Exception:
            pass
        
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
        
        if is_tired():
            answer = apply_fatigue_to_text(answer)
        
        if brain_is_initialized():
            try:
                on_ai_response(answer)
            except Exception as e:
                print(f"⚠️ Ошибка мозга (on_ai_response): {e}")
        
        if random.random() < REFLECT_ON_ANSWER_CHANCE:
            try:
                from self_reflection import reflect_on_answer
                reflect_on_answer(text, answer, user.id)
            except Exception:
                pass
        
        from progress import replace_with_answer
        
        if ai_animation_msg:
            if replace_with_answer(bot, chat_id, ai_animation_msg.message_id, answer):
                db.history[chat_id].append({"role": "user", "content": f"{user.first_name}: {text}"})
                db.history[chat_id].append({"role": "assistant", "content": answer})
                try:
                    from consciousness import remember
                    remember(f"Ответила {user.first_name}")
                except Exception:
                    pass
                return
        
        if ai_animation_msg:
            delete_progress_message(bot, chat_id, ai_animation_msg.message_id)
        
        db.history[chat_id].append({"role": "user", "content": f"{user.first_name}: {text}"})
        db.history[chat_id].append({"role": "assistant", "content": answer})
        
        sent_msg = bot.reply_to(message, answer)
        
        try:
            from consciousness import remember
            remember(f"Ответила {user.first_name}")
        except Exception:
            pass
        
        if hasattr(sent_msg, 'message_id'):
            try:
                from reactions import get_favorite_reaction, react_to_message
                react_to_message(
                    bot, chat_id, sent_msg.message_id, get_favorite_reaction()
                )
            except Exception:
                pass
    
    except Exception as e:
        if ai_animation_msg:
            try:
                delete_progress_message(bot, chat_id, ai_animation_msg.message_id)
            except Exception:
                pass
        
        try:
            from error_reporter import notify_error
            from self_learning import learn_from_error
            notify_error(bot, OWNER_IDS, e, chat_id, user.first_name, text)
            learn_from_error(str(e))
        except Exception:
            print(f"❌ Ошибка в handle_message: {e}")

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("📨 Основной обработчик сообщений загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"🧠 Мозг: {'✅ подключён' if brain_is_initialized() else '⚠️ не инициализирован'}")
print(f"🎯 Решения мозга: ✅ подключены")
print(f"⚡ Оптимизация HTTP:")
print(f"   • Анализ сообщений: {int(ANALYZE_MESSAGE_CHANCE * 100)}%")
print(f"   • Рефлексия ответов: {int(REFLECT_ON_ANSWER_CHANCE * 100)}%")
print(f"   • Обновление впечатлений: {int(UPDATE_IMPRESSION_CHANCE * 100)}%")