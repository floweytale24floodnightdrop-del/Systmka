"""История сообщений"""

from datetime import datetime
import database as db

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MAX_HISTORY_PER_CHAT = 200
MAX_USER_HISTORY = 100

# ============================================================
# 2. СОХРАНЕНИЕ СООБЩЕНИЯ
# ============================================================

def save_message(chat_id, user_id, user_name, text, chat_type):
    """
    Сохранить сообщение в историю.
    
    Args:
        chat_id: ID чата
        user_id: ID пользователя
        user_name: имя пользователя
        text: текст сообщения
        chat_type: тип чата
    
    Returns:
        bool: успех
    """
    if not chat_id or not user_id:
        return False
    
    if chat_id not in db.history:
        db.history[chat_id] = []
    
    db.history[chat_id].append({
        "user_id": user_id,
        "user_name": user_name or "?",
        "text": text or "",
        "time": datetime.now().strftime("%H:%M:%S"),
        "chat_type": chat_type or "unknown",
    })
    
    # Ограничиваем историю
    if len(db.history[chat_id]) > MAX_HISTORY_PER_CHAT:
        db.history[chat_id] = db.history[chat_id][-MAX_HISTORY_PER_CHAT:]
    
    return True

# ============================================================
# 3. ПОЛУЧЕНИЕ ИСТОРИИ
# ============================================================

def get_chat_history(chat_id, limit=50):
    """
    Получить историю чата.
    
    Returns:
        list
    """
    if not chat_id or limit <= 0:
        return []
    
    if chat_id in db.history:
        return db.history[chat_id][-limit:]
    
    return []


def get_user_history(user_id, limit=100):
    """
    Получить историю пользователя.
    
    Returns:
        list
    """
    if not user_id or limit <= 0:
        return []
    
    user_messages = []
    
    for chat_id, messages in db.history.items():
        for msg in messages:
            if msg.get("user_id") == user_id:
                user_messages.append(msg)
    
    return user_messages[-limit:]

# ============================================================
# 4. ОЧИСТКА
# ============================================================

def clear_chat_history(chat_id):
    """
    Очистить историю чата.
    
    Returns:
        bool: успех
    """
    if chat_id in db.history:
        db.history[chat_id] = []
        return True
    return False


def clear_all_history():
    """Очистить всю историю"""
    db.history = {}
    return True

# ============================================================
# 5. СТАТИСТИКА
# ============================================================

def get_history_stats():
    """
    Получить статистику истории.
    
    Returns:
        dict
    """
    total_messages = sum(len(h) for h in db.history.values())
    total_chats = len(db.history)
    
    return {
        "total_messages": total_messages,
        "total_chats": total_chats,
        "max_per_chat": MAX_HISTORY_PER_CHAT,
    }

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_history(messages):
    """
    Форматировать историю для вывода.
    
    Returns:
        str
    """
    if not messages:
        return "История пуста"
    
    result = ""
    
    for msg in messages:
        time = msg.get("time", "?")
        name = msg.get("user_name", "?")
        text = msg.get("text", "")
        
        # Обрезаем длинный текст
        if len(text) > 100:
            text = text[:100] + "..."
        
        result += f"[{time}] {name}: {text}\n"
    
    return result


def format_history_stats():
    """Форматировать статистику истории"""
    stats = get_history_stats()
    
    lines = [
        "📜 СТАТИСТИКА ИСТОРИИ:",
        f"  💬 Сообщений: {stats['total_messages']}",
        f"  💬 Чатов: {stats['total_chats']}",
        f"  📊 Макс. на чат: {stats['max_per_chat']}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📜 Модуль истории загружен (PC)")
print(f"💬 Чатов: {len(db.history)}")
print(f"💬 Сообщений: {sum(len(h) for h in db.history.values())}")