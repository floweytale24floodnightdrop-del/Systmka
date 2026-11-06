"""Кастомные стикеры — Систмка сама добавляет себе стикеры"""

import os
import json
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

STICKERS_FILE = "custom_stickers.json"
MAX_STICKERS = 1000

# ============================================================
# 2. ДАННЫЕ
# ============================================================

custom_stickers = []

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_stickers():
    """Сохранить стикеры"""
    try:
        with open(STICKERS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_stickers, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения стикеров: {e}")
        return False


def load_stickers():
    """Загрузить стикеры"""
    global custom_stickers
    try:
        if os.path.exists(STICKERS_FILE):
            with open(STICKERS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    custom_stickers = loaded
        return custom_stickers
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON стикеров: {e}")
        custom_stickers = []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки стикеров: {e}")
        custom_stickers = []
    return custom_stickers


load_stickers()

# ============================================================
# 4. ДОБАВЛЕНИЕ СТИКЕРА
# ============================================================

def add_custom_sticker(file_id, set_name, source_user, description=""):
    """
    Добавить стикер.
    
    Args:
        file_id: file_id стикера
        set_name: имя пака
        source_user: источник (кто прислал)
        description: описание
    
    Returns:
        dict или None
    """
    if not file_id:
        print("⚠️ Нет file_id для стикера")
        return None
    
    # Проверяем дубликат
    for s in custom_stickers:
        if s.get("file_id") == file_id:
            return s  # Уже есть
    
    # Лимит
    if len(custom_stickers) >= MAX_STICKERS:
        # Удаляем самый старый
        if custom_stickers:
            custom_stickers.pop(0)
    
    sticker = {
        "id": len(custom_stickers) + 1,
        "file_id": file_id,
        "set_name": set_name or "unknown",
        "source_user": source_user or "unknown",
        "description": description or "",
        "added_at": datetime.now().isoformat(),
    }
    
    custom_stickers.append(sticker)
    save_stickers()
    return sticker

# ============================================================
# 5. ПАРСИНГ RAW DATA
# ============================================================

def parse_raw_data_response(raw_data):
    """
    Парсить ответ от RawDataBot.
    
    Args:
        raw_data: str или dict
    
    Returns:
        dict или None
    """
    try:
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            return None
        
        message = data.get("message", {})
        sticker = message.get("sticker", {})
        
        if not sticker:
            return None
        
        file_id = sticker.get("file_id")
        set_name = sticker.get("set_name")
        emoji = sticker.get("emoji")
        
        # Источник
        forward_from = message.get("forward_from", {})
        source_user = forward_from.get(
            "username",
            forward_from.get("first_name", "Unknown"),
        )
        
        return {
            "file_id": file_id,
            "set_name": set_name,
            "emoji": emoji,
            "source_user": source_user,
        }
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"⚠️ Ошибка парсинга raw data: {e}")
        return None

# ============================================================
# 6. АНАЛИЗ ПАКА
# ============================================================

def analyze_sticker_pack(bot, set_name):
    """
    Проанализировать стикер-пак.
    
    Returns:
        dict или None
    """
    if not bot or not set_name:
        return None
    
    try:
        sticker_set = bot.get_sticker_set(set_name)
        
        stickers = []
        for sticker in sticker_set.stickers:
            stickers.append({
                "file_id": sticker.file_id,
                "emoji": sticker.emoji,
                "set_name": sticker.set_name,
            })
        
        return {
            "title": sticker_set.title,
            "name": sticker_set.name,
            "stickers": stickers,
        }
    except Exception as e:
        print(f"⚠️ Ошибка анализа пака '{set_name}': {e}")
        return None

# ============================================================
# 7. ПОЛУЧЕНИЕ СПИСКА
# ============================================================

def get_all_custom_stickers():
    """Получить все стикеры"""
    return custom_stickers


def get_sticker_by_id(sticker_id):
    """Найти стикер по ID"""
    if sticker_id is None:
        return None
    
    for sticker in custom_stickers:
        if sticker.get("id") == sticker_id:
            return sticker
    return None


def get_sticker_by_file_id(file_id):
    """Найти стикер по file_id"""
    if not file_id:
        return None
    
    for sticker in custom_stickers:
        if sticker.get("file_id") == file_id:
            return sticker
    return None


def get_random_sticker():
    """Получить случайный стикер"""
    if not custom_stickers:
        return None
    
    import random
    return random.choice(custom_stickers)

# ============================================================
# 8. УДАЛЕНИЕ
# ============================================================

def remove_custom_sticker(sticker_id):
    """
    Удалить стикер по ID.
    
    Returns:
        bool: успех
    """
    global custom_stickers
    
    if sticker_id is None:
        return False
    
    for i, sticker in enumerate(custom_stickers):
        if sticker.get("id") == sticker_id:
            custom_stickers.pop(i)
            save_stickers()
            return True
    
    return False


def clear_all_stickers():
    """Очистить все стикеры"""
    global custom_stickers
    custom_stickers = []
    save_stickers()
    return True

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_stickers_stats():
    """Получить статистику"""
    sets = set()
    sources = set()
    
    for s in custom_stickers:
        if s.get("set_name"):
            sets.add(s["set_name"])
        if s.get("source_user"):
            sources.add(s["source_user"])
    
    return {
        "total_stickers": len(custom_stickers),
        "sets": len(sets),
        "sources": len(sources),
    }


def format_sticker_info(sticker):
    """Форматировать информацию о стикере"""
    if not sticker:
        return "❌ Стикер не найден"
    
    lines = [
        f"🆔 {sticker.get('id', '?')}",
        f"📦 Пак: {sticker.get('set_name', '?')}",
        f"👤 От: {sticker.get('source_user', '?')}",
    ]
    
    if sticker.get("description"):
        lines.append(f"📝 {sticker['description']}")
    
    if sticker.get("added_at"):
        lines.append(f"📅 {sticker['added_at'][:16]}")
    
    return "\n".join(lines)


def format_stickers_stats():
    """Форматировать статистику"""
    stats = get_stickers_stats()
    
    lines = [
        "🎯 СТАТИСТИКА СТИКЕРОВ:",
        f"📊 Всего: {stats['total_stickers']} / {MAX_STICKERS}",
        f"📦 Паков: {stats['sets']}",
        f"👤 Источников: {stats['sources']}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print(f"🎯 Модуль стикеров загружен (PC)")
print(f"📊 Кастомных стикеров: {len(custom_stickers)}")
print(f"📦 Паков: {get_stickers_stats()['sets']}")