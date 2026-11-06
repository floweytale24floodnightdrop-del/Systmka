"""Управление профилем пользователя — ник, описание, теги, местоимения"""

import database as db

# ============================================================
# 1. ОБНОВЛЕНИЕ ПРОФИЛЯ
# ============================================================

def update_nickname(user_id, new_nickname):
    """
    Изменить ник в профиле.
    
    Args:
        user_id: ID пользователя
        new_nickname: новый ник
    
    Returns:
        bool: успех
    """
    if not user_id or not new_nickname:
        return False
    
    # Обрезаем длину
    new_nickname = str(new_nickname).strip()[:32]
    
    if not new_nickname:
        return False
    
    if user_id not in db.user_profiles:
        db.user_profiles[user_id] = {}
    
    db.user_profiles[user_id]["custom_nickname"] = new_nickname
    return True


def update_description(user_id, new_description):
    """
    Изменить описание.
    
    Args:
        user_id: ID пользователя
        new_description: новое описание
    
    Returns:
        bool: успех
    """
    if not user_id:
        return False
    
    if new_description is None:
        new_description = ""
    
    # Обрезаем длину
    new_description = str(new_description).strip()[:500]
    
    if user_id not in db.user_profiles:
        db.user_profiles[user_id] = {}
    
    db.user_profiles[user_id]["description"] = new_description
    return True


def update_tags(user_id, tags):
    """
    Изменить теги.
    
    Args:
        user_id: ID пользователя
        tags: список тегов или строка с разделителем ","
    
    Returns:
        bool: успех
    """
    if not user_id:
        return False
    
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, list):
        tags = [str(t).strip() for t in tags if t]
    else:
        tags = []
    
    # Ограничиваем количество и длину
    tags = [t[:32] for t in tags[:10]]
    
    if user_id not in db.user_profiles:
        db.user_profiles[user_id] = {}
    
    db.user_profiles[user_id]["tags"] = tags
    return True


def update_pronouns(user_id, pronouns):
    """
    Изменить местоимения.
    
    Args:
        user_id: ID пользователя
        pronouns: местоимения (например, "он/его")
    
    Returns:
        bool: успех
    """
    if not user_id:
        return False
    
    if pronouns is None:
        pronouns = ""
    
    pronouns = str(pronouns).strip()[:32]
    
    if user_id not in db.user_profiles:
        db.user_profiles[user_id] = {}
    
    db.user_profiles[user_id]["pronouns"] = pronouns
    return True

# ============================================================
# 2. ПОЛУЧЕНИЕ ПРОФИЛЯ
# ============================================================

def get_profile_info(user_id):
    """
    Получить полную информацию профиля.
    
    Args:
        user_id: ID пользователя
    
    Returns:
        dict: {nickname, description, tags, pronouns}
    """
    if not user_id:
        return {
            "nickname": "Неизвестно",
            "description": "",
            "tags": [],
            "pronouns": "",
        }
    
    profile = db.user_profiles.get(user_id, {})
    
    return {
        "nickname": profile.get(
            "custom_nickname",
            profile.get("first_name", "Неизвестно"),
        ),
        "description": profile.get("description", ""),
        "tags": profile.get("tags", []),
        "pronouns": profile.get("pronouns", ""),
    }


def format_profile_info(user_id):
    """
    Форматировать профиль для вывода.
    
    Returns:
        str
    """
    info = get_profile_info(user_id)
    
    lines = [f"👤 {info['nickname']}"]
    
    if info["pronouns"]:
        lines.append(f"  🗣 {info['pronouns']}")
    
    if info["description"]:
        lines.append(f"  📝 {info['description']}")
    
    if info["tags"]:
        lines.append(f"  🏷 {', '.join(info['tags'])}")
    
    return "\n".join(lines)


def has_custom_profile(user_id):
    """Проверить, есть ли у пользователя кастомный профиль"""
    if not user_id or user_id not in db.user_profiles:
        return False
    
    profile = db.user_profiles[user_id]
    return bool(
        profile.get("custom_nickname")
        or profile.get("description")
        or profile.get("tags")
    )


def reset_profile(user_id):
    """Сбросить кастомные данные профиля"""
    if not user_id or user_id not in db.user_profiles:
        return False
    
    profile = db.user_profiles[user_id]
    
    for key in ("custom_nickname", "description", "tags", "pronouns"):
        if key in profile:
            del profile[key]
    
    return True

# ============================================================
# 3. ЗАГРУЗКА
# ============================================================

print("👤 Модуль профиля загружен (PC)")