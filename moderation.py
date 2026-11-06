"""Модерация чата — спам, рейдеры, оскорбления, мут/бан/варн"""

import re
import time
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, HELPER_IDS
import database as db

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

# Маркеры рейдеров
RAID_MARKERS = [
    "#KXD", "#kxd",
    "#PDVL", "#pdvl",
    "¹¹²⁴⁴", "11244",
    "ᶜᵃᵗ", "ᵇᵒᵗ",
]

# Список оскорблений
INSULTS = [
    "тупой", "тупая", "дурак", "дура",
    "идиот", "идиотка", "дебил", "дебилка",
    "ублюдок", "мразь", "тварь",
    "сука", "блядь", "пизда", "хуй", "мудак", "гандон", "пидор",
    "чмо", "лох", "козел", "козёл",
]

# Сколько времени держать мут за спам (минуты)
SPAM_MUTE_MINUTES = 15

# ============================================================
# 3. ПРОВЕРКА СПАМА
# ============================================================

def check_spam(message, spam_counter=None):
    """
    Проверка на спам.
    
    Args:
        message: telebot Message
        spam_counter: словарь счётчиков (если None — используем db.spam_counter)
    
    Returns:
        bool: True если это спам
    """
    if spam_counter is None:
        spam_counter = db.spam_counter
    
    user_id = message.from_user.id
    content = message.text or ""
    
    # Если стикер — используем его file_unique_id
    if hasattr(message, "sticker") and message.sticker:
        content = message.sticker.file_unique_id
    
    # Если голосовое — используем file_id
    if hasattr(message, "voice") and message.voice:
        content = message.voice.file_id
    
    now = datetime.now()
    
    # Первое сообщение от пользователя
    if user_id not in spam_counter:
        spam_counter[user_id] = {
            "count": 1,
            "last_content": content,
            "last_time": now,
        }
        return False
    
    last = spam_counter[user_id]
    
    # Если прошло больше 30 секунд — сбрасываем
    if (now - last["last_time"]).seconds > 30:
        spam_counter[user_id] = {
            "count": 1,
            "last_content": content,
            "last_time": now,
        }
        return False
    
    # Если контент тот же — увеличиваем счётчик
    if content == last["last_content"]:
        last["count"] += 1
        last["last_time"] = now
        
        # Порог для стикеров/голосовых — 3, для текста — 5
        if hasattr(message, "sticker") and message.sticker:
            return last["count"] >= 3
        if hasattr(message, "voice") and message.voice:
            return last["count"] >= 3
        return last["count"] >= 5
    else:
        # Другой контент — сбрасываем
        spam_counter[user_id] = {
            "count": 1,
            "last_content": content,
            "last_time": now,
        }
    
    return False

# ============================================================
# 4. ПРОВЕРКА РЕЙДЕРОВ
# ============================================================

def check_raid_markers(text, username=None):
    """
    Проверка на рейдерские метки.
    
    Returns:
        tuple: (is_raid, marker)
    """
    if not text and not username:
        return False, None
    
    text_lower = (text or "").lower()
    username_lower = (username or "").lower()
    
    for marker in RAID_MARKERS:
        marker_lower = marker.lower()
        if marker_lower in text_lower:
            return True, marker
        if marker_lower in username_lower:
            return True, marker
    
    return False, None

# ============================================================
# 5. ПРОВЕРКА ОСКОРБЛЕНИЙ
# ============================================================

def check_insults(text):
    """
    Проверка на оскорбления.
    
    Returns:
        tuple: (has_insult, insult)
    """
    if not text:
        return False, None
    
    text_lower = text.lower()
    
    for insult in INSULTS:
        # Проверка с учётом границ слова
        pattern = r'\b' + re.escape(insult) + r'\b'
        if re.search(pattern, text_lower):
            return True, insult
    
    return False, None

# ============================================================
# 6. ПРОВЕРКА ССЫЛОК
# ============================================================

def check_links(text):
    """
    Проверить наличие ссылок.
    
    Returns:
        list: список ссылок
    """
    if not text:
        return []
    
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
    return urls

def is_suspicious_link(url):
    """Проверить, подозрительная ли ссылка"""
    suspicious_domains = [
        "bit.ly", "tinyurl.com", "goo.gl", "t.co",
        "shorturl.at", "cutt.ly", "is.gd",
    ]
    url_lower = url.lower()
    return any(d in url_lower for d in suspicious_domains)

# ============================================================
# 7. КАПС
# ============================================================

def is_caps_spam(text, threshold=0.7):
    """
    Проверить, написан ли текст капсом.
    
    Returns:
        bool
    """
    if not text:
        return False
    
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 5:
        return False
    
    caps_count = sum(1 for c in letters if c.isupper())
    ratio = caps_count / len(letters)
    
    return ratio > threshold

# ============================================================
# 8. ОСНОВНАЯ ФУНКЦИЯ МОДЕРАЦИИ
# ============================================================

def check_moderation(message, bot, is_admin_or_owner_func=None, is_owner_func=None):
    """
    Полная модерация сообщения.
    
    Args:
        message: telebot Message
        bot: telebot instance
        is_admin_or_owner_func: функция проверки админа (опционально)
        is_owner_func: функция проверки владельца (опционально)
    
    Returns:
        dict: {action, reason, muted, banned, warned}
    """
    result = {
        "action": "none",
        "reason": None,
        "muted": False,
        "banned": False,
        "warned": False,
    }
    
    user = message.from_user
    chat_id = message.chat.id
    text = message.text or ""
    
    # Пропускаем владельцев и помощников
    if user.id in OWNER_IDS or user.id in HELPER_IDS:
        return result
    
    # Пропускаем админов чата
    is_admin = False
    if is_admin_or_owner_func:
        try:
            is_admin = is_admin_or_owner_func(chat_id, user.id)
        except Exception:
            pass
    
    if is_admin:
        return result
    
    # ============================================================
    # 8.1 ПРОВЕРКА СПАМА
    # ============================================================
    
    if check_spam(message):
        until = datetime.now() + timedelta(minutes=SPAM_MUTE_MINUTES)
        
        try:
            bot.restrict_chat_member(
                chat_id,
                user.id,
                until_date=until,
                can_send_messages=False,
            )
            bot.reply_to(
                message,
                f"{user.first_name}, мут на {SPAM_MUTE_MINUTES} минут за спам"
            )
            result["action"] = "mute"
            result["reason"] = "спам"
            result["muted"] = True
            return result
        except Exception as e:
            print(f"⚠️ Не удалось замутить {user.id}: {e}")
    
    # ============================================================
    # 8.2 ПРОВЕРКА РЕЙДЕРОВ
    # ============================================================
    
    is_raid, raid_marker = check_raid_markers(text, user.username)
    if is_raid:
        # Уведомляем админов
        try:
            admins = bot.get_chat_administrators(chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    try:
                        bot.send_message(
                            admin.user.id,
                            f"⚠️ Рейдер обнаружен!\n"
                            f"Пользователь: {user.first_name} (@{user.username})\n"
                            f"Метка: {raid_marker}\n"
                            f"Чат: {message.chat.title}"
                        )
                    except Exception:
                        pass
        except Exception:
            pass
        
        result["action"] = "alert"
        result["reason"] = f"рейдер (метка: {raid_marker})"
        return result
    
    # ============================================================
    # 8.3 ПРОВЕРКА КАПСА
    # ============================================================
    
    if is_caps_spam(text) and len(text) > 20:
        try:
            bot.reply_to(message, f"{user.first_name}, не капси!")
            result["action"] = "warn_caps"
            result["reason"] = "капс"
            return result
        except Exception:
            pass
    
    # ============================================================
    # 8.4 ПРОВЕРКА ОСКОРБЛЕНИЙ
    # ============================================================
    
    has_insult, insult = check_insults(text)
    if has_insult:
        # Проверяем цензуру
        censorship_level = db.censorship_levels.get(chat_id, 2)
        
        # Уровень 1 = строгий (любой мат наказуем)
        # Уровень 2 = обычный (мат допустим, но оскорбления нет)
        # Уровень 3 = свободный (всё можно)
        
        if censorship_level == 1:
            try:
                bot.delete_message(chat_id, message.message_id)
                bot.reply_to(message, f"{user.first_name}, мат запрещён (цензура 1)")
                result["action"] = "delete"
                result["reason"] = f"оскорбление: {insult}"
                return result
            except Exception:
                pass
    
    # ============================================================
    # 8.5 ПРОВЕРКА ССЫЛОК
    # ============================================================
    
    links = check_links(text)
    if links:
        for link in links:
            if is_suspicious_link(link):
                try:
                    bot.delete_message(chat_id, message.message_id)
                    bot.reply_to(
                        message,
                        f"{user.first_name}, подозрительная ссылка удалена"
                    )
                    result["action"] = "delete"
                    result["reason"] = f"подозрительная ссылка: {link}"
                    return result
                except Exception:
                    pass
    
    return result

# ============================================================
# 9. РУЧНЫЕ НАКАЗАНИЯ
# ============================================================

def mute_user(bot, chat_id, user_id, duration_minutes, reason="Нарушение правил"):
    """Выдать мут"""
    try:
        until = datetime.now() + timedelta(minutes=duration_minutes)
        bot.restrict_chat_member(
            chat_id,
            user_id,
            until_date=until,
            can_send_messages=False,
        )
        
        # Записываем в БД
        db.muted_users[user_id] = {
            "until": until,
            "reason": reason,
            "by": "Систмка",
            "chat_id": chat_id,
        }
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка мьюта: {e}")
        return False

def unmute_user(bot, chat_id, user_id):
    """Снять мут"""
    try:
        bot.restrict_chat_member(
            chat_id,
            user_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        
        if user_id in db.muted_users:
            del db.muted_users[user_id]
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка размьюта: {e}")
        return False

def ban_user(bot, chat_id, user_id, reason="Нарушение правил"):
    """Забанить"""
    try:
        bot.ban_chat_member(chat_id, user_id)
        
        db.banned_users[user_id] = {
            "reason": reason,
            "by": "Систмка",
            "chat_id": chat_id,
            "time": datetime.now().isoformat(),
        }
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка бана: {e}")
        return False

def unban_user(bot, chat_id, user_id):
    """Разбанить"""
    try:
        bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        
        if user_id in db.banned_users:
            del db.banned_users[user_id]
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка разбана: {e}")
        return False

def warn_user(bot, chat_id, user_id, reason="Нарушение правил"):
    """
    Выдать варн.
    
    3 варна = мут навсегда.
    """
    try:
        if user_id not in db.warned_users:
            db.warned_users[user_id] = {
                "count": 0,
                "history": [],
                "chat_id": chat_id,
            }
        
        db.warned_users[user_id]["count"] += 1
        db.warned_users[user_id]["history"].append({
            "reason": reason,
            "by": "Систмка",
            "time": datetime.now().isoformat(),
        })
        
        count = db.warned_users[user_id]["count"]
        
        # 3 варна → мут навсегда
        if count >= 3:
            until = datetime.now() + timedelta(days=365)
            bot.restrict_chat_member(
                chat_id,
                user_id,
                until_date=until,
                can_send_messages=False,
            )
            bot.send_message(
                chat_id,
                f"🔨 Пользователь получил мут навсегда за 3 варна!"
            )
        else:
            bot.send_message(
                chat_id,
                f"⚠️ Варн ({count}/3) за: {reason}"
            )
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка варна: {e}")
        return False

# ============================================================
# 10. АВТОМАТИЧЕСКОЕ СНЯТИЕ МУТОВ
# ============================================================

def check_expired_mutes(bot):
    """
    Проверить истёкшие мьюты.
    
    Returns:
        list: список user_id, с которых снят мут
    """
    expired = []
    now = datetime.now()
    
    for user_id in list(db.muted_users.keys()):
        mute = db.muted_users[user_id]
        until = mute.get("until")
        
        if isinstance(until, str):
            try:
                until = datetime.fromisoformat(until)
            except ValueError:
                until = None
        
        if until and now >= until:
            chat_id = mute.get("chat_id")
            if chat_id:
                if unmute_user(bot, chat_id, user_id):
                    expired.append(user_id)
            else:
                # Не знаем чат — просто удаляем
                del db.muted_users[user_id]
                expired.append(user_id)
    
    return expired

# ============================================================
# 11. СТАТИСТИКА МОДЕРАЦИИ
# ============================================================

def get_moderation_stats():
    """Получить статистику модерации"""
    return {
        "muted": len(db.muted_users),
        "banned": len(db.banned_users),
        "warned": len(db.warned_users),
    }

def format_moderation_stats():
    """Форматировать статистику"""
    stats = get_moderation_stats()
    return (
        f"🛡️ МОДЕРАЦИЯ:\n"
        f"  🔇 В муте: {stats['muted']}\n"
        f"  🚫 В бане: {stats['banned']}\n"
        f"  ⚠️ С варнами: {stats['warned']}"
    )

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("🛡️ Модуль модерации загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")
print(f"🚫 Маркеров рейдеров: {len(RAID_MARKERS)}")
print(f"🤬 Оскорблений в списке: {len(INSULTS)}")