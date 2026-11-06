"""Система премиума — 4 уровня + владелец + помощник"""

import os
import json
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, HELPER_IDS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

PREMIUM_FILE = "premium_data.json"

# Уровни премиума
PREMIUM_LEVELS = {
    "none": {
        "name": "🫶 Обычный",
        "level": 0,
        "can_chat_ls": False,
        "can_chat_group": True,
        "need_ftf24": True,
        "commission": 0.30,
        "transfers_per_week": 0,
        "gift_multiplier": 1.0,
        "casino_bonus": 0.0,
        "battle_bonus": 0.0,
        "trojan_chance": 0.0,
        "trojan_bonus": 0.0,
        "rp_commands_limit": 1,
        "can_generate_images": False,
        "can_get_glitches": False,
        "can_use_premium_commands": False,
        "priority": 0,
        "weekly_glitches": 0,
        "can_view_status": False,
    },
    "premka": {
        "name": "✨ Премка",
        "level": 1,
        "can_chat_ls": False,
        "can_chat_group": True,
        "need_ftf24": True,
        "commission": 0.30,
        "transfers_per_week": 2,
        "gift_multiplier": 1.25,
        "casino_bonus": 0.05,
        "battle_bonus": 0.3,
        "trojan_chance": 0.0,
        "trojan_bonus": 0.0,
        "rp_commands_limit": 3,
        "can_generate_images": False,
        "can_get_glitches": False,
        "can_use_premium_commands": False,
        "priority": 1,
        "weekly_glitches": 0,
        "can_view_status": False,
    },
    "premium": {
        "name": "⭐️ Премиум",
        "level": 2,
        "can_chat_ls": True,
        "can_chat_group": True,
        "need_ftf24": False,
        "commission": 0.10,
        "transfers_per_week": -1,
        "gift_multiplier": 2.0,
        "casino_bonus": 0.10,
        "battle_bonus": 0.5,
        "trojan_chance": 0.05,
        "trojan_bonus": 0.20,
        "rp_commands_limit": 5,
        "can_generate_images": True,
        "can_get_glitches": True,
        "can_use_premium_commands": True,
        "priority": 2,
        "weekly_glitches": 0,
        "can_view_status": False,
    },
    "premium_plus": {
        "name": "🌟 ПРЕМИУМ",
        "level": 3,
        "can_chat_ls": True,
        "can_chat_group": True,
        "need_ftf24": False,
        "commission": 0.0,
        "transfers_per_week": -1,
        "gift_multiplier": 3.0,
        "casino_bonus": 0.10,
        "battle_bonus": 1.0,
        "trojan_chance": 0.10,
        "trojan_bonus": 0.30,
        "rp_commands_limit": 10,
        "can_generate_images": True,
        "can_get_glitches": True,
        "can_use_premium_commands": True,
        "priority": 3,
        "weekly_glitches": 0,
        "can_view_status": False,
    },
    "owner": {
        "name": "👾 ФТФлауи",
        "level": 99,
        "can_chat_ls": True,
        "can_chat_group": True,
        "need_ftf24": False,
        "commission": 0.0,
        "transfers_per_week": -1,
        "gift_multiplier": 999.0,
        "casino_bonus": 0.50,
        "battle_bonus": 5.0,
        "trojan_chance": 0.50,
        "trojan_bonus": 1.0,
        "rp_commands_limit": -1,
        "can_generate_images": True,
        "can_get_glitches": True,
        "can_use_premium_commands": True,
        "priority": 99,
        "weekly_glitches": 0,
        "can_view_status": True,
    },
    "helper": {
        "name": "💫 ПОМОЩНИК",
        "level": 10,
        "can_chat_ls": True,
        "can_chat_group": True,
        "need_ftf24": False,
        "commission": 0.0,
        "transfers_per_week": -1,
        "gift_multiplier": 3.0,
        "casino_bonus": 0.10,
        "battle_bonus": 1.0,
        "trojan_chance": 0.10,
        "trojan_bonus": 0.30,
        "rp_commands_limit": 10,
        "can_generate_images": True,
        "can_get_glitches": True,
        "can_use_premium_commands": True,
        "priority": 3,
        "weekly_glitches": 10,
        "can_view_status": True,
    },
}

# ============================================================
# 3. ДАННЫЕ
# ============================================================

user_premium = {}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_premium_data():
    """Сохранить данные премиума"""
    try:
        data = {}
        for uid, info in user_premium.items():
            data[str(uid)] = {
                "level": info.get("level", "none"),
                "expires": info.get("expires"),
                "transfers_used": info.get("transfers_used", 0),
                "last_transfer_reset": info.get("last_transfer_reset"),
            }
        with open(PREMIUM_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения премиума: {e}")
        return False


def load_premium_data():
    """Загрузить данные премиума"""
    global user_premium
    try:
        if os.path.exists(PREMIUM_FILE):
            with open(PREMIUM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                for uid_str, info in data.items():
                    try:
                        uid = int(uid_str)
                    except (ValueError, TypeError):
                        continue
                    
                    if isinstance(info, dict):
                        user_premium[uid] = info
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON премиума: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки премиума: {e}")
        return False


load_premium_data()

# ============================================================
# 5. УРОВЕНЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_user_level(user_id):
    """
    Получить уровень премиума пользователя.
    
    Returns:
        str: "owner", "helper", "premka", "premium",
             "premium_plus" или "none"
    """
    if not user_id:
        return "none"
    
    if user_id in OWNER_IDS:
        return "owner"
    
    if user_id in HELPER_IDS:
        return "helper"
    
    if user_id not in user_premium:
        return "none"
    
    data = user_premium[user_id]
    level = data.get("level", "none")
    
    # Проверяем истечение
    if level != "none":
        expires = data.get("expires")
        
        if expires:
            if isinstance(expires, str):
                try:
                    expires = datetime.fromisoformat(expires)
                except (ValueError, TypeError):
                    return "none"
            
            if isinstance(expires, datetime) and datetime.now() > expires:
                user_premium[user_id]["level"] = "none"
                save_premium_data()
                return "none"
    
    return level


def get_premium_config(user_id):
    """Получить конфигурацию премиума для пользователя"""
    level = get_user_level(user_id)
    return PREMIUM_LEVELS.get(level, PREMIUM_LEVELS["none"])


def check_premium(user_id, owner_ids=None):
    """
    Проверить, есть ли у пользователя премиум.
    
    Args:
        user_id: ID пользователя
        owner_ids: (устаревший параметр, игнорируется)
    
    Returns:
        bool
    """
    return get_user_level(user_id) != "none"


def get_premium_level(user_id):
    """Получить название уровня"""
    return get_premium_config(user_id)["name"]


def get_premium_level_icon(user_id):
    """Получить иконку уровня"""
    name = get_premium_config(user_id)["name"]
    return name[0] if name else "🫶"


def is_owner(user_id):
    """Проверить, владелец ли"""
    return user_id in OWNER_IDS


def is_helper(user_id):
    """Проверить, помощник ли"""
    return user_id in HELPER_IDS

# ============================================================
# 6. ФУНКЦИИ ПРОВЕРКИ ПРАВ
# ============================================================

def can_chat_ls(user_id):
    """Может ли общаться в ЛС"""
    return get_premium_config(user_id)["can_chat_ls"]


def can_chat_group(user_id):
    """Может ли общаться в группах"""
    return get_premium_config(user_id)["can_chat_group"]


def need_ftf24(user_id):
    """Нужна ли приписка #FTF24"""
    return get_premium_config(user_id)["need_ftf24"]


def get_commission(user_id):
    """Комиссия при переводе"""
    return get_premium_config(user_id)["commission"]


def get_transfers_per_week(user_id):
    """Лимит переводов в неделю"""
    return get_premium_config(user_id)["transfers_per_week"]


def get_gift_multiplier(user_id):
    """Множитель подарочка"""
    return get_premium_config(user_id)["gift_multiplier"]


def get_casino_bonus(user_id):
    """Бонус казино"""
    return get_premium_config(user_id)["casino_bonus"]


def get_battle_bonus(user_id):
    """Бонус битвы аков"""
    return get_premium_config(user_id)["battle_bonus"]


def get_trojan_chance(user_id):
    """Шанс особого трояна"""
    return get_premium_config(user_id)["trojan_chance"]


def get_trojan_bonus(user_id):
    """Бонус особого трояна"""
    return get_premium_config(user_id)["trojan_bonus"]


def get_rp_commands_limit(user_id):
    """Лимит РП команд"""
    return get_premium_config(user_id)["rp_commands_limit"]


def can_generate_images(user_id):
    """Может ли генерировать картинки"""
    return get_premium_config(user_id)["can_generate_images"]


def can_get_glitches(user_id):
    """Может ли получать глитчи за актив"""
    return get_premium_config(user_id)["can_get_glitches"]


def can_use_premium_commands(user_id):
    """Может ли использовать премиум команды"""
    return get_premium_config(user_id)["can_use_premium_commands"]


def get_priority(user_id):
    """Приоритет ответов"""
    return get_premium_config(user_id)["priority"]


def get_weekly_glitches(user_id):
    """Бонус глитчей в неделю"""
    return get_premium_config(user_id)["weekly_glitches"]


def can_view_status(user_id):
    """Может ли смотреть статус бота"""
    return get_premium_config(user_id)["can_view_status"]

# ============================================================
# 7. ВЫДАЧА / СНЯТИЕ ПРЕМИУМА
# ============================================================

def set_premium(user_id, level, days=30):
    """
    Выдать премиум определённого уровня.
    
    Args:
        user_id: ID пользователя
        level: "premka", "premium", "premium_plus"
        days: количество дней
    
    Returns:
        bool
    """
    if not user_id or not level:
        return False
    
    if level not in PREMIUM_LEVELS:
        return False
    
    if level in ("owner", "helper", "none"):
        return False
    
    if user_id in OWNER_IDS or user_id in HELPER_IDS:
        return False
    
    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 30
    
    if days <= 0:
        return False
    
    expires = datetime.now() + timedelta(days=days)
    
    user_premium[user_id] = {
        "level": level,
        "expires": expires.isoformat(),
        "transfers_used": 0,
        "last_transfer_reset": datetime.now().isoformat(),
    }
    
    save_premium_data()
    return True


def remove_premium(user_id):
    """Снять премиум"""
    if user_id in user_premium:
        del user_premium[user_id]
        save_premium_data()
        return True
    return False


def extend_premium(user_id, days=30):
    """Продлить премиум"""
    if user_id not in user_premium:
        return False
    
    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 30
    
    if days <= 0:
        return False
    
    data = user_premium[user_id]
    expires = data.get("expires")
    
    if expires and isinstance(expires, str):
        try:
            expires = datetime.fromisoformat(expires)
        except (ValueError, TypeError):
            expires = datetime.now()
    else:
        expires = datetime.now()
    
    base_date = max(expires, datetime.now())
    new_expires = base_date + timedelta(days=days)
    
    user_premium[user_id]["expires"] = new_expires.isoformat()
    save_premium_data()
    return True

# ============================================================
# 8. ТРАНЗАКЦИИ
# ============================================================

def can_transfer(user_id):
    """
    Может ли пользователь переводить глитчи.
    
    Returns:
        tuple: (can_transfer: bool, remaining: int)
    """
    config = get_premium_config(user_id)
    transfers_per_week = config["transfers_per_week"]
    
    # Безлимит
    if transfers_per_week == -1:
        return True, -1
    
    if user_id not in user_premium:
        return False, 0
    
    data = user_premium[user_id]
    
    # Проверяем сброс раз в неделю
    last_reset = data.get("last_transfer_reset")
    if last_reset:
        try:
            last = datetime.fromisoformat(last_reset)
            if (datetime.now() - last).days >= 7:
                data["transfers_used"] = 0
                data["last_transfer_reset"] = datetime.now().isoformat()
                save_premium_data()
        except (ValueError, TypeError):
            pass
    
    used = data.get("transfers_used", 0)
    remaining = transfers_per_week - used
    
    return remaining > 0, max(0, remaining)


def use_transfer(user_id):
    """Использовать перевод"""
    config = get_premium_config(user_id)
    
    if config["transfers_per_week"] == -1:
        return True
    
    if user_id not in user_premium:
        return False
    
    data = user_premium[user_id]
    data["transfers_used"] = data.get("transfers_used", 0) + 1
    save_premium_data()
    return True

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_premium_stats():
    """Получить общую статистику премиума"""
    counts = {level: 0 for level in PREMIUM_LEVELS}
    
    for uid in user_premium:
        level = get_user_level(uid)
        if level in counts:
            counts[level] += 1
    
    return {
        "total": len(user_premium),
        "by_level": counts,
        "owners": len(OWNER_IDS),
        "helpers": len(HELPER_IDS),
    }

# ============================================================
# 10. ФОРМАТИРОВАНИЕ
# ============================================================

def format_premium_status(user_id):
    """Форматировать статус премиума"""
    level = get_user_level(user_id)
    config = PREMIUM_LEVELS.get(level, PREMIUM_LEVELS["none"])
    
    lines = [
        f"💎 СТАТУС ПРЕМИУМА:",
        f"👤 Уровень: {config['name']}",
    ]
    
    # === Обычный ===
    if level == "none":
        lines.append("")
        lines.append("📝 У тебя нет премиума")
        lines.append("💡 Напиши Флауи для получения")
        return "\n".join(lines)
    
    # === Владелец ===
    if level == "owner":
        lines.append("")
        lines.append("👑 Ты создатель Систмки!")
        lines.append("✨ У тебя есть ВСЕ возможности")
        return "\n".join(lines)
    
    # === Помощник ===
    if level == "helper":
        lines.append("")
        lines.append("💫 Ты помощник Флауи!")
        lines.append("🌟 У тебя почти все возможности")
        return "\n".join(lines)
    
    # === Обычный премиум ===
    expires = user_premium.get(user_id, {}).get("expires")
    if expires:
        try:
            expires_dt = datetime.fromisoformat(expires)
            days_left = (expires_dt - datetime.now()).days
            if days_left >= 0:
                lines.append(f"📅 Истекает через: {days_left} дней")
        except (ValueError, TypeError):
            pass
    
    lines.append("")
    lines.append("📋 ТВОИ ПРИВИЛЕГИИ:")
    lines.append(
        f"  💬 Общение в ЛС: "
        f"{'✅' if config['can_chat_ls'] else '❌'}"
    )
    lines.append(
        f"  💬 Общение в группах: "
        f"{'✅' if config['can_chat_group'] else '❌'}"
    )
    lines.append(
        f"  🔑 Приписка #FTF24: "
        f"{'❌' if config['need_ftf24'] else '✅'}"
    )
    lines.append(f"  💰 Комиссия: {int(config['commission'] * 100)}%")
    
    transfers = config["transfers_per_week"]
    if transfers == -1:
        lines.append("  💸 Переводов: ♾️")
    else:
        can, remaining = can_transfer(user_id)
        lines.append(f"  💸 Переводов: {remaining}/{transfers} в неделю")
    
    lines.append(f"  🎁 Подарочек: x{config['gift_multiplier']}")
    lines.append(f"  🎰 Казино: +{int(config['casino_bonus'] * 100)}%")
    lines.append(f"  ⚔️ Битва аков: +{config['battle_bonus']}")
    
    if config["trojan_chance"] > 0:
        lines.append(
            f"  🦠 Троян: +{int(config['trojan_chance'] * 100)}% особый"
        )
        lines.append(
            f"  🦠 Троян бонус: "
            f"+{int(config['trojan_bonus'] * 100)}%"
        )
    
    rp_limit = config["rp_commands_limit"]
    lines.append(
        f"  🎭 РП команд: {'♾️' if rp_limit == -1 else rp_limit}"
    )
    lines.append(
        f"  🎨 Создание картинок: "
        f"{'✅' if config['can_generate_images'] else '❌'}"
    )
    lines.append(
        f"  ⭐ Глитчи за актив: "
        f"{'✅' if config['can_get_glitches'] else '❌'}"
    )
    lines.append(
        f"  💎 Премиум команды: "
        f"{'✅' if config['can_use_premium_commands'] else '❌'}"
    )
    
    if config["weekly_glitches"] > 0:
        lines.append(
            f"  📦 Бонус в неделю: +{config['weekly_glitches']}👾"
        )
    
    return "\n".join(lines)


def format_premium_stats():
    """Форматировать общую статистику"""
    stats = get_premium_stats()
    
    lines = ["📊 СТАТИСТИКА ПРЕМИУМА:"]
    
    for level, count in stats["by_level"].items():
        if count > 0:
            name = PREMIUM_LEVELS[level]["name"]
            lines.append(f"  {name}: {count}")
    
    lines.append("")
    lines.append(f"👑 Владельцев: {stats['owners']}")
    lines.append(f"💫 Помощников: {stats['helpers']}")
    lines.append(f"💎 Всего премиум: {stats['total']}")
    
    return "\n".join(lines)

# ============================================================
# 11. ОБРАТНАЯ СОВМЕСТИМОСТЬ
# ============================================================

# Экспорт для старых вызовов
def get_premium_level_name(user_id):
    """Алиас для get_premium_level"""
    return get_premium_level(user_id)


def has_premium(user_id):
    """Алиас для check_premium"""
    return check_premium(user_id)


def get_user_premium(user_id):
    """Получить данные премиума пользователя"""
    return user_premium.get(user_id)

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("💎 Система премиума загружена")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")
print(f"📊 Уровней: {len(PREMIUM_LEVELS)}")
print(f"💎 Пользователей с премиумом: {len(user_premium)}")