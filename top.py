"""Топ игроков — по глитчам, сообщениям, комбо"""

import database as db

# ============================================================
# 1. ТОП ПО ГЛИТЧАМ
# ============================================================

def get_top_players(limit=10, owner_ids=None):
    """
    Получить топ игроков по глитчам.
    
    Args:
        limit: сколько игроков
        owner_ids: ID владельцев (исключаются)
    
    Returns:
        list: [{user_id, name, username, glitches}, ...]
    """
    if limit <= 0:
        return []
    
    if owner_ids is None:
        try:
            from config import OWNER_IDS
            owner_ids = OWNER_IDS
        except Exception:
            owner_ids = []
    
    # Фильтруем владельцев (у них бесконечность)
    filtered = {
        uid: g for uid, g in db.user_glitches.items()
        if uid not in owner_ids
    }
    
    sorted_users = sorted(
        filtered.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    
    top = []
    for uid, glitches in sorted_users[:limit]:
        profile = db.user_profiles.get(uid, {})
        top.append({
            "user_id": uid,
            "name": profile.get("first_name", "?"),
            "username": profile.get("username", ""),
            "glitches": glitches,
        })
    
    return top

# ============================================================
# 2. ТОП ПО СООБЩЕНИЯМ
# ============================================================

def get_top_by_messages(limit=10):
    """
    Топ по сообщениям.
    
    Returns:
        list: [{user_id, name, username, messages}, ...]
    """
    if limit <= 0:
        return []
    
    sorted_users = sorted(
        db.user_profiles.items(),
        key=lambda x: x[1].get("messages", 0),
        reverse=True,
    )
    
    top = []
    for uid, profile in sorted_users[:limit]:
        if profile.get("is_bot", False):
            continue
        
        top.append({
            "user_id": uid,
            "name": profile.get("first_name", "?"),
            "username": profile.get("username", ""),
            "messages": profile.get("messages", 0),
        })
    
    return top

# ============================================================
# 3. ТОП ПО КОМБО
# ============================================================

def get_top_by_combo(limit=10):
    """
    Топ по комбо.
    
    Returns:
        list: [{user_id, name, username, combo}, ...]
    """
    if limit <= 0:
        return []
    
    sorted_users = sorted(
        db.user_combo.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    
    top = []
    for uid, combo in sorted_users[:limit]:
        profile = db.user_profiles.get(uid, {})
        top.append({
            "user_id": uid,
            "name": profile.get("first_name", "?"),
            "username": profile.get("username", ""),
            "combo": combo,
        })
    
    return top

# ============================================================
# 4. ФОРМАТИРОВАНИЕ
# ============================================================

def format_top(top_list, value_key="glitches", value_icon="👾"):
    """
    Форматировать топ.
    
    Returns:
        str
    """
    if not top_list:
        return "🏆 Пока нет игроков"
    
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 ТОП ИГРОКОВ:", ""]
    
    for i, item in enumerate(top_list, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = item.get("name", "?")
        username = item.get("username", "")
        
        if username and not username.startswith("@"):
            username = f" @{username}"
        
        value = item.get(value_key, 0)
        
        lines.append(f"{medal} {name}{username} — {value}{value_icon}")
    
    return "\n".join(lines)


def format_top_glitches(top_list):
    """Форматировать топ по глитчам"""
    return format_top(top_list, "glitches", "👾")


def format_top_messages(top_list):
    """Форматировать топ по сообщениям"""
    return format_top(top_list, "messages", "💬")


def format_top_combo(top_list):
    """Форматировать топ по комбо"""
    return format_top(top_list, "combo", "💜")

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("🏆 Модуль топа загружен (PC)")
print(f"👥 Пользователей в БД: {len(db.user_profiles)}")