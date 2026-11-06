"""Диалог с владельцем — консоль + Telegram"""

import os
import sys
import json
import time
import threading
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from error_common import (
    safe_print,
    ensure_stdout,
    is_stdin_available,
)

try:
    from config import OWNER_IDS
except ImportError:
    OWNER_IDS = []

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

OWNER_RESPONSE_TIMEOUT = 300  # 5 минут

# Telegram bot (устанавливается позже из bot.py)
_telegram_bot = None

# Защита от рекурсии
_dialog_lock = threading.Lock()
_dialog_in_progress = False

# ============================================================
# 3. РЕГИСТРАЦИЯ TELEGRAM-БОТА
# ============================================================

def register_telegram_bot(bot):
    """Зарегистрировать Telegram-бот для диалога с владельцем"""
    global _telegram_bot
    _telegram_bot = bot
    safe_print("🛡️ error_dialog: Telegram-бот зарегистрирован")


def is_telegram_available():
    """Проверить, доступен ли Telegram-бот"""
    return _telegram_bot is not None and bool(OWNER_IDS)

# ============================================================
# 4. ДИАЛОГ В КОНСОЛИ
# ============================================================

def ask_owner_console(module_name):
    """
    Спросить владельца в консоли.
    
    Returns:
        str: "freeze" | "fix" | "stop" | "skip" | None (если нет stdin)
    """
    if not is_stdin_available():
        return None
    
    safe_print("")
    safe_print("❓ ЧТО ДЕЛАТЬ С МОДУЛЕМ?")
    safe_print("   [З] — Заморозить (заморозить и продолжить)")
    safe_print("   [И] — Исправить через ИИ")
    safe_print("   [О] — Остановить программу")
    safe_print("   [П] — Пропустить (заглушка без заморозки)")
    safe_print("")
    
    try:
        answer = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None
    except Exception:
        return None
    
    if answer in ("з", "z", "freeze", "заморозить"):
        return "freeze"
    elif answer in ("и", "i", "fix", "исправить"):
        return "fix"
    elif answer in ("о", "o", "stop", "остановить"):
        return "stop"
    elif answer in ("п", "p", "skip", "пропустить"):
        return "skip"
    else:
        safe_print(f"   ❓ Неизвестный ответ: '{answer}' — по умолчанию замораживаю")
        return "freeze"

# ============================================================
# 5. ДИАЛОГ В TELEGRAM
# ============================================================

def ask_owner_telegram(module_name, report_text):
    """
    Спросить владельца в Telegram.
    
    Returns:
        str: "freeze" | "fix" | "stop" | "skip" | None
    """
    global _dialog_in_progress
    
    if not is_telegram_available():
        return None
    
    # Защита от рекурсии
    with _dialog_lock:
        if _dialog_in_progress:
            return "freeze"
        _dialog_in_progress = True
    
    try:
        import telebot
        
        # Inline-клавиатура
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                "❄️ Заморозить",
                callback_data=f"guardian_freeze_{module_name}"
            ),
            telebot.types.InlineKeyboardButton(
                "🔧 Исправить",
                callback_data=f"guardian_fix_{module_name}"
            ),
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                "🛑 Остановить бота",
                callback_data=f"guardian_stop_{module_name}"
            ),
            telebot.types.InlineKeyboardButton(
                "⏭ Пропустить",
                callback_data=f"guardian_skip_{module_name}"
            ),
        )
        
        # Отчёт (обрезка до 4000)
        short_report = report_text[:4000]
        
        sent_messages = []
        for oid in OWNER_IDS:
            try:
                msg = _telegram_bot.send_message(
                    oid,
                    short_report,
                    reply_markup=keyboard
                )
                sent_messages.append((oid, msg.message_id))
            except Exception as e:
                safe_print(f"⚠️ Не удалось отправить {oid}: {e}")
        
        if not sent_messages:
            return None
        
        # Файлы для ожидания ответа
        pending_file = f"guardian_pending_{module_name}.json"
        answer_file = f"guardian_answer_{module_name}.json"
        
        # Чистим старый ответ если был
        try:
            if os.path.exists(answer_file):
                os.remove(answer_file)
        except Exception:
            pass
        
        # Пишем pending
        try:
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump({
                    "module": module_name,
                    "asked_at": datetime.now().isoformat(),
                    "owners": [oid for oid, _ in sent_messages],
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        # Ждём ответа
        start_time = time.time()
        while time.time() - start_time < OWNER_RESPONSE_TIMEOUT:
            if os.path.exists(answer_file):
                try:
                    with open(answer_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    answer = data.get("answer", "freeze")
                    
                    # Удаляем файлы
                    for f_path in (pending_file, answer_file):
                        try:
                            os.remove(f_path)
                        except Exception:
                            pass
                    
                    return answer
                except Exception:
                    pass
            
            time.sleep(1)
        
        # Таймаут
        safe_print(f"⏰ Владелец не ответил за {OWNER_RESPONSE_TIMEOUT}с")
        
        try:
            os.remove(pending_file)
        except Exception:
            pass
        
        return "freeze"
    
    finally:
        with _dialog_lock:
            _dialog_in_progress = False

# ============================================================
# 6. ОБРАБОТКА ОТВЕТА ВЛАДЕЛЬЦА (ИЗ BOT_HANDLERS)
# ============================================================

def process_guardian_callback(call, bot):
    """
    Обработать callback от владельца.
    
    Вызывается из bot_handlers.py.
    
    Формат: guardian_<action>_<module_name>
    """
    try:
        data = call.data
        parts = data.split("_", 2)
        
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ Неверный формат")
            return
        
        action = parts[1]
        module_name = parts[2]
        
        # Записываем ответ
        answer_file = f"guardian_answer_{module_name}.json"
        try:
            with open(answer_file, "w", encoding="utf-8") as f:
                json.dump({
                    "answer": action,
                    "module": module_name,
                    "answered_at": datetime.now().isoformat(),
                    "answered_by": call.from_user.id,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Ошибка записи: {e}")
            return
        
        action_text = {
            "freeze": "❄️ Заморозить",
            "fix": "🔧 Исправить",
            "stop": "🛑 Остановить",
            "skip": "⏭ Пропустить",
        }.get(action, "❓ Неизвестно")
        
        bot.answer_callback_query(call.id, f"✅ {action_text}")
        
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass
    
    except Exception as e:
        safe_print(f"⚠️ Ошибка process_guardian_callback: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка")
        except Exception:
            pass

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🛡️ error_dialog загружен")
print(f"📱 Telegram: {'✅' if is_telegram_available() else '❌ (не зарегистрирован)'}")
print(f"💻 Консоль: {'✅' if is_stdin_available() else '❌'}")