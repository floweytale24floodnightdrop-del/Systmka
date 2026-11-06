"""Команды владельца — расширенная версия с явными импортами + мозг"""

import telebot
import json
import os
import time
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS
import database as db

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

DEBUG_FILE = "debug_settings.json"


def load_debug_settings():
    """Загрузить настройки отладки"""
    try:
        if os.path.exists(DEBUG_FILE):
            with open(DEBUG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    return loaded
    except Exception as e:
        print(f"⚠️ Ошибка загрузки отладки: {e}")
    
    return {
        "debug_mode": False,
        "learning_mode": True,
        "auto_respond": True,
    }


def save_debug_settings(settings):
    """Сохранить настройки отладки"""
    try:
        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения отладки: {e}")
        return False


debug_settings = load_debug_settings()

# ============================================================
# 3. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def register_owner_handlers(bot, message, text, chat_id, user,
                            is_owner_user, debug_settings_arg=None):
    """
    Обработка команд владельца.
    
    Returns:
        bool: True если команда обработана
    """
    
    if not text:
        return False
    
    # ============================================================
    # 3.0 МОЗГ (НОВОЕ!)
    # ============================================================
    
    if "💟Мозг" in text:
        return _handle_brain(bot, message, text)
    
    # === 3.1 ЧАТЫ ===
    if "💟Чаты" in text:
        return _handle_chats(bot, message)
    
    # === 3.2 ОТЛАДКА ===
    if "💟Отладка" in text:
        return _handle_debug_toggle(bot, message)
    
    # === 3.3 ДОКС ===
    if "💟Докс" in text:
        return _handle_dox(bot, message, text, chat_id)
    
    # === 3.4 СИСТЕМА ===
    if "💟Система" in text:
        return _handle_system(bot, message, chat_id)
    
    # === 3.5 КОРЗИНА ===
    if "💟Корзина" in text:
        return _handle_trash(bot, message, text)
    
    # === 3.6 СТИКЕРЫ ===
    if "💟Стикеры" in text:
        return _handle_stickers(bot, message)
    
    # === 3.7 РЕАКЦИЯ ===
    if "💟Реакция" in text:
        return _handle_reaction(bot, message, text)
    
    # === 3.8 ВЫДАТЬ ПРЕМИУМ ===
    if "💟Выдать премиум" in text:
        return _handle_give_premium(bot, message, text)
    
    # === 3.9 СНЯТЬ ПРЕМИУМ ===
    if "💟Снять премиум" in text:
        return _handle_remove_premium(bot, message, text)
    
    # === 3.10 ИСТОРИЯ ===
    if "💟История сообщений" in text:
        return _handle_history(bot, message, text, chat_id)
    
    # === 3.11 ГОЛОС ===
    if "💟Голос" in text:
        return _handle_voice(bot, message, text, chat_id)
    
    # === 3.12 МОДЕЛИ ===
    if "💟Модели" in text or text.lower() == "/aimodels":
        return _handle_ai_models(bot, message)
    
    # === 3.13 ОЦЕНКИ ===
    if "💟Оценки" in text or text.lower() == "/evaluations":
        return _handle_evaluations(bot, message)
    
    # === 3.14 ПОВЕДЕНИЕ ===
    if "💟Поведение" in text or text.lower() == "/behavior_stats":
        return _handle_behavior_stats(bot, message)
    
    # === 3.15 ПОЛ ===
    if "💟Пол" in text or text.lower() == "/gender_stats":
        return _handle_gender_stats(bot, message)
    
    # === 3.16 МОДЕРАЦИЯ ===
    if "💟Модерация" in text or text.lower() == "/moderation":
        return _handle_moderation_stats(bot, message)
    
    # === 3.17 ТРОЯН СТАТИСТИКА ===
    if "💟Троян Стата" in text or "💟Троян Статистика" in text:
        return _handle_trojan_stats(bot, message, user)
    
    # === 3.18 АВТОНОМИЯ ===
    if "💟Автономия" in text:
        return _handle_autonomy(bot, message, text)
    
    # === 3.19 ОТЛАДОЧНЫЕ КОМАНДЫ ===
    if debug_settings.get("debug_mode"):
        if text.startswith("📁"):
            return _handle_files_debug(bot, message, text, chat_id)
        if text.startswith("🔓"):
            return _handle_system_debug(bot, message, text, chat_id)
    
    return False

# ============================================================
# 4. ОБРАБОТЧИКИ
# ============================================================

def _handle_brain(bot, message, text):
    """
    💟Мозг — статус мозга (НОВОЕ!).
    
    Подкоманды:
    - 💟Мозг — полный статус
    - 💟Мозг переменные — список переменных
    - 💟Мозг эмоции — активные эмоции
    - 💟Мозг связи — связи
    - 💟Мозг сохранить — принудительное сохранение
    """
    try:
        from brain_init import (
            get_full_status,
            brain,
            is_initialized,
            force_save,
        )
        
        if not is_initialized():
            bot.reply_to(message, "❌ Мозг не инициализирован!")
            return True
        
        parts = text.replace("💟Мозг", "").strip().lower().split()
        subcommand = parts[0] if parts else ""
        
        # === 💟Мозг (полный статус) ===
        if not subcommand:
            status = get_full_status()
            
            if len(status) > 4000:
                chunks = [status[i:i+4000] for i in range(0, len(status), 4000)]
                for chunk in chunks:
                    bot.send_message(message.chat.id, chunk)
            else:
                bot.reply_to(message, status)
            return True
        
        # === 💟Мозг переменные ===
        if subcommand in ("переменные", "vars", "variables"):
            total = len(brain.variables)
            
            # Группируем по тегам
            groups = {}
            for name, var in brain.variables.items():
                tag = "unknown"
                if var.tags:
                    tag = var.tags[0]
                if tag not in groups:
                    groups[tag] = []
                groups[tag].append(f"{name}={var.value:.0f}")
            
            lines = [f"🧠 ПЕРЕМЕННЫЕ ({total}):"]
            for tag, vars_list in sorted(groups.items()):
                lines.append(f"\n📦 {tag} ({len(vars_list)}):")
                # Первые 5
                for v in vars_list[:5]:
                    lines.append(f"  • {v}")
                if len(vars_list) > 5:
                    lines.append(f"  ... и ещё {len(vars_list) - 5}")
            
            response = "\n".join(lines)
            
            if len(response) > 4000:
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    bot.send_message(message.chat.id, chunk)
            else:
                bot.reply_to(message, response)
            return True
        
        # === 💟Мозг эмоции ===
        if subcommand in ("эмоции", "emotions"):
            lines = ["🎭 ЭМОЦИИ:"]
            
            for name, emotion in brain.emotions.items():
                var = brain.get_variable(name)
                value = var.value if var else 0
                
                if emotion.active:
                    icon = "🔥"
                elif value >= emotion.threshold * 0.7:
                    icon = "⚠️"
                else:
                    icon = "💤"
                
                lines.append(
                    f"{icon} {name}: {value:.0f}/100 "
                    f"(порог {emotion.threshold:.0f}, "
                    f"активаций {emotion.activation_count})"
                )
            
            # Топ-5 по значению
            top = sorted(
                [(name, brain.get_variable(name).value if brain.get_variable(name) else 0)
                 for name in brain.emotions],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            lines.append("\n📊 ТОП-5:")
            for name, value in top:
                lines.append(f"  • {name}: {value:.0f}")
            
            bot.reply_to(message, "\n".join(lines))
            return True
        
        # === 💟Мозг связи ===
        if subcommand in ("связи", "connections"):
            total = len(brain.connections)
            
            # Топ-10 по весу
            sorted_conn = sorted(
                brain.connections.values(),
                key=lambda c: abs(c.weight),
                reverse=True
            )[:10]
            
            lines = [f"🔗 СВЯЗИ ({total}):", "", "📊 ТОП-10 ПО ВЕСУ:"]
            
            for conn in sorted_conn:
                direction = "→" if conn.weight > 0 else "⊣"
                lines.append(
                    f"  {conn.source} {direction} {conn.target} "
                    f"(w={conn.weight:.2f}, исп. {conn.usage_count})"
                )
            
            bot.reply_to(message, "\n".join(lines))
            return True
        
        # === 💟Мозг сохранить ===
        if subcommand in ("сохранить", "save"):
            success = force_save()
            if success:
                bot.reply_to(message, "✅ Мозг сохранён!")
            else:
                bot.reply_to(message, "❌ Не удалось сохранить мозг")
            return True
        
        # === Неизвестная подкоманда ===
        bot.reply_to(
            message,
            "🧠 ПОДКОМАНДЫ МОЗГА:\n"
            "  💟Мозг — полный статус\n"
            "  💟Мозг переменные — список переменных\n"
            "  💟Мозг эмоции — активные эмоции\n"
            "  💟Мозг связи — связи\n"
            "  💟Мозг сохранить — принудительное сохранение"
        )
        return True
    
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка мозга: {e}")
        import traceback
        traceback.print_exc()
        return True


def _handle_chats(bot, message):
    """Список чатов"""
    response = "📋 СПИСОК ЧАТОВ:\n\n"
    
    if db.all_chats:
        for cid, info in db.all_chats.items():
            title = info.get('title', 'Без названия')
            chat_type = info.get('type', 'unknown')
            member_count = info.get('member_count', 0)
            response += f"• {title} ({chat_type}) — {member_count} участников\n"
    else:
        response += "❌ Нет активных чатов\n"
    
    response += "\n📋 ЛС ПОЛЬЗОВАТЕЛЕЙ:\n"
    if db.ls_users:
        for uid in list(db.ls_users)[:20]:
            if uid in db.user_profiles:
                p = db.user_profiles[uid]
                username = p.get('username', '')
                name = p.get('first_name', 'Неизвестно')
                response += f"• {name} {username}\n"
        if len(db.ls_users) > 20:
            response += f"... и ещё {len(db.ls_users) - 20} пользователей"
    else:
        response += "❌ Нет ЛС пользователей"
    
    bot.reply_to(message, response)
    return True


def _handle_debug_toggle(bot, message):
    """Переключить отладку"""
    global debug_settings
    debug_settings["debug_mode"] = not debug_settings.get("debug_mode", False)
    save_debug_settings(debug_settings)
    
    status = "включена" if debug_settings["debug_mode"] else "выключена"
    bot.reply_to(message, f"🔧 Отладка {status}")
    return True


def _handle_dox(bot, message, text, chat_id):
    """Докс"""
    try:
        from osint_engine import full_dox_real, format_dox_result_real
        from progress import show_loading_animation, delete_progress_message
        
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


def _handle_system(bot, message, chat_id):
    """Системный отчёт"""
    try:
        from system_monitor import get_full_report, format_report
        from progress import send_long_message
        
        report = get_full_report(db)
        formatted = format_report(report)
        send_long_message(bot, chat_id, formatted, message)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка получения отчёта: {e}")
    return True


def _handle_trash(bot, message, text):
    """Корзина"""
    try:
        from trash import get_trash_list, get_trash_stats, clear_trash
        
        parts = text.replace("💟Корзина", "").strip().split()
        
        if parts and parts[0].lower() == "очистить":
            success, msg = clear_trash()
            bot.reply_to(message, msg)
            return True
        
        trash_list = get_trash_list()
        stats = get_trash_stats()
        
        response = "🗑 КОРЗИНА:\n"
        response += f"📁 Файлов: {stats.get('total_files', 0)}\n"
        response += f"💾 Размер: {stats.get('dir_size_mb', 0)}MB\n\n"
        
        if trash_list:
            for item in trash_list[:20]:
                name = item.get('name', '?')
                original = item.get('original', '?')
                size = item.get('size', 0)
                response += f"• {name} → {original} ({size} байт)\n"
            if len(trash_list) > 20:
                response += f"\n... и ещё {len(trash_list) - 20} файлов"
            response += "\n\n💡 Чтобы очистить: 💟Корзина очистить"
        else:
            response += "❌ Корзина пуста"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_stickers(bot, message):
    """Кастомные стикеры"""
    try:
        from stickers_custom import get_all_custom_stickers, get_stickers_stats
        
        stickers = get_all_custom_stickers()
        stats = get_stickers_stats()
        
        response = "🎯 КАСТОМНЫЕ СТИКЕРЫ:\n"
        response += f"📊 Всего: {stats.get('total_stickers', 0)}\n"
        response += f"📦 Паков: {stats.get('sets', 0)}\n"
        response += f"👤 Источников: {stats.get('sources', 0)}\n\n"
        
        if stickers:
            for s in stickers[:20]:
                sticker_id = s.get('id', '?')
                source = s.get('source_user', '?')
                set_name = s.get('set_name', '?')
                response += f"• #{sticker_id} — {source} (пак: {set_name})\n"
            if len(stickers) > 20:
                response += f"\n... и ещё {len(stickers) - 20} стикеров"
        else:
            response += "❌ Нет кастомных стикеров"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_reaction(bot, message, text):
    """Управление любимой реакцией"""
    try:
        from reactions import set_favorite_reaction, get_favorite_reaction
        
        parts = text.replace("💟Реакция", "").strip()
        if parts:
            if set_favorite_reaction(parts):
                bot.reply_to(message, f"❤️ Любимая реакция: {parts}")
            else:
                bot.reply_to(
                    message,
                    "❌ Неверная реакция. Доступны: 👍 👎 ❤️ 🔥 🥰 👏 "
                    "😁 🤔 🤯 😱 🥱 😢 🤡 👾 🎉 😈 🤗 😍 🤩 😎 😏 😘 "
                    "🥺 😭 😡 🤬 🫶 🕊"
                )
        else:
            bot.reply_to(
                message,
                f"❤️ Текущая любимая реакция: {get_favorite_reaction()}"
            )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_give_premium(bot, message, text):
    """Выдать премиум"""
    try:
        from premium import set_premium, PREMIUM_LEVELS
        
        parts = text.replace("💟Выдать премиум", "").strip().split()
        if len(parts) < 1:
            bot.reply_to(message, "❌ Формат: 💟Выдать премиум @юзер [уровень] [дни]")
            return True
        
        username = parts[0].replace("@", "")
        level = parts[1] if len(parts) > 1 else "premium"
        
        try:
            days = int(parts[2]) if len(parts) > 2 else 30
        except ValueError:
            days = 30
        
        if level not in PREMIUM_LEVELS or level in ("owner", "helper", "none"):
            bot.reply_to(
                message,
                "❌ Уровни: premka, premium, premium_plus"
            )
            return True
        
        target_id = None
        target_name = None
        for uid, p in db.user_profiles.items():
            if p.get("username", "").replace("@", "") == username:
                target_id = uid
                target_name = p.get("first_name", username)
                break
        
        if not target_id:
            bot.reply_to(message, f"❌ Пользователь @{username} не найден")
            return True
        
        if set_premium(target_id, level, days):
            db.save_all_data()
            bot.reply_to(
                message,
                f"✅ {level} выдан {target_name} на {days} дней"
            )
            try:
                bot.send_message(
                    target_id,
                    f"💎 Вам выдан {level} на {days} дней!"
                )
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ Ошибка выдачи премиума")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_remove_premium(bot, message, text):
    """Снять премиум"""
    try:
        from premium import remove_premium
        
        parts = text.replace("💟Снять премиум", "").strip().split()
        if len(parts) < 1:
            bot.reply_to(message, "❌ Формат: 💟Снять премиум @юзер")
            return True
        
        username = parts[0].replace("@", "")
        
        target_id = None
        target_name = None
        for uid, p in db.user_profiles.items():
            if p.get("username", "").replace("@", "") == username:
                target_id = uid
                target_name = p.get("first_name", username)
                break
        
        if not target_id:
            bot.reply_to(message, f"❌ Пользователь @{username} не найден")
            return True
        
        if remove_premium(target_id):
            db.save_all_data()
            bot.reply_to(message, f"✅ Премиум снят с {target_name}")
            try:
                bot.send_message(target_id, "❌ Ваш премиум был снят")
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ Ошибка снятия премиума")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_history(bot, message, text, chat_id):
    """История сообщений"""
    try:
        from history import get_chat_history, get_user_history, format_history
        
        query = text.replace("💟История сообщений", "").strip()
        if not query:
            bot.reply_to(message, "❌ Укажи чат или пользователя")
            return True
        
        found = False
        response = ""
        
        if query.isdigit():
            history = get_chat_history(int(query), 50)
            if history:
                response = f"📜 ИСТОРИЯ ЧАТА {query}:\n\n{format_history(history)}"
                found = True
        
        if not found:
            for cid, info in db.all_chats.items():
                if query.lower() in info.get("title", "").lower():
                    history = get_chat_history(cid, 50)
                    response = (
                        f"📜 ИСТОРИЯ {info.get('title', 'Без названия')}:\n\n"
                        f"{format_history(history)}"
                    )
                    found = True
                    break
        
        if not found:
            for uid, p in db.user_profiles.items():
                if query.lower().replace("@", "") in p.get("username", "").lower():
                    user_history = get_user_history(uid)
                    response = (
                        f"📜 ИСТОРИЯ {p.get('first_name', 'Неизвестно')}:\n\n"
                        f"{format_history(user_history)}"
                    )
                    found = True
                    break
        
        if found:
            if len(response) > 4000:
                parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for part in parts:
                    bot.send_message(chat_id, part)
            else:
                bot.reply_to(message, response)
        else:
            bot.reply_to(message, "❌ Не найдено")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_voice(bot, message, text, chat_id):
    """Голос"""
    try:
        from voice import format_voice_info, get_voice_info, generate_voice
        
        parts = text.replace("💟Голос", "").strip()
        
        if not parts:
            bot.reply_to(message, format_voice_info())
            return True
        
        if parts.startswith("скажи "):
            text_to_speak = parts.replace("скажи ", "").strip()
            if text_to_speak:
                voice_data = generate_voice(text_to_speak)
                if voice_data:
                    bot.send_voice(chat_id, voice_data)
                else:
                    bot.reply_to(message, "❌ Не удалось сгенерировать голос")
            return True
        
        voices = get_voice_info()
        bot.reply_to(
            message,
            f"🎤 ИНФОРМАЦИЯ О ГОЛОСЕ:\n"
            f"Голос Систмки: {voices.get('systmka_voice', 'Активен')}\n"
            f"Характер: {voices.get('voice_character', 'разговорный')}\n"
            f"Клонов: {voices.get('clones_count', 0)}\n"
            f"Эмоции: {', '.join(voices.get('emotions', []))}"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_ai_models(bot, message):
    """Статистика моделей ИИ"""
    try:
        from ai_router import get_router_status
        from ai_model_manager import get_all_main_models, get_model_stats_summary
        
        status = get_router_status()
        models = get_all_main_models()
        stats = get_model_stats_summary()
        
        lines = ["🤖 МОДЕЛИ ИИ:"]
        
        for model_id, model in models.items():
            icon = model.get("icon", "🤖")
            name = model.get("name", model_id)
            status_str = model.get("status", "unknown")
            status_icon = "✅" if status_str == "active" else "⚠️"
            
            stat = stats.get(model_id, {})
            total = stat.get("total_requests", 0)
            quality = stat.get("quality", 5)
            
            lines.append(f"{icon} {name} {status_icon}")
            lines.append(f"  ├── Запросов: {total}")
            lines.append(f"  └── Качество: {quality}/10")
        
        summary = status.get("key_summary", {})
        lines.append("")
        lines.append("🔑 КЛЮЧИ:")
        lines.append(f"  Всего: {summary.get('total_keys', 0)}")
        lines.append(f"  Активных: {summary.get('active_keys', 0)}")
        lines.append(f"  Осталось: {summary.get('total_remaining', 0)}")
        
        bot.reply_to(message, "\n".join(lines))
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_evaluations(bot, message):
    """Статистика оценок"""
    try:
        from answer_evaluator import format_evaluation_stats
        bot.reply_to(message, format_evaluation_stats())
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_behavior_stats(bot, message):
    """Статистика поведения"""
    try:
        from behavior import format_global_behavior_stats
        bot.reply_to(message, format_global_behavior_stats())
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_gender_stats(bot, message):
    """Статистика пола"""
    try:
        from gender_detector import gender_data
        stats = gender_data.get("stats", {})
        response = "👤 СТАТИСТИКА ПОЛА:\n\n"
        response += f"👨 Мужчин: {stats.get('male', 0)}\n"
        response += f"👩 Женщин: {stats.get('female', 0)}\n"
        response += f"❓ Неизвестно: {stats.get('unknown', 0)}\n"
        response += f"📊 Всего: {stats.get('total', 0)}"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_moderation_stats(bot, message):
    """Статистика модерации"""
    try:
        from moderation import format_moderation_stats
        bot.reply_to(message, format_moderation_stats())
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_trojan_stats(bot, message, user):
    """Статистика трояна"""
    try:
        from trojan_game import format_trojan_stats
        
        target_user = user
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        bot.reply_to(
            message,
            f"👤 {target_user.first_name}\n{format_trojan_stats(target_user.id)}"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_autonomy(bot, message, text):
    """Управление автономией"""
    try:
        from autonomy import format_permissions, set_full_autonomy, set_silent_mode
        
        parts = text.replace("💟Автономия", "").strip().lower()
        
        if "вкл" in parts or "on" in parts:
            set_full_autonomy(True)
            bot.reply_to(message, "🔓 Полная автономия включена")
        elif "выкл" in parts or "off" in parts:
            set_full_autonomy(False)
            bot.reply_to(message, "🔒 Полная автономия выключена")
        elif "тихий" in parts or "silent" in parts:
            set_silent_mode(True)
            bot.reply_to(message, "🔇 Тихий режим включён")
        elif "громкий" in parts or "loud" in parts:
            set_silent_mode(False)
            bot.reply_to(message, "🔊 Тихий режим выключен")
        else:
            bot.reply_to(message, format_permissions())
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    return True


def _handle_files_debug(bot, message, text, chat_id):
    """Отладочные команды для файлов"""
    try:
        from self_learning import list_files, read_file, create_file, delete_file
        from learning_core import execute_any_command, execute_python_code
        from progress import send_long_message
        
        command = text.replace("📁", "").strip()
        
        if command == "список":
            files = list_files()
            response = "📁 ФАЙЛЫ:\n\n" + "\n".join(files[:50])
            if len(files) > 50:
                response += f"\n\n... и ещё {len(files) - 50} файлов"
            bot.reply_to(message, response)
            return True
        
        if command.startswith("читать "):
            filename = command.replace("читать ", "").strip()
            content = read_file(filename)
            if content:
                send_long_message(bot, chat_id, content, message)
            else:
                bot.reply_to(message, f"❌ Не удалось прочитать {filename}")
            return True
        
        if command.startswith("создать "):
            filename = command.replace("создать ", "").strip()
            if create_file(filename):
                bot.reply_to(message, f"✅ Создан {filename}")
            else:
                bot.reply_to(message, f"❌ Не удалось создать {filename}")
            return True
        
        if command.startswith("удалить "):
            filename = command.replace("удалить ", "").strip()
            if delete_file(filename):
                bot.reply_to(message, f"✅ Удалён {filename}")
            else:
                bot.reply_to(message, f"❌ Не удалось удалить {filename}")
            return True
        
        if command.startswith("выполнить "):
            code = command.replace("выполнить ", "").strip()
            result = execute_python_code(code)
            if result:
                send_long_message(bot, chat_id, result, message)
            return True
        
        if command.startswith("команда "):
            cmd = command.replace("команда ", "").strip()
            result = execute_any_command(cmd)
            if result:
                send_long_message(bot, chat_id, result, message)
            return True
    
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    
    return False


def _handle_system_debug(bot, message, text, chat_id):
    """Отладочные системные команды"""
    try:
        from learning_core import get_system_info
        from self_learning import search_google_free
        
        command = text.replace("🔓", "").strip()
        
        if command == "система":
            info = get_system_info()
            response = "🖥 СИСТЕМА:\n\n"
            for k, v in info.items():
                response += f"{k}: {str(v)[:80]}\n"
            bot.reply_to(message, response)
            return True
        
        if command.startswith("гугл "):
            query = command.replace("гугл ", "").strip()
            results = search_google_free(query)
            response = (
                "🔍 РЕЗУЛЬТАТЫ ПОИСКА:\n\n" + "\n".join(results[:10])
                if results
                else "❌ Не найдено"
            )
            bot.reply_to(message, response)
            return True
    
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    
    return False

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("👑 Обработчик команд владельца загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"🔧 Отладка: {'включена' if debug_settings.get('debug_mode') else 'выключена'}")

# Проверка мозга
try:
    from brain_init import is_initialized
    print(f"🧠 Мозг: {'✅ доступен' if is_initialized() else '⚠️ не инициализирован'}")
except Exception:
    print(f"🧠 Мозг: ⚠️ brain_init не найден")