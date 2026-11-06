"""Обработчики старта — /start, /help, /info, 💟Команды"""

import telebot
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS
import database as db

# ============================================================
# 2. РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# ============================================================

def register_start_handlers(bot, bot_status=None):
    """
    Зарегистрировать стартовые обработчики.
    
    Args:
        bot: telebot instance
        bot_status: словарь статуса бота (опционально)
    """
    
    if bot_status is None:
        bot_status = {}
    
    # ============================================================
    # 2.1 КОМАНДА /start
    # ============================================================
    
    @bot.message_handler(commands=['start'])
    def start(message):
        """Обработка /start"""
        try:
            from bot import check_startup_grace, check_ftf24
            
            if check_startup_grace():
                return
        except Exception:
            pass
        
        # Количество участников
        member_count = 0
        try:
            if message.chat.type in ('group', 'supergroup'):
                member_count = bot.get_chat_member_count(message.chat.id)
        except Exception as e:
            print(f"⚠️ Ошибка получения количества участников: {e}")
        
        # Поведение + приветствие
        greeting = "Привет! Я Систмка)"
        try:
            from behavior import get_behavior, format_greeting
            behavior = get_behavior(
                message.chat.type,
                member_count,
                message.from_user.id,
            )
            greeting_result = format_greeting(
                behavior, message.from_user.username
            )
            if greeting_result:
                greeting = greeting_result
        except Exception as e:
            print(f"⚠️ Ошибка форматирования приветствия: {e}")
        
        # ЛС — проверка FTF24
        if message.chat.type == "private":
            if message.from_user.id not in OWNER_IDS:
                try:
                    from premium import check_premium
                    from bot import check_ftf24 as check_ftf24_func
                    
                    has_premium = check_premium(
                        message.from_user.id, OWNER_IDS
                    )
                    
                    if not check_ftf24_func(message.from_user) and not has_premium:
                        bot.reply_to(
                            message,
                            "У тебя нет приписки #FTF24 в нике, "
                            "я не хочу с тобой разговаривать."
                        )
                        return
                except Exception:
                    pass
            
            # Сохраняем пользователя в ЛС
            if message.from_user.id not in db.ls_users:
                db.ls_users.add(message.from_user.id)
                print(
                    f"👤 Новый пользователь в ЛС: "
                    f"{message.from_user.first_name} "
                    f"(@{message.from_user.username})"
                )
        
        try:
            bot.reply_to(message, greeting)
        except Exception as e:
            print(f"⚠️ Ошибка отправки приветствия: {e}")
    
    # ============================================================
    # 2.2 КОМАНДА 💟Команды
    # ============================================================
    
    @bot.message_handler(commands=['💟Команды', 'commands'])
    def show_commands(message):
        """Показать список команд"""
        try:
            from bot import check_startup_grace
            if check_startup_grace():
                return
        except Exception:
            pass
        
        # В ЛС команды только для владельцев
        if message.chat.type == "private":
            if message.from_user.id not in OWNER_IDS:
                bot.reply_to(message, "В лс команды не работают)")
                return
        
        try:
            from commands import get_commands_text
            is_owner = message.from_user.id in OWNER_IDS
            is_private = message.chat.type == "private"
            
            commands = get_commands_text(
                is_owner and is_private, False
            )
            bot.reply_to(message, commands)
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
    
    # ============================================================
    # 2.3 КОМАНДА /help
    # ============================================================
    
    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Обработка /help"""
        try:
            from bot import check_startup_grace
            if check_startup_grace():
                return
        except Exception:
            pass
        
        bot.reply_to(message, "Напиши 💟Команды для списка команд")
    
    # ============================================================
    # 2.4 КОМАНДА /info
    # ============================================================
    
    @bot.message_handler(commands=['info'])
    def info_command(message):
        """Информация о системе (только владелец)"""
        try:
            from bot import check_startup_grace
            if check_startup_grace():
                return
        except Exception:
            pass
        
        if message.from_user.id not in OWNER_IDS:
            bot.reply_to(
                message,
                "❌ Только владелец может смотреть информацию"
            )
            return
        
        # Собираем информацию
        info_lines = [
            "📊 ИНФОРМАЦИЯ О СИСТЕМЕ:",
            f"🤖 Бот: @{bot.get_me().username}",
            f"👑 Владельцев: {len(OWNER_IDS)}",
            f"👤 Пользователей в БД: {len(db.user_profiles)}",
            f"💬 Чатов: {len(db.all_chats)}",
        ]
        
        # Сообщения в истории
        try:
            total_messages = sum(
                len(h) for h in db.history.values()
            )
            info_lines.append(f"📝 Сообщений в истории: {total_messages}")
        except Exception:
            pass
        
        # Время работы
        start_time = bot_status.get("start_time")
        if start_time:
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time)
                except (ValueError, TypeError):
                    start_time = None
            
            if isinstance(start_time, datetime):
                try:
                    uptime = (datetime.now() - start_time).total_seconds()
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    info_lines.append(f"⏱ Аптайм: {hours}ч {minutes}м")
                except Exception:
                    pass
        
        # Статистика ИИ
        try:
            from ai_key_rotator import get_key_stats_summary
            stats = get_key_stats_summary()
            info_lines.append(
                f"🤖 Запросов ИИ: {stats.get('total_used', 0)}"
            )
            info_lines.append(
                f"📊 Осталось запросов: {stats.get('total_remaining', 0)}"
            )
        except Exception:
            pass
        
        # Статистика премиума
        try:
            from premium import format_premium_stats
            info_lines.append("")
            info_lines.append(format_premium_stats())
        except Exception:
            pass
        
        bot.reply_to(message, "\n".join(info_lines))
    
    print("📨 Стартовые обработчики зарегистрированы")

# ============================================================
# 3. ЗАГРУЗКА
# ============================================================

print("📨 Модуль стартовых обработчиков загружен")