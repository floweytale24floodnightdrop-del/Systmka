"""Обработка основных команд — статус, бой, топ, селфи, музыка, профиль"""

import telebot
import time
import re
import random
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, HELPER_IDS
import database as db

# ============================================================
# 2. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def handle_command(bot, message, text, chat_id, user, is_owner_user,
                   profile, pending_battles, bot_status):
    """
    Обработать команду.
    
    Returns:
        bool: True если команда обработана
    """
    
    # ============================================================
    # 2.1 СТАТУС (ПОЛНАЯ ИНФОРМАЦИЯ)
    # ============================================================
    
    if "💟Статус" in text or text.lower() in ("/status", "статус"):
        return _handle_status(bot, message, chat_id, user, is_owner_user, bot_status)
    
    # ============================================================
    # 2.2 БОЙ (ПРИНЯТИЕ ВЫЗОВА)
    # ============================================================
    
    if text.strip() == "💟Бой" and user.id in pending_battles:
        return _handle_battle_accept(
            bot, message, user, pending_battles
        )
    
    # ============================================================
    # 2.3 ТОП
    # ============================================================
    
    if "💟Топ" in text:
        return _handle_top(bot, message)
    
    # ============================================================
    # 2.4 СЕЛФИ
    # ============================================================
    
    if "💟Селфи" in text:
        return _handle_selfie(bot, message, text, chat_id, user)
    
    # ============================================================
    # 2.5 МУЗЫКА
    # ============================================================
    
    if "💟Музыка" in text:
        return _handle_music(bot, message, text, chat_id, user)
    
    # ============================================================
    # 2.6 ПРОФИЛЬ
    # ============================================================
    
    if "💟Профиль" in text:
        return _handle_profile(bot, message, user)
    
    # ============================================================
    # 2.7 БОЙ АКОВ
    # ============================================================
    
    if "💟Бой Аков" in text:
        return _handle_battle_accounts(
            bot, message, text, chat_id, user, pending_battles
        )
    
    # ============================================================
    # 2.8 СПИСОК УЧАСТНИКОВ
    # ============================================================
    
    if "💟Список" in text:
        return _handle_members_list(bot, message, chat_id)
    
    # ============================================================
    # 2.9 ТРОЯН
    # ============================================================
    
    if "💟Троян" in text:
        return _handle_trojan(bot, message, user)
    
    # ============================================================
    # 2.10 АНАЛИЗ СООБЩЕНИЯ
    # ============================================================
    
    if "💟Анализ" in text or text.lower() == "/analyze":
        return _handle_analyze(bot, message, chat_id)
    
    # ============================================================
    # 2.11 АНАЛИЗ ПЕРЕПИСКИ
    # ============================================================
    
    if "💟Переписка" in text or text.lower() == "/conversation":
        return _handle_conversation(bot, message, chat_id)
    
    # ============================================================
    # 2.12 ПРЕМИУМ СТАТУС
    # ============================================================
    
    if "💟Премиум" in text or text.lower() == "/premium":
        return _handle_premium_status(bot, message, user)
    
    # ============================================================
    # 2.13 /models
    # ============================================================
    
    if text.lower() in ("/models", "модели"):
        return _handle_models(bot, message)
    
    # ============================================================
    # 2.14 /keys (только владелец)
    # ============================================================
    
    if text.lower() in ("/keys", "ключи"):
        return _handle_keys(bot, message, user, is_owner_user)
    
    # ============================================================
    # 2.15 /gender
    # ============================================================
    
    if text.lower() in ("/gender", "пол"):
        return _handle_gender(bot, message, user)
    
    # ============================================================
    # 2.16 /behavior
    # ============================================================
    
    if text.lower() in ("/behavior", "поведение"):
        return _handle_behavior(bot, message, user)
    
    return False

# ============================================================
# 3. ОБРАБОТЧИКИ
# ============================================================

def _handle_status(bot, message, chat_id, user, is_owner_user, bot_status):
    """Статус бота"""
    try:
        from ai_router import format_router_status
        from premium import can_view_status
        
        if not can_view_status(user.id) and not is_owner_user:
            bot.reply_to(message, "❌ У тебя нет доступа к статусу. Купи премиум!")
            return True
        
        status_text = format_router_status()
        
        if bot_status and bot_status.get("start_time"):
            start = bot_status["start_time"]
            if isinstance(start, str):
                try:
                    start = datetime.fromisoformat(start)
                except ValueError:
                    start = None
            
            if start:
                uptime = (datetime.now() - start).total_seconds()
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                status_text += f"\n\n⏱ Аптайм: {hours}ч {minutes}м"
        
        if len(status_text) > 4000:
            parts = [status_text[i:i+4000] for i in range(0, len(status_text), 4000)]
            for part in parts:
                bot.send_message(chat_id, part)
        else:
            bot.send_message(chat_id, status_text)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка получения статуса: {e}")
    return True

def _handle_battle_accept(bot, message, user, pending_battles):
    """Принятие вызова на бой"""
    try:
        from battle import battle_accounts
        
        battle_data = pending_battles[user.id]
        challenger_id = battle_data["challenger_id"]
        bet = battle_data.get("bet", 0)
        
        result, ca, oa, cu, ou = battle_accounts(
            challenger_id, user.id,
            db.user_profiles, db.user_glitches, db.user_combo,
            db.get_user_glitches, db.add_glitches, db.get_combo_multiplier,
            OWNER_IDS, bet, bot
        )
        del pending_battles[user.id]
        
        from handlers_main import save_pending_battles
        save_pending_battles()
        
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка боя: {e}")
    return True

def _handle_top(bot, message):
    """Топ игроков"""
    try:
        from top import get_top_players
        
        top = get_top_players(10)
        if top:
            response = "🏆 ТОП ИГРОКОВ:\n\n"
            medals = ["🥇", "🥈", "🥉"]
            for i, p in enumerate(top, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                response += f"{medal} {p['name']} — {p['glitches']}👾\n"
        else:
            response = "🏆 Пока нет игроков"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_selfie(bot, message, text, chat_id, user):
    """Селфи/генерация картинки"""
    try:
        from premium import can_generate_images
        from generation import generate_image, generate_selfie
        from progress import show_loading_animation, delete_progress_message
        
        if not can_generate_images(user.id) and user.id not in OWNER_IDS and user.id not in HELPER_IDS:
            bot.reply_to(message, "❌ У тебя нет доступа к созданию картинок. Купи премиум!")
            return True
        
        prompt = text.replace("💟Селфи", "").strip()
        bot.send_chat_action(chat_id, 'upload_photo')
        progress_msg = show_loading_animation(bot, chat_id, 30)
        
        try:
            if prompt:
                img = generate_image(prompt)
            else:
                img = generate_selfie()
        except Exception as e:
            print(f"⚠️ Ошибка генерации: {e}")
            img = None
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        if img:
            bot.send_photo(chat_id, img, caption="✨ Вот твоя картинка! 💜")
        else:
            bot.reply_to(message, "❌ Не получилось сгенерировать. Попробуй другой запрос.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_music(bot, message, text, chat_id, user):
    """Поиск и отправка музыки"""
    try:
        from music import find_music, get_music_audio
        from progress import show_loading_animation, delete_progress_message
        
        query = text.replace("💟Музыка", "").strip()
        if not query:
            bot.reply_to(message, "❌ Напиши название песни: 💟Музыка <название>")
            return True
        
        bot.send_chat_action(chat_id, 'typing')
        progress_msg = show_loading_animation(bot, chat_id, 60)
        
        try:
            music = find_music(query)
        except Exception as e:
            print(f"⚠️ Ошибка поиска музыки: {e}")
            music = None
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        if music:
            try:
                audio_data = get_music_audio(music)
            except Exception as e:
                print(f"⚠️ Ошибка скачивания: {e}")
                audio_data = None
            
            if audio_data and len(audio_data) > 10000:
                bot.send_audio(
                    chat_id,
                    audio_data,
                    title=music.get('title', 'Неизвестно'),
                    performer=music.get('artist', 'Неизвестен'),
                    duration=music.get('duration', 0)
                )
            else:
                bot.reply_to(
                    message,
                    f"🎵 {music.get('title', 'Неизвестно')} — {music.get('artist', 'Неизвестен')}"
                )
            
            # Текст песни в ЛС
            try:
                from music_lyrics import get_music_lyrics
                lyrics = get_music_lyrics(music)
                if lyrics:
                    msg = f"📝 ТЕКСТ ПЕСНИ: {music.get('title', 'Неизвестно')}\n\n{lyrics}"
                    if len(msg) > 4000:
                        parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                        for part in parts:
                            bot.send_message(user.id, part)
                    else:
                        bot.send_message(user.id, msg)
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ Не нашёл музыку по этому запросу")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_profile(bot, message, user):
    """Профиль пользователя"""
    try:
        from premium import get_user_level, get_premium_level_icon, get_premium_config
        
        g = db.get_user_glitches(user.id, OWNER_IDS)
        badge = db.get_glitch_badge(g)
        combo = db.user_combo.get(user.id, 0)
        
        level = get_user_level(user.id)
        level_icon = get_premium_level_icon(user.id)
        level_name = get_premium_config(user.id)["name"]
        
        response = f"👤 {user.first_name}\n"
        if user.username:
            response += f"@{user.username}\n"
        response += f"👾 {g} {badge}\n"
        response += f"💜 Комбо: {combo}\n"
        
        if level != "none":
            response += f"{level_icon} {level_name}\n"
        
        if user.id in db.user_credits:
            response += f"💳 Кредит: {db.user_credits[user.id].get('remaining', 0)}👾\n"
        
        # Статистика общения
        try:
            from message_analyzer import get_user_stats
            user_stats = get_user_stats(str(user.id))
            if user_stats:
                response += f"\n📊 СТАТИСТИКА ОБЩЕНИЯ:"
                response += f"\n⭐ Оценка: {user_stats.get('avg_score', 0):.1f}/10"
                response += f"\n💬 Сообщений: {user_stats.get('count', 0)}"
        except Exception:
            pass
        
        # Поведение
        try:
            from behavior import get_user_behavior
            behavior_data = get_user_behavior(user.id)
            if behavior_data:
                response += f"\n🎭 Поведение: {behavior_data.get('behavior_score', 50)}/100"
                response += f"\n🤝 Доверие: {behavior_data.get('trust', 5)}/10"
        except Exception:
            pass
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✏️ ИЗМЕНИТЬ", callback_data="edit_profile"),
            telebot.types.InlineKeyboardButton("💎 ПРЕМИУМ", callback_data="premium_menu")
        )
        bot.reply_to(message, response, reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_battle_accounts(bot, message, text, chat_id, user, pending_battles):
    """Бой аков"""
    try:
        from battle import battle_accounts
        from progress import show_loading_animation, delete_progress_message
        from premium import get_battle_bonus
        
        parts = text.replace("💟Бой Аков", "").strip().split()
        target_id = None
        bet = 0
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            if parts:
                try:
                    bet = int(parts[0])
                except ValueError:
                    pass
        elif parts:
            username = parts[0].replace("@", "")
            for uid, p in db.user_profiles.items():
                if p.get("username", "").replace("@", "") == username:
                    target_id = uid
                    break
            if len(parts) > 1:
                try:
                    bet = int(parts[1])
                except ValueError:
                    pass
        
        if not target_id or target_id == user.id:
            bot.reply_to(
                message,
                "❌ Ответь на сообщение или укажи юзера: 💟Бой Аков @юзер [ставка]"
            )
            return True
        
        progress_msg = show_loading_animation(bot, chat_id, 15)
        
        if bet > 0:
            current = db.get_user_glitches(user.id, OWNER_IDS)
            if current != float('inf') and current < bet:
                if progress_msg:
                    delete_progress_message(bot, chat_id, progress_msg.message_id)
                bot.reply_to(message, f"❌ Нужно {bet}👾, у тебя {current}👾")
                return True
            
            pending_battles[target_id] = {"challenger_id": user.id, "bet": bet}
            
            from handlers_main import save_pending_battles
            save_pending_battles()
            
            target_name = db.user_profiles.get(target_id, {}).get("first_name", "Игрок")
            if progress_msg:
                delete_progress_message(bot, chat_id, progress_msg.message_id)
            bot.reply_to(
                message,
                f"⚔️ {target_name}! Ставка: {bet}👾\nНапиши 💟Бой чтобы принять!"
            )
            return True
        
        # Бой без ставки
        battle_bonus = get_battle_bonus(user.id)
        
        result, ca, oa, cu, ou = battle_accounts(
            user.id, target_id,
            db.user_profiles, db.user_glitches, db.user_combo,
            db.get_user_glitches, db.add_glitches, db.get_combo_multiplier,
            OWNER_IDS, bet, bot
        )
        
        if battle_bonus > 0:
            result += f"\n\n💎 Премиум бонус: +{battle_bonus} балла"
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка боя аков: {e}")
    return True

def _handle_members_list(bot, message, chat_id):
    """Список участников"""
    try:
        from bot import get_chat_members
        from progress import show_loading_animation, delete_progress_message
        
        progress_msg = show_loading_animation(bot, chat_id, 30)
        members = get_chat_members(bot, chat_id)
        
        if progress_msg:
            delete_progress_message(bot, chat_id, progress_msg.message_id)
        
        if members:
            stats = [f"{m.first_name} @{m.username or ''}" for m in members if not m.is_bot]
            response = "📊 СПИСОК УЧАСТНИКОВ:\n\n" + "\n".join(stats[:50])
            if len(stats) > 50:
                response += f"\n\n... и ещё {len(stats) - 50} участников"
        else:
            response = "📊 Участников нет"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_trojan(bot, message, user):
    """Запуск игры Троян"""
    try:
        from trojan_game import start_trojan_game
        start_trojan_game(message, user, bot)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_analyze(bot, message, chat_id):
    """Анализ сообщения"""
    try:
        from message_analyzer import analyze_message, format_analysis_result
        
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответь на сообщение, которое хочешь проанализировать!")
            return True
        
        target_msg = message.reply_to_message
        target_text = target_msg.text or ""
        target_user = target_msg.from_user
        
        progress_msg = bot.send_message(chat_id, "🔍 Анализирую...")
        
        result = analyze_message(target_text, target_user.id, target_user.first_name)
        
        try:
            bot.delete_message(chat_id, progress_msg.message_id)
        except Exception:
            pass
        
        response = format_analysis_result(result)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_conversation(bot, message, chat_id):
    """Анализ переписки"""
    try:
        from message_analyzer import analyze_conversation, analysis_data
        
        if chat_id not in analysis_data.get("conversations", {}):
            bot.reply_to(message, "❌ Нет данных для анализа переписки")
            return True
        
        conv_data = analysis_data["conversations"][chat_id]
        if len(conv_data) < 2:
            bot.reply_to(message, "❌ Слишком мало сообщений для анализа (нужно минимум 2)")
            return True
        
        result = analyze_conversation(conv_data[-20:])
        
        response = f"📊 АНАЛИЗ ПЕРЕПИСКИ:\n\n"
        response += f"💬 Сообщений: {result.get('total_messages', 0)}\n"
        response += f"👥 Участников: {result.get('participants', 0)}\n"
        response += f"⭐ Средняя оценка: {result.get('avg_score', 0):.1f}/10\n"
        response += f"🎭 Тон: {result.get('tone', 'нейтральный')}\n"
        response += f"📝 {result.get('summary', '')}"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_premium_status(bot, message, user):
    """Статус премиума"""
    try:
        from premium import format_premium_status
        bot.reply_to(message, format_premium_status(user.id))
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_models(bot, message):
    """Список моделей"""
    try:
        from ai_model_manager import get_all_main_models, get_model_stats_summary
        
        models = get_all_main_models()
        stats = get_model_stats_summary()
        
        response = "🧠 МОДЕЛИ SYSTMKA:\n\n"
        for model_id, model in models.items():
            icon = model.get("icon", "🤖")
            name = model.get("name", model_id)
            status = model.get("status", "unknown")
            status_icon = "✅" if status == "active" else "⚠️" if status == "degraded" else "❌"
            stat = stats.get(model_id, {})
            total = stat.get("total_requests", 0)
            quality = stat.get("quality", 5)
            
            response += f"{icon} {name} {status_icon}\n"
            response += f"   ├── Статус: {status}\n"
            response += f"   ├── Запросов: {total}\n"
            response += f"   ├── Качество: {quality}/10\n"
            response += f"   └── Задачи: {', '.join(model.get('tasks', [])[:3])}\n\n"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_keys(bot, message, user, is_owner_user):
    """Статус ключей (только владелец)"""
    try:
        if not is_owner_user:
            bot.reply_to(message, "❌ Только владелец может смотреть ключи")
            return True
        
        from ai_key_rotator import get_all_openrouter_keys_status, get_key_stats_summary
        
        keys = get_all_openrouter_keys_status()
        summary = get_key_stats_summary()
        
        response = "🔑 СТАТУС КЛЮЧЕЙ:\n\n"
        response += f"📊 Всего ключей: {summary.get('total_keys', 0)}\n"
        response += f"✅ Активных: {summary.get('active_keys', 0)}\n"
        response += f"❌ Отключённых: {summary.get('disabled_keys', 0)}\n"
        response += f"📈 Осталось запросов: {summary.get('total_remaining', 0)}\n\n"
        
        for key, data in keys.items():
            email = data.get("email", key[:20] + "...")
            remaining = data.get("remaining", 0)
            total = data.get("total", 5000)
            status = data.get("status", "unknown")
            status_icon = "✅" if status == "active" else "⚠️" if status == "low" else "🔴"
            percent = (remaining / total) * 100 if total > 0 else 0
            bar_len = 10
            filled = int((percent / 100) * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            response += f"{status_icon} {email}\n"
            response += f"   ├── {remaining}/{total} ({percent:.1f}%) {bar}\n"
            response += f"   └── Статус: {status}\n"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_gender(bot, message, user):
    """Пол пользователя"""
    try:
        from gender_detector import format_gender_info
        
        target_user = user
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        gender_info = format_gender_info(target_user.id)
        bot.reply_to(message, f"👤 {target_user.first_name}\n{gender_info}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

def _handle_behavior(bot, message, user):
    """Поведение пользователя"""
    try:
        from behavior import format_user_behavior
        
        target_user = user
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        behavior_info = format_user_behavior(target_user.id)
        bot.reply_to(message, f"👤 {target_user.first_name}\n{behavior_info}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True

# ============================================================
# 4. ЗАГРУЗКА
# ============================================================

print("📨 Обработчик команд загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")