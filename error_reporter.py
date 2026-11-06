"""Уведомления об ошибках владельцу"""

import os
import json
import traceback
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

ERROR_NOTIFICATIONS_FILE = "error_notifications.json"
MAX_NOTIFICATIONS = 200

# ============================================================
# 2. ДАННЫЕ
# ============================================================

error_notifications = []

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_notifications():
    """Сохранить уведомления"""
    try:
        with open(ERROR_NOTIFICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(error_notifications, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения уведомлений: {e}")
        return False


def load_notifications():
    """Загрузить уведомления"""
    global error_notifications
    try:
        if os.path.exists(ERROR_NOTIFICATIONS_FILE):
            with open(ERROR_NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    error_notifications = loaded
        return error_notifications
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON уведомлений: {e}")
        error_notifications = []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки уведомлений: {e}")
        error_notifications = []
    return error_notifications

# ============================================================
# 4. УВЕДОМЛЕНИЕ ОБ ОШИБКЕ
# ============================================================

def notify_error(bot, owner_ids, error, chat_id=None, user=None, request_text=None):
    """
    Уведомить владельцев об ошибке.
    
    Args:
        bot: telebot instance
        owner_ids: список ID владельцев
        error: объект ошибки (Exception)
        chat_id: ID чата (опционально)
        user: имя пользователя (опционально)
        request_text: текст запроса (опционально)
    
    Returns:
        bool: успех
    """
    if not bot or not owner_ids or error is None:
        return False
    
    try:
        error_info = {
            "error": str(error)[:500],
            "type": error.__class__.__name__,
            "chat_id": chat_id,
            "user": user,
            "request": (request_text[:200] if request_text else None),
            "trace": traceback.format_exc()[:2000],
            "time": datetime.now().isoformat(),
        }
        
        # Формируем сообщение
        message_text = f"❌ ОШИБКА!\n\n"
        message_text += f"Тип: {error_info['type']}\n"
        message_text += f"Ошибка: {error_info['error'][:200]}\n"
        
        if chat_id:
            message_text += f"Чат: {chat_id}\n"
        if user:
            message_text += f"Пользователь: {user}\n"
        if request_text:
            message_text += f"Запрос: {request_text[:100]}\n"
        
        message_text += f"Время: {datetime.now().strftime('%H:%M:%S')}"
        
        # Отправляем владельцам
        sent_count = 0
        for oid in owner_ids:
            try:
                bot.send_message(oid, message_text)
                sent_count += 1
            except Exception as e:
                print(f"⚠️ Не смогла отправить {oid}: {str(e)[:80]}")
        
        # Сохраняем в историю
        error_notifications.append(error_info)
        
        if len(error_notifications) > MAX_NOTIFICATIONS:
            error_notifications = error_notifications[-MAX_NOTIFICATIONS:]
        
        save_notifications()
        
        return sent_count > 0
    except Exception as e:
        print(f"⚠️ Ошибка в notify_error: {e}")
        return False

# ============================================================
# 5. СТАТИСТИКА
# ============================================================

def get_error_stats():
    """Получить статистику ошибок"""
    if not error_notifications:
        return {
            "total": 0,
            "last_error": None,
            "by_type": {},
        }
    
    # Считаем по типам
    by_type = {}
    for err in error_notifications:
        error_type = err.get("type", "Unknown")
        by_type[error_type] = by_type.get(error_type, 0) + 1
    
    return {
        "total": len(error_notifications),
        "last_error": error_notifications[-1],
        "by_type": by_type,
    }


def format_error_stats():
    """Форматировать статистику ошибок"""
    stats = get_error_stats()
    
    lines = [
        "❌ СТАТИСТИКА ОШИБОК:",
        f"  📊 Всего: {stats['total']}",
    ]
    
    if stats["by_type"]:
        lines.append("")
        lines.append("  📋 ПО ТИПАМ:")
        for error_type, count in sorted(
            stats["by_type"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            lines.append(f"    • {error_type}: {count}")
    
    if stats["last_error"]:
        lines.append("")
        lines.append(
            f"  🕐 Последняя: "
            f"{stats['last_error'].get('time', '?')[:16]}"
        )
    
    return "\n".join(lines)


def clear_notifications():
    """Очистить историю уведомлений"""
    global error_notifications
    error_notifications = []
    save_notifications()
    return True

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

load_notifications()

print("❌ Модуль уведомлений загружен (PC)")
print(f"📊 Уведомлений в истории: {len(error_notifications)}")