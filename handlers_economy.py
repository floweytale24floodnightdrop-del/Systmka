"""Экономика — казино, кредиты, переводы, штрафы"""

import telebot
import random
import time
import threading
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, HELPER_IDS
import database as db
from premium import check_premium

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

# Интервал фоновой обработки кредитов (секунды)
CREDITS_LOOP_INTERVAL = 3600  # 1 час

# Процент ежедневного платежа
CREDIT_DAILY_PERCENT = 0.20

# Штраф за неуплату (множитель)
CREDIT_PENALTY_MULTIPLIER = 10

# ============================================================
# 3. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def register_economy_handlers(bot, message, text, chat_id, user, is_owner_user, profile):
    """
    Обработка экономических команд.
    
    Returns:
        bool: True если команда обработана
    """
    
    # ============================================================
    # 3.1 ПОДАРОЧЕК
    # ============================================================
    
    if "💟Подарочек" in text:
        return _handle_gift(bot, message, user, profile)
    
    # ============================================================
    # 3.2 КАЗИНО
    # ============================================================
    
    if "💟Казино" in text:
        return _handle_casino(bot, message, text, user)
    
    # ============================================================
    # 3.3 КРЕДИТ
    # ============================================================
    
    if "💟Кредит" in text:
        return _handle_credit(bot, message, text, user)
    
    # ============================================================
    # 3.4 ОПЛАТА КРЕДИТА
    # ============================================================
    
    if "💟Оплатить" in text:
        return _handle_pay_credit(bot, message, text, user)
    
    # ============================================================
    # 3.5 ПЕРЕВОД
    # ============================================================
    
    if "💟Перевод" in text:
        return _handle_transfer(bot, message, text, user)
    
    # ============================================================
    # 3.6 ШТРАФ
    # ============================================================
    
    if "💟Штраф" in text:
        return _handle_fine(bot, message, text, user)
    
    # ============================================================
    # 3.7 СНЯТЬ ШТРАФ
    # ============================================================
    
    if "💟Снять штраф" in text:
        return _handle_remove_fine(bot, message, text, user)
    
    return False

# ============================================================
# 4. ОБРАБОТЧИКИ
# ============================================================

def _handle_gift(bot, message, user, profile):
    """Подарочек — раз в 2 часа"""
    last_gift = profile.get("last_gift_time")
    
    if last_gift:
        if isinstance(last_gift, str):
            try:
                last_gift = datetime.fromisoformat(last_gift)
            except (ValueError, TypeError):
                last_gift = None
        
        if last_gift and (datetime.now() - last_gift).total_seconds() < 7200:
            remaining = 7200 - (datetime.now() - last_gift).total_seconds()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            bot.reply_to(
                message,
                f"⏳ Подарочек уже забран! Попробуй через {hours}ч {minutes}м"
            )
            return True
    
    gift = random.randint(1, 5)
    
    # Бонус за FTF24
    try:
        from bot import check_ftf24
        if check_ftf24(user):
            gift *= 2
    except Exception:
        pass
    
    db.add_glitches(user.id, gift, OWNER_IDS)
    profile["last_gift_time"] = datetime.now()
    bot.reply_to(message, f"🎁 +{gift}👾")
    return True


def _handle_casino(bot, message, text, user):
    """Казино"""
    try:
        bet = int(text.replace("💟Казино", "").strip())
    except ValueError:
        bot.reply_to(message, "❌ Введи число: 💟Казино <ставка>")
        return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True
    
    if bet <= 0:
        bot.reply_to(message, "❌ Ставка должна быть больше 0")
        return True
    
    current = db.get_user_glitches(user.id, OWNER_IDS)
    if current != float('inf') and current < bet:
        bot.reply_to(message, f"❌ Нужно {bet}👾, у тебя {current}👾")
        return True
    
    # Списываем ставку
    if current != float('inf'):
        db.add_glitches(user.id, -bet, OWNER_IDS)
    
    symbols = ["7⃣", "🍒", "💀", "🌟", "🎀", "🌸", "⭐"]
    result = [random.choice(symbols) for _ in range(3)]
    display = "".join(result)
    
    if result[0] == result[1] == result[2]:
        if result[0] == "7⃣":
            win = bet * 7
        elif result[0] == "💀":
            win = -bet * 2
        elif result[0] == "🌟":
            win = bet * 2
        else:
            win = int(bet * 1.5)
        
        db.add_glitches(user.id, win, OWNER_IDS)
        bot.reply_to(
            message,
            f"{display}\n{'+' if win > 0 else ''}{win}👾"
        )
    else:
        bot.reply_to(message, f"{display}\n-{bet}👾")
    
    return True


def _handle_credit(bot, message, text, user):
    """Взять кредит"""
    try:
        amount = int(text.replace("💟Кредит", "").strip())
    except ValueError:
        bot.reply_to(message, "❌ Введи число: 💟Кредит <сумма>")
        return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True
    
    if amount < 50 or amount > 1000:
        bot.reply_to(message, "❌ Кредит от 50 до 1000👾")
        return True
    
    if user.id in db.user_credits:
        bot.reply_to(message, "❌ У тебя уже есть кредит")
        return True
    
    db.user_credits[user.id] = {
        "amount": amount,
        "remaining": amount,
        "date": datetime.now(),
        "next_payment": datetime.now() + timedelta(days=1),
    }
    db.add_glitches(user.id, amount, OWNER_IDS)
    bot.reply_to(message, f"✅ Кредит {amount}👾 выдан! Каждый день -20%")
    return True


def _handle_pay_credit(bot, message, text, user):
    """Оплатить кредит (ручная оплата)"""
    if user.id not in db.user_credits:
        bot.reply_to(message, "❌ У тебя нет кредита")
        return True
    
    credit = db.user_credits[user.id]
    remaining = credit.get("remaining", credit.get("amount", 0))
    
    parts = text.replace("💟Оплатить", "").strip().split()
    if parts:
        try:
            pay_amount = int(parts[0])
        except ValueError:
            pay_amount = remaining
    else:
        pay_amount = remaining
    
    if pay_amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше 0")
        return True
    
    current = db.get_user_glitches(user.id, OWNER_IDS)
    if current != float('inf') and current < pay_amount:
        bot.reply_to(message, f"❌ Нужно {pay_amount}👾, у тебя {current}👾")
        return True
    
    if current != float('inf'):
        db.add_glitches(user.id, -pay_amount, OWNER_IDS)
    
    new_remaining = max(0, remaining - pay_amount)
    credit["remaining"] = new_remaining
    
    if new_remaining <= 0:
        del db.user_credits[user.id]
        bot.reply_to(message, "✅ Кредит полностью погашен!")
    else:
        bot.reply_to(
            message,
            f"✅ Оплачено {pay_amount}👾. Осталось: {new_remaining}👾"
        )
    
    return True


def _handle_transfer(bot, message, text, user):
    """Перевод глитчей"""
    parts = text.replace("💟Перевод", "").strip().split()
    if not parts:
        bot.reply_to(message, "❌ Формат: 💟Перевод <сумма> @юзер [сообщение]")
        return True
    
    try:
        amount = int(parts[0])
    except ValueError:
        bot.reply_to(message, "❌ Введи число: 💟Перевод <сумма> @юзер")
        return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше 0")
        return True
    
    # Определяем получателя
    target_id = None
    target_name = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(parts) > 1:
        username = parts[1].replace("@", "")
        for uid, p in db.user_profiles.items():
            if p.get("username", "").replace("@", "") == username:
                target_id = uid
                target_name = p.get("first_name", username)
                break
    
    if not target_id:
        bot.reply_to(message, "❌ Пользователь не найден")
        return True
    
    if target_id == user.id:
        bot.reply_to(message, "❌ Нельзя переводить самому себе")
        return True
    
    if user.id in db.user_credits:
        bot.reply_to(message, "❌ Нельзя переводить с активным кредитом!")
        return True
    
    # Комиссия
    has_premium = check_premium(user.id, OWNER_IDS)
    rate = 0.10 if has_premium else 0.30
    commission = int(amount * rate)
    total = amount + commission
    
    current = db.get_user_glitches(user.id, OWNER_IDS)
    if current != float('inf') and current < total:
        bot.reply_to(
            message,
            f"❌ Нужно {total}👾 (комиссия {commission}👾)\nУ тебя: {current}👾"
        )
        return True
    
    if current != float('inf'):
        db.add_glitches(user.id, -total, OWNER_IDS)
    
    db.add_glitches(target_id, amount, OWNER_IDS)
    
    # Сообщение получателю
    msg = " ".join(parts[2:]) if len(parts) > 2 else ""
    try:
        bot.send_message(
            target_id,
            f"💜 Тебе перевели {amount}👾 от {user.first_name}!\n{msg}"
        )
    except Exception:
        pass
    
    bot.reply_to(
        message,
        f"✅ {amount}👾 переведено {target_name} (комиссия {commission}👾)"
    )
    return True


def _handle_fine(bot, message, text, user):
    """Штраф (только для владельца/помощника)"""
    if user.id not in OWNER_IDS and user.id not in HELPER_IDS:
        bot.reply_to(message, "❌ Только владелец или помощник может накладывать штраф!")
        return True
    
    parts = text.replace("💟Штраф", "").strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Формат: 💟Штраф <сумма> @юзер [причина]")
        return True
    
    try:
        amount = int(parts[0])
    except ValueError:
        bot.reply_to(message, "❌ Введи число: 💟Штраф <сумма> @юзер [причина]")
        return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма штрафа должна быть больше 0")
        return True
    
    # Ищем пользователя
    username = parts[1].replace("@", "")
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
    
    if target_id in OWNER_IDS:
        bot.reply_to(message, "❌ Нельзя наложить штраф на владельца!")
        return True
    
    reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
    
    current = db.get_user_glitches(target_id, OWNER_IDS)
    if current == float('inf'):
        bot.reply_to(message, "❌ Нельзя наложить штраф на владельца")
        return True
    
    actual_amount = min(amount, current)
    db.add_glitches(target_id, -actual_amount, OWNER_IDS)
    
    # Уведомляем получателя
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(
            "⚖️ Обжаловать",
            callback_data=f"appeal_fine_{user.id}"
        ))
        bot.send_message(
            target_id,
            f"💸 На вас наложен штраф!\n"
            f"📊 Сумма: {actual_amount}👾\n"
            f"📝 Причина: {reason}\n"
            f"👮 Кто: {user.first_name}\n\n"
            f"Осталось: {db.get_user_glitches(target_id, OWNER_IDS)}👾",
            reply_markup=keyboard
        )
    except Exception:
        pass
    
    bot.reply_to(
        message,
        f"✅ Штраф {actual_amount}👾 наложен на {target_name}\n"
        f"📝 Причина: {reason}\n"
        f"📊 Осталось: {db.get_user_glitches(target_id, OWNER_IDS)}👾"
    )
    return True


def _handle_remove_fine(bot, message, text, user):
    """Снять штраф"""
    if user.id not in OWNER_IDS and user.id not in HELPER_IDS:
        bot.reply_to(message, "❌ Только владелец или помощник может снимать штраф!")
        return True
    
    parts = text.replace("💟Снять штраф", "").strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Формат: 💟Снять штраф <сумма> @юзер [причина]")
        return True
    
    try:
        amount = int(parts[0])
    except ValueError:
        bot.reply_to(message, "❌ Введи число: 💟Снять штраф <сумма> @юзер")
        return True
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        return True
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше 0")
        return True
    
    # Ищем пользователя
    username = parts[1].replace("@", "")
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
    
    db.add_glitches(target_id, amount, OWNER_IDS)
    
    reason = " ".join(parts[2:]) if len(parts) > 2 else "Штраф снят"
    
    # Уведомление
    try:
        bot.send_message(
            target_id,
            f"✅ Штраф снят!\n"
            f"📊 Сумма возвращена: {amount}👾\n"
            f"📝 Причина: {reason}\n"
            f"👮 Кто: {user.first_name}\n\n"
            f"Теперь у вас: {db.get_user_glitches(target_id, OWNER_IDS)}👾"
        )
    except Exception:
        pass
    
    bot.reply_to(
        message,
        f"✅ Штраф {amount}👾 снят с {target_name}\n"
        f"📝 Причина: {reason}\n"
        f"📊 Теперь у {target_name}: {db.get_user_glitches(target_id, OWNER_IDS)}👾"
    )
    return True

# ============================================================
# 5. ОБРАБОТКА КРЕДИТОВ (ИСПРАВЛЕНО!)
# ============================================================

def process_credit_for_user(bot, user_id):
    """
    Обработать платёж для ОДНОГО пользователя.
    
    Вызывается из callback-обработчика (кнопка "Оплатить").
    
    Returns:
        bool: True если был обработан платёж
    """
    if user_id not in db.user_credits:
        return False
    
    credit = db.user_credits[user_id]
    now = datetime.now()
    next_payment = credit.get("next_payment")
    
    if isinstance(next_payment, str):
        try:
            next_payment = datetime.fromisoformat(next_payment)
        except (ValueError, TypeError):
            next_payment = None
    
    # Если платёж ещё не наступил — ничего не делаем
    if not next_payment or now < next_payment:
        return False
    
    amount = credit.get("amount", 0)
    payment = int(amount * CREDIT_DAILY_PERCENT)
    remaining = credit.get("remaining", amount)
    current = db.get_user_glitches(user_id, OWNER_IDS)
    
    if current == float('inf'):
        return False
    
    if current >= payment:
        # Обычный платёж
        db.add_glitches(user_id, -payment, OWNER_IDS)
        new_remaining = max(0, remaining - payment)
        credit["remaining"] = new_remaining
        msg = (
            f"💳 Платёж по кредиту: -{payment}👾\n"
            f"Осталось: {new_remaining}👾"
        )
    else:
        # Штраф за неуплату
        penalty = (payment - current) * CREDIT_PENALTY_MULTIPLIER
        db.add_glitches(user_id, -penalty, OWNER_IDS)
        msg = f"❌ Штраф за неуплату!\nМинус: {penalty}👾"
    
    credit["next_payment"] = now + timedelta(days=1)
    
    # Уведомляем
    try:
        bot.send_message(user_id, msg)
    except Exception:
        pass
    
    # Проверяем, погашен ли кредит
    if credit.get("remaining", 0) <= 0:
        del db.user_credits[user_id]
        try:
            bot.send_message(user_id, "✅ Кредит погашен!")
        except Exception:
            pass
    
    return True


def process_credit_payments(bot):
    """
    Обработка ежедневных платежей по ВСЕМ кредитам.
    
    Вызывается из фонового цикла (credits_background_loop).
    
    Returns:
        int: количество обработанных платежей
    """
    now = datetime.now()
    processed = 0
    
    # Копируем ключи, чтобы безопасно удалять
    for user_id in list(db.user_credits.keys()):
        credit = db.user_credits[user_id]
        next_payment = credit.get("next_payment")
        
        # Парсим next_payment
        if isinstance(next_payment, str):
            try:
                next_payment = datetime.fromisoformat(next_payment)
            except (ValueError, TypeError):
                next_payment = None
        
        if not next_payment or now < next_payment:
            continue
        
        amount = credit.get("amount", 0)
        payment = int(amount * CREDIT_DAILY_PERCENT)
        remaining = credit.get("remaining", amount)
        current = db.get_user_glitches(user_id, OWNER_IDS)
        
        if current == float('inf'):
            continue
        
        if current >= payment:
            db.add_glitches(user_id, -payment, OWNER_IDS)
            new_remaining = max(0, remaining - payment)
            credit["remaining"] = new_remaining
            msg = (
                f"💳 Платёж по кредиту: -{payment}👾\n"
                f"Осталось: {new_remaining}👾"
            )
        else:
            penalty = (payment - current) * CREDIT_PENALTY_MULTIPLIER
            db.add_glitches(user_id, -penalty, OWNER_IDS)
            msg = f"❌ Штраф за неуплату!\nМинус: {penalty}👾"
        
        credit["next_payment"] = now + timedelta(days=1)
        
        # Уведомляем с кнопкой
        try:
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton(
                "💳 Оплатить",
                callback_data="pay_credit"
            ))
            bot.send_message(user_id, msg, reply_markup=keyboard)
            processed += 1
        except Exception:
            pass
        
        # Проверяем, погашен ли кредит
        if credit.get("remaining", 0) <= 0:
            del db.user_credits[user_id]
            try:
                bot.send_message(user_id, "✅ Кредит погашен!")
            except Exception:
                pass
    
    return processed


def credits_background_loop(bot, interval=CREDITS_LOOP_INTERVAL):
    """
    Фоновый цикл обработки кредитов.
    
    Запускается из bot_loops.py в отдельном потоке.
    По умолчанию — раз в час.
    
    Args:
        bot: telebot instance
        interval: интервал в секундах
    """
    print(f"💳 Цикл кредитов запущен (интервал: {interval}с)")
    
    while True:
        try:
            time.sleep(interval)
            
            processed = process_credit_payments(bot)
            if processed > 0:
                print(f"💳 Обработано кредитов: {processed}")
        
        except Exception as e:
            print(f"⚠️ Ошибка в credits_background_loop: {e}")
            time.sleep(60)

# ============================================================
# 6. УВЕДОМЛЕНИЯ О НАКАЗАНИЯХ
# ============================================================

def notify_punishment(bot, user_id, punishment_type, reason, duration, by_user):
    """Уведомить пользователя о наказании"""
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(
            "⚖️ Оспорить",
            callback_data=f"appeal_{punishment_type}_{by_user}"
        ))
        
        if punishment_type == "mute":
            msg = (
                f"🔇 Тебе выдали мут!\n"
                f"Причина: {reason}\n"
                f"Срок: {duration}\n"
                f"Кто: {by_user}"
            )
        elif punishment_type == "ban":
            msg = (
                f"🚫 Тебя забанили!\n"
                f"Причина: {reason}\n"
                f"Срок: {duration}\n"
                f"Кто: {by_user}"
            )
        elif punishment_type == "warn":
            msg = f"⚠️ Тебе выдали варн!\nПричина: {reason}\nКто: {by_user}"
        else:
            msg = f"Наказание: {punishment_type}\nПричина: {reason}"
        
        bot.send_message(user_id, msg, reply_markup=keyboard)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка notify_punishment: {e}")
        return False


def process_appeal(bot, call):
    """Обработать апелляцию"""
    try:
        data = call.data.split("_")
        punishment_type = data[1] if len(data) > 1 else "unknown"
        
        try:
            by_user_id = int(data[2]) if len(data) > 2 else 0
        except ValueError:
            by_user_id = 0
        
        if by_user_id:
            try:
                bot.send_message(
                    by_user_id,
                    f"⚖️ {call.from_user.first_name} "
                    f"(@{call.from_user.username}) оспорил наказание!\n"
                    f"Тип: {punishment_type}\n\n"
                    f"Поговори с ним: "
                    f"@{call.from_user.username or call.from_user.first_name}"
                )
            except Exception:
                pass
        
        bot.answer_callback_query(call.id, "📨 Апелляция отправлена!")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка process_appeal: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка")
        except Exception:
            pass
        return False

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("💰 Модуль экономики загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")
print(f"👤 С кредитом: {len(db.user_credits)}")
print(f"💳 Интервал обработки кредитов: {CREDITS_LOOP_INTERVAL}с")