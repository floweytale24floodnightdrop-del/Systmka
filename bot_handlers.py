"""Обработчики сообщений, callback и inline"""

import telebot
import json
import time

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS

# ============================================================
# 2. INLINE ОБРАБОТЧИК
# ============================================================

def register_inline_handler(bot, bot_status, system_prompt, openrouter_key):
    """
    Зарегистрировать inline-обработчик.
    
    Args:
        bot: telebot instance
        bot_status: словарь статуса
        system_prompt: системный промт
        openrouter_key: ключ OpenRouter (или список)
    """
    
    @bot.inline_handler(lambda query: True)
    def inline_query(query):
        """Обработка inline-запросов"""
        try:
            text = query.query or "Привет"
            bot_status["total_ai_requests"] = bot_status.get("total_ai_requests", 0) + 1
            
            # Трекинг
            try:
                from network_monitor import track_request
                track_request(50)
            except Exception:
                pass
            
            # Проверяем интернет
            try:
                from config_network import check_internet
                if check_internet() == "offline":
                    results = [telebot.types.InlineQueryResultArticle(
                        id="1",
                        title="🌐 Нет интернета",
                        description="Попробуй позже",
                        input_message_content=telebot.types.InputTextMessageContent(
                            "Я занята или сплю. Отвечу позже!🫰"
                        )
                    )]
                    bot.answer_inline_query(query.id, results, cache_time=0)
                    return
            except Exception:
                pass
            
            # Импорт personality
            try:
                from personality import get_personality_for_prompt
                personality_suffix = get_personality_for_prompt()
            except Exception:
                personality_suffix = ""
            
            # Получаем ключ
            if isinstance(openrouter_key, list):
                key = openrouter_key[0] if openrouter_key else ""
            else:
                key = openrouter_key
            
            if not key:
                bot.answer_inline_query(query.id, [], cache_time=0)
                return
            
            # Запрос к OpenRouter
            import requests
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
                            "content": system_prompt + personality_suffix
                        },
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.8,
                },
                timeout=30
            )
            
            answer = "Не получилось"
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    answer = data['choices'][0]['message']['content'].strip()
            
            results = [telebot.types.InlineQueryResultArticle(
                id="1",
                title="💜 Систмка",
                description=answer[:100],
                input_message_content=telebot.types.InputTextMessageContent(answer)
            )]
            bot.answer_inline_query(query.id, results, cache_time=0)
        
        except Exception as e:
            print(f"⚠️ Ошибка inline: {e}")
            try:
                bot.answer_inline_query(query.id, [], cache_time=0)
            except Exception:
                pass

# ============================================================
# 3. ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ
# ============================================================

def register_message_handler(bot, debug_settings, bot_status):
    """Зарегистрировать основной обработчик сообщений"""
    
    @bot.message_handler(func=lambda message: True)
    def message_handler(message):
        """Обработка всех сообщений"""
        try:
            from handlers_main import handle_message
            handle_message(bot, message, debug_settings, bot_status)
        except Exception as e:
            print(f"⚠️ Ошибка в message_handler: {e}")
            try:
                from error_reporter import notify_error
                notify_error(bot, OWNER_IDS, e, message.chat.id)
            except Exception:
                pass

# ============================================================
# 4. ОБРАБОТЧИК CALLBACK
# ============================================================

def register_callback_handler(bot):
    """Зарегистрировать обработчик callback-запросов"""
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        """Обработка callback-запросов"""
        try:
            data = call.data
        except Exception:
            return
        
        # ============================================================
        # 4.1 НОВОЕ: CALLBACK ОТ ERROR_GUARDIAN
        # ============================================================
        
        if data.startswith("guardian_"):
            _handle_guardian_callback(bot, call)
            return
        
        # ============================================================
        # 4.2 Редактирование профиля
        # ============================================================
        
        if data == "edit_profile":
            _handle_edit_profile(bot, call)
        
        elif data == "edit_nick":
            _handle_edit_nick(bot, call)
        
        # ============================================================
        # 4.3 Премиум
        # ============================================================
        
        elif data == "premium_menu":
            _handle_premium_menu(bot, call)
        
        elif data == "premium_3d":
            _handle_premium_buy(bot, call, "3d")
        
        # ============================================================
        # 4.4 Кредит
        # ============================================================
        
        elif data == "pay_credit":
            _handle_pay_credit(bot, call)
        
        # ============================================================
        # 4.5 Апелляции
        # ============================================================
        
        elif data.startswith("appeal_"):
            _handle_appeal(bot, call)
        
        # ============================================================
        # 4.6 Разрешения автономии
        # ============================================================
        
        elif data.startswith("perm_"):
            _handle_permission(bot, call)
        
        # ============================================================
        # 4.7 РП-запросы
        # ============================================================
        
        elif data.startswith("rp_accept_"):
            _handle_rp_accept(bot, call)
        
        elif data.startswith("rp_decline_"):
            _handle_rp_decline(bot, call)
        
        # ============================================================
        # 4.8 Изменения файлов
        # ============================================================
        
        elif data.startswith("file_change_"):
            _handle_file_change(bot, call)
        
        # ============================================================
        # 4.9 Игры
        # ============================================================
        
        elif data.startswith("game_"):
            _handle_game(bot, call)

# ============================================================
# 5. ОБРАБОТЧИКИ CALLBACK
# ============================================================

def _handle_guardian_callback(bot, call):
    """
    Обработка callback от error_guardian.
    
    Формат: guardian_<action>_<module_name>
    action: freeze | fix | stop | skip
    """
    try:
        from error_guardian import process_guardian_callback
        process_guardian_callback(call, bot)
    except Exception as e:
        print(f"⚠️ Ошибка guardian_callback: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка обработки")
        except Exception:
            pass


def _handle_edit_profile(bot, call):
    """Меню редактирования профиля"""
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(
            "Изменить ник", callback_data="edit_nick"
        ))
        bot.edit_message_text(
            "Что изменить?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"⚠️ Ошибка edit_profile: {e}")


def _handle_edit_nick(bot, call):
    """Подсказка по изменению ника"""
    try:
        bot.answer_callback_query(call.id, "Напиши новый ник сообщением")
    except Exception:
        pass


def _handle_premium_menu(bot, call):
    """Меню премиума"""
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(
            "3 дня - 15⭐", callback_data="premium_3d"
        ))
        bot.edit_message_text(
            "💎 Премиум",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"⚠️ Ошибка premium_menu: {e}")


def _handle_premium_buy(bot, call, period):
    """Покупка премиума"""
    try:
        bot.answer_callback_query(call.id, f"Покупка на {period} — свяжись с Флауи")
    except Exception:
        pass


def _handle_pay_credit(bot, call):
    """Оплата кредита (для одного пользователя)"""
    try:
        from handlers_economy import process_credit_for_user
        process_credit_for_user(bot, call.from_user.id)
        bot.answer_callback_query(call.id, "✅ Обработано")
    except Exception as e:
        print(f"⚠️ Ошибка pay_credit: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка")
        except Exception:
            pass


def _handle_appeal(bot, call):
    """Обработка апелляции"""
    try:
        from handlers_economy import process_appeal
        process_appeal(bot, call)
    except Exception as e:
        print(f"⚠️ Ошибка appeal: {e}")


def _handle_permission(bot, call):
    """Обработка разрешения автономии"""
    try:
        from autonomy import process_permission_response
        process_permission_response(call, bot)
    except Exception as e:
        print(f"⚠️ Ошибка perm: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка")
        except Exception:
            pass


def _handle_rp_accept(bot, call):
    """Принятие РП-запроса"""
    try:
        request_id = int(call.data.replace("rp_accept_", ""))
        from rp_commands import process_rp_response
        process_rp_response(bot, call, request_id, accept=True)
    except Exception as e:
        print(f"⚠️ Ошибка rp_accept: {e}")
        try:
            bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        except Exception:
            pass


def _handle_rp_decline(bot, call):
    """Отклонение РП-запроса"""
    try:
        request_id = int(call.data.replace("rp_decline_", ""))
        from rp_commands import process_rp_response
        process_rp_response(bot, call, request_id, accept=False)
    except Exception as e:
        print(f"⚠️ Ошибка rp_decline: {e}")
        try:
            bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        except Exception:
            pass


def _handle_file_change(bot, call):
    """Изменение файлов"""
    try:
        from personality_builder import process_file_change_response
        process_file_change_response(call, bot)
    except Exception as e:
        print(f"⚠️ Ошибка file_change: {e}")


def _handle_game(bot, call):
    """Игровые callback'и"""
    try:
        from games import handle_game_callback
        handle_game_callback(call, bot)
    except Exception as e:
        print(f"⚠️ Ошибка game: {e}")

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("📨 Обработчики бота загружены")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"🛡️ Guardian callback: ✅")