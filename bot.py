"""Главный файл запуска Систмки — ядро"""

import telebot
import threading
import time
import json
import os
import sys
import requests
from datetime import datetime

# ============================================================
# 0. ФОРСИРУЕМ UTF-8 ДЛЯ WINDOWS CMD
# ============================================================

if sys.platform == "win32":
    try:
        import io
        _original_stdout = sys.stdout
        _original_stderr = sys.stderr
        
        if hasattr(_original_stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(
                _original_stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stdout._original = _original_stdout
        
        if hasattr(_original_stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(
                _original_stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stderr._original = _original_stderr
    except Exception:
        pass

# ============================================================
# 1. КРИТИЧЕСКИЕ ИМПОРТЫ
# ============================================================

from config import (
    TELEGRAM_TOKEN, OPENROUTER_KEYS, OPENROUTER_EMAILS,
    OWNER_IDS, ALL_STICKERS, moscow_tz, GEMINI_KEY, HUGGINGFACE_KEY
)

import database as db

from module_fixer import module_manager

from auto_import import *

from system_prompt import SYSTEM_PROMPT

from learning_manager import init_learning
from ai_key_rotator import init_keys, start_stats_updater
from prompt_notes_manager import prompt_manager

# ============================================================
# 1.5 МОЗГ СИСТМКИ (НОВОЕ!)
# ============================================================

from brain_init import init_brain, shutdown_brain, is_initialized

# ============================================================
# 2. ИНИЦИАЛИЗАЦИЯ КЛЮЧЕЙ
# ============================================================

print("=" * 60)
print("🔑 ИНИЦИАЛИЗАЦИЯ КЛЮЧЕЙ...")
print("=" * 60)

init_keys(OPENROUTER_KEYS, OPENROUTER_EMAILS, GEMINI_KEY, HUGGINGFACE_KEY)
start_stats_updater()

# ============================================================
# 3. ПРОВЕРКА ЗАМОРОЖЕННЫХ МОДУЛЕЙ
# ============================================================

print("=" * 60)
print("🛡️ ПРОВЕРКА ЗАМОРОЖЕННЫХ МОДУЛЕЙ...")
print("=" * 60)

if module_manager:
    status = module_manager.get_status()
    if status.get('frozen_modules'):
        print(f"❄️ Заморожено модулей: {len(status['frozen_modules'])}")
        print(f"   📦 {', '.join(status['frozen_modules'])}")
    else:
        print("✅ Нет замороженных модулей")

# ============================================================
# 4. ИНИЦИАЛИЗАЦИЯ ПРОМТОВ (АСИНХРОННО)
# ============================================================

print("=" * 60)
print("📝 ИНИЦИАЛИЗАЦИЯ ПРОМТОВ...")
print("=" * 60)

try:
    prompt_manager.init_all_prompts_async()
    print("📝 Промты инициализируются в фоне")
except Exception as e:
    print(f"⚠️ Ошибка инициализации промтов: {e}")

# ============================================================
# 4.5 ИНИЦИАЛИЗАЦИЯ МОЗГА (НОВОЕ!)
# ============================================================

print("=" * 60)
print("🧠 ИНИЦИАЛИЗАЦИЯ МОЗГА...")
print("=" * 60)

try:
    brain_ok = init_brain(auto_start=True)
    if brain_ok:
        print("✅ Мозг Систмки готов")
    else:
        print("⚠️ Мозг не инициализирован — работаем без него")
except Exception as e:
    print(f"⚠️ Ошибка инициализации мозга: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# 5. СИСТМКА ЗАПУСКАЕТСЯ
# ============================================================

print("=" * 60)
print("🤖 СИСТМКА ЗАПУСКАЕТСЯ...")
print("=" * 60)

# ============================================================
# 6. ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

bot_startup_time = datetime.now()
startup_grace_period = 10
last_request_time = {}
request_interval = 1.5

STATE_FILE = "bot_state.json"

debug_settings = {
    "debug_mode": False,
    "learning_mode": True,
    "auto_respond": True,
}

bot_status = {
    "running": False,
    "start_time": None,
    "messages_processed": 0,
    "errors_count": 0,
    "last_error": None,
    "ai_requests_saved": 0,
    "total_ai_requests": 0,
}

# ============================================================
# 7. СТАТУС СИСТМКИ
# ============================================================

systmka_status = {
    "online": True,
    "last_seen": None,
}

# ============================================================
# 8. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def save_state():
    """
    Сохранить состояние бота.
    """
    try:
        serializable_bot_status = {}
        for key, value in bot_status.items():
            if isinstance(value, datetime):
                serializable_bot_status[key] = value.isoformat()
            else:
                serializable_bot_status[key] = value
        
        state = {
            "last_request_time": {
                str(k): v.isoformat() if isinstance(v, datetime) else str(v)
                for k, v in last_request_time.items()
            },
            "bot_status": serializable_bot_status,
            "systmka_status": systmka_status,
            "saved_at": datetime.now().isoformat(),
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка save_state: {e}")
        return False


def load_state():
    """
    Загрузить состояние бота.
    """
    global last_request_time, bot_status, systmka_status
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            for k, v in state.get("last_request_time", {}).items():
                try:
                    last_request_time[int(k)] = datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    pass
            
            if isinstance(state.get("bot_status"), dict):
                loaded_status = state["bot_status"]
                if loaded_status.get("start_time"):
                    try:
                        loaded_status["start_time"] = datetime.fromisoformat(
                            loaded_status["start_time"]
                        )
                    except (ValueError, TypeError):
                        loaded_status["start_time"] = None
                bot_status.update(loaded_status)
            
            if isinstance(state.get("systmka_status"), dict):
                systmka_status.update(state["systmka_status"])
            
            return True
    except Exception:
        pass
    return False


def log_error(error, source="unknown"):
    """Логировать ошибку"""
    try:
        from log_manager import smart_logger
        smart_logger.error(error, source)
    except Exception:
        print(f"❌ [{source}] {error}")


def get_moscow_time():
    """Московское время"""
    return datetime.now(moscow_tz)


def is_admin_or_owner(chat_id, user_id):
    """Проверить, админ ли пользователь в чате"""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ('creator', 'administrator')
    except Exception:
        return False


def is_owner(user_id):
    """Проверить, владелец ли пользователь"""
    return user_id in OWNER_IDS


def is_private_chat(message):
    """ЛС?"""
    return message.chat.type == "private"


def is_group_chat(message):
    """Группа?"""
    return message.chat.type in ('group', 'supergroup')


def is_channel(message):
    """Канал?"""
    return message.chat.type == "channel"


def check_rate_limit(chat_id):
    """Проверить rate limit"""
    now = datetime.now()
    if not last_request_time:
        load_state()
    
    if chat_id in last_request_time:
        if (now - last_request_time[chat_id]).total_seconds() < request_interval:
            return False
    
    last_request_time[chat_id] = now
    save_state()
    return True


def check_startup_grace():
    """Grace-период после старта"""
    return (datetime.now() - bot_startup_time).total_seconds() < startup_grace_period


def check_ftf24(user):
    """Проверить приписку #FTF24"""
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_check = f"{username} {first_name} {last_name}".upper()
    return "#FTF24" in full_check or "FTF24" in username.upper()


def send_to_user(user_id, text):
    """Отправить сообщение пользователю"""
    try:
        bot.send_message(user_id, text)
        return True
    except Exception:
        return False


def get_chat_members(bot_instance, chat_id):
    """Получить участников чата"""
    members = []
    
    try:
        admins = bot_instance.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                members.append(admin.user)
    except Exception:
        pass
    
    for uid, p in db.user_profiles.items():
        if p.get("is_bot", False):
            continue
        
        try:
            member = bot_instance.get_chat_member(chat_id, uid)
            if member.status in ('creator', 'administrator', 'member'):
                if not any(m.id == uid for m in members):
                    class FakeUser:
                        def __init__(self, uid, first_name, username):
                            self.id = uid
                            self.first_name = first_name
                            self.username = (
                                username.replace("@", "") if username else None
                            )
                            self.is_bot = False
                    
                    members.append(FakeUser(
                        uid,
                        p.get("first_name", "?"),
                        p.get("username", ""),
                    ))
        except Exception:
            pass
    
    return members


def check_owner_present(chat_id):
    """Есть ли владелец в чате"""
    return db.chat_owner_present.get(chat_id, False)


def update_chat_info(message):
    """Обновить информацию о чате"""
    chat_id = message.chat.id
    
    if message.chat.type not in ('group', 'supergroup'):
        return
    
    try:
        chat = bot.get_chat(chat_id)
        db.all_chats[chat_id] = {
            "title": chat.title,
            "type": chat.type,
            "last_active": datetime.now(),
            "member_count": bot.get_chat_member_count(chat_id),
        }
        
        has_owner = False
        for oid in OWNER_IDS:
            try:
                member = bot.get_chat_member(chat_id, oid)
                if member.status in ('creator', 'administrator', 'member'):
                    has_owner = True
                    break
            except Exception:
                pass
        
        db.chat_owner_present[chat_id] = has_owner
    except Exception:
        pass


def clean_logs_now():
    """Очистить логи"""
    log_files = ["bot.log", "boot.log"]
    
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                with open(log_file, "r", encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if len(lines) > 200:
                    with open(log_file, "w", encoding='utf-8') as f:
                        f.writelines(lines[-200:])
                    print(f"✂️ {log_file} обрезан до 200 строк")
        except Exception:
            pass


def update_profile_status(text):
    """Обновить описание профиля бота"""
    try:
        bot.set_my_description(text)
        return True
    except Exception:
        return False


def _save_all_on_exit():
    """Сохранить все данные при выходе"""
    
    # === НОВОЕ: Остановить мозг ===
    try:
        from brain_init import shutdown_brain
        shutdown_brain()
    except Exception as e:
        print(f"⚠️ Ошибка остановки мозга: {e}")
    
    try:
        from consciousness import save_consciousness
        save_consciousness()
    except Exception:
        pass
    
    try:
        db.save_all_data()
    except Exception:
        pass
    
    try:
        save_state()
    except Exception:
        pass
    
    try:
        from roleplay import save_rp_data
        save_rp_data()
    except Exception:
        pass
    
    try:
        from message_analyzer import save_analysis
        save_analysis()
    except Exception:
        pass
    
    try:
        from osint_engine import save_osint_data, save_accounts
        save_osint_data()
        save_accounts()
    except Exception:
        pass
    
    try:
        from ai_key_rotator import save_key_stats
        save_key_stats()
    except Exception:
        pass

# ============================================================
# 9. КОМАНДА /status
# ============================================================

@bot.message_handler(commands=['status'])
def status_command(message):
    """Управление статусом Систмки"""
    if message.from_user.id not in OWNER_IDS:
        bot.reply_to(message, "❌ Только владелец может менять статус")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        current = "в сети" if systmka_status["online"] else "выключена"
        brain_status = "🧠 активен" if is_initialized() else "🧠 не активен"
        bot.reply_to(message, f"🟢 Систмка {current}\n{brain_status}")
        return
    
    arg = parts[1].lower()
    
    if arg in ("on", "включить", "вкл"):
        systmka_status["online"] = True
        bot.reply_to(message, "🟢 Систмка включена")
    elif arg in ("off", "выключить", "выкл"):
        systmka_status["online"] = False
        bot.reply_to(message, "🔴 Систмка выключена")
    else:
        bot.reply_to(message, "❌ Используй: /status on или /status off")

# ============================================================
# 10. КОМАНДА /keys
# ============================================================

@bot.message_handler(commands=['keys'])
def keys_command(message):
    """Статус ключей OpenRouter"""
    if message.from_user.id not in OWNER_IDS:
        bot.reply_to(message, "❌ Только владелец может смотреть ключи")
        return
    
    try:
        from ai_key_rotator import (
            get_all_openrouter_keys_status,
            get_key_stats_summary,
        )
        
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
            status_icon = (
                "✅" if status == "active"
                else "⚠️" if status == "low"
                else "🔴"
            )
            response += f"{status_icon} {email} — {remaining}/{total} ({status})\n"
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ============================================================
# 11. РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ И ЗАПУСК
# ============================================================

from bot_startup import load_all_data
from bot_handlers import (
    register_inline_handler,
    register_message_handler,
    register_callback_handler,
)
from bot_loops import start_background_threads, initialize_consciousness

# Загружаем все данные
load_all_data(bot, log_error, bot_status)

# Регистрируем обработчики
register_inline_handler(bot, bot_status, SYSTEM_PROMPT, OPENROUTER_KEYS)
register_message_handler(bot, debug_settings, bot_status)
register_callback_handler(bot)

# Запускаем фоновые потоки
threads = start_background_threads(bot, OWNER_IDS, db)

# Инициализируем сознание
initialize_consciousness()

print("=" * 60)
print("🚀 БОТ ЗАПУЩЕН!")
print(f"📊 Потоков: {len([t for t in threads if t])}")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")
print(f"📝 Промтов: {len(prompt_manager.prompts_cache)}")
print(f"🧠 Мозг: {'✅ активен' if is_initialized() else '❌ не активен'}")
print("=" * 60)

# ============================================================
# 12. СПИСОК КОМАНД В КОНСОЛИ
# ============================================================

print("""
📋 ДОСТУПНЫЕ КОМАНДЫ В КОНСОЛИ:
─────────────────────────────────────────────
  /msg <текст>  - отправить сообщение Систмке
  /status       - статус бота
  /system       - система
  /processes    - топ процессов
  /network      - сеть и IP
  /apps         - запущенные приложения
  /fix          - исправить ошибки
  /emotions     - эмоции
  /personality  - характер
  /dreams       - мечты и страхи
  /memes        - мемы
  /opinions     - мнения о людях
  /help         - справка
  /restart      - перезапуск
  /stop         - остановка
─────────────────────────────────────────────
  💡 Введи команду в консоль и нажми Enter
""")

# ============================================================
# 13. ГЛАВНЫЙ ЦИКЛ
# ============================================================

if __name__ == "__main__":
    while True:
        try:
            bot_status["running"] = True
            bot_status["start_time"] = datetime.now()
            print("🔄 Polling...")
            bot.polling(none_stop=True, interval=3, timeout=60)
        
        except requests.exceptions.ReadTimeout:
            print("⏱ Таймаут! Перезапуск...")
            time.sleep(5)
            continue
        
        except requests.exceptions.ConnectionError:
            print("🔌 Нет соединения! Жду...")
            time.sleep(30)
            continue
        
        except KeyboardInterrupt:
            print("\n👋 Остановлен")
            _save_all_on_exit()
            break
        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            log_error(e, "main")
            time.sleep(30)
            continue
        
        finally:
            bot_status["running"] = False
            _save_all_on_exit()