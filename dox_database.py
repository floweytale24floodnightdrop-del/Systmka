"""База данных для докса — хранение всей информации о людях"""

import os
import re
import json
import time
import hashlib
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DOX_DB_FILE = "dox_database.json"
MAX_PEOPLE = 1000

# Максимальное количество точек данных на человека
MAX_DATA_POINTS = 500

# Сколько дней хранить устаревшие записи
MAX_DATA_AGE_DAYS = 90

# ============================================================
# 2. ДАННЫЕ
# ============================================================

dox_db = {
    "people": {},
    "sources": {},
    "queries": {},
    "statistics": {
        "total_people": 0,
        "total_queries": 0,
        "last_query": None,
    },
    "known_platforms": [
        "telegram", "vk", "instagram", "twitter", "youtube",
        "github", "tiktok", "reddit", "pinterest", "spotify",
        "steam", "discord", "twitch", "tumblr", "linkedin",
        "facebook", "whatsapp", "signal", "threads",
    ],
    "index": {},
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_dox_db():
    """Сохранить БД докса"""
    try:
        with open(DOX_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dox_db, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения БД докса: {e}")
        return False


def load_dox_db():
    """Загрузить БД докса"""
    global dox_db
    try:
        if os.path.exists(DOX_DB_FILE):
            with open(DOX_DB_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ("people", "sources", "queries", "index"):
                    if isinstance(loaded.get(key), dict):
                        dox_db[key] = loaded[key]
                
                if isinstance(loaded.get("statistics"), dict):
                    dox_db["statistics"].update(loaded["statistics"])
                
                if isinstance(loaded.get("known_platforms"), list):
                    dox_db["known_platforms"] = loaded["known_platforms"]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON докса: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки БД докса: {e}")
        return False


load_dox_db()

# ============================================================
# 4. НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_identifier(identifier):
    """
    Нормализовать идентификатор.
    
    Args:
        identifier: ID пользователя, ник, телефон и т.д.
    
    Returns:
        str: нормализованный ID
    """
    if identifier is None:
        return "unknown"
    
    id_str = str(identifier).strip()
    
    # Если это просто число (Telegram ID)
    if id_str.isdigit():
        return f"tg_{id_str}"
    
    # Иначе — хэш
    clean = id_str.replace("@", "").lower()
    hash_part = hashlib.md5(clean.encode()).hexdigest()[:12]
    return f"user_{hash_part}"

# ============================================================
# 5. ИНДЕКСИРОВАНИЕ
# ============================================================

def update_index(person_id, value, key=None):
    """
    Обновить индекс для быстрого поиска.
    
    Args:
        person_id: ID человека
        value: значение (телефон, email, ник и т.д.)
        key: ключ данных (phone, email, username и т.д.)
    """
    if person_id not in dox_db["index"]:
        dox_db["index"][person_id] = []
    
    value_lower = str(value).lower()
    
    # Базовое значение
    if value_lower not in dox_db["index"][person_id]:
        dox_db["index"][person_id].append(value_lower)
    
    # Значение с ключом
    if key:
        key_value = f"{key}:{value_lower}"
        if key_value not in dox_db["index"][person_id]:
            dox_db["index"][person_id].append(key_value)

# ============================================================
# 6. ДОБАВЛЕНИЕ ДАННЫХ
# ============================================================

def add_person_data(identifier, data, source="unknown"):
    """
    Добавить информацию о человеке.
    
    Args:
        identifier: ID/ник/телефон
        data: dict с данными
        source: источник данных
    
    Returns:
        str или None: person_id
    """
    if not identifier or not isinstance(data, dict):
        return None
    
    person_id = normalize_identifier(identifier)
    
    # Проверяем лимит
    if len(dox_db["people"]) >= MAX_PEOPLE:
        _cleanup_oldest_person()
    
    # Создаём запись
    if person_id not in dox_db["people"]:
        dox_db["people"][person_id] = {
            "identifiers": [identifier],
            "data": {},
            "sources": [],
            "first_seen": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "confidence": 0,
        }
        dox_db["statistics"]["total_people"] += 1
    
    person = dox_db["people"][person_id]
    
    # Добавляем идентификатор
    if identifier not in person["identifiers"]:
        person["identifiers"].append(identifier)
        update_index(person_id, identifier)
    
    # Добавляем данные
    for key, value in data.items():
        if value is None:
            continue
        
        if key not in person["data"]:
            person["data"][key] = []
        
        # Проверка дубликата
        exists = any(
            item.get("value") == value
            for item in person["data"][key]
            if isinstance(item, dict)
        )
        
        if not exists:
            # Ограничение количества точек данных
            if len(person["data"][key]) >= MAX_DATA_POINTS:
                continue
            
            person["data"][key].append({
                "value": value,
                "source": source,
                "found_at": datetime.now().isoformat(),
                "confidence": 0.5,
            })
            
            update_index(person_id, str(value), key)
    
    # Добавляем источник
    if source and source not in person["sources"]:
        person["sources"].append(source)
    
    person["last_updated"] = datetime.now().isoformat()
    person["confidence"] = min(1.0, person.get("confidence", 0) + 0.1)
    
    save_dox_db()
    return person_id


def _cleanup_oldest_person():
    """Удалить самого старого человека (при переполнении)"""
    if not dox_db["people"]:
        return
    
    try:
        oldest_id = min(
            dox_db["people"].items(),
            key=lambda x: x[1].get("last_updated", ""),
        )[0]
        
        del dox_db["people"][oldest_id]
        
        if oldest_id in dox_db["index"]:
            del dox_db["index"][oldest_id]
        
        dox_db["statistics"]["total_people"] = len(dox_db["people"])
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")

# ============================================================
# 7. ПОИСК
# ============================================================

def search_person(query):
    """
    Поиск человека в БД.
    
    Args:
        query: что искать
    
    Returns:
        list: список найденных записей
    """
    if not query:
        return []
    
    query_lower = str(query).lower().replace("@", "")
    results = []
    seen_ids = set()
    
    # === 1. Поиск по индексу ===
    for person_id, index_values in dox_db["index"].items():
        if person_id in seen_ids:
            continue
        
        for index_val in index_values:
            if query_lower in index_val:
                person = dox_db["people"].get(person_id)
                if person:
                    results.append({
                        "id": person_id,
                        "identifiers": person.get("identifiers", []),
                        "data": person.get("data", {}),
                        "confidence": person.get("confidence", 0),
                    })
                    seen_ids.add(person_id)
                break
    
    # === 2. Если ничего не найдено — полный поиск ===
    if not results:
        for person_id, person in dox_db["people"].items():
            if person_id in seen_ids:
                continue
            
            # Проверяем идентификаторы
            for identifier in person.get("identifiers", []):
                if query_lower in str(identifier).lower():
                    results.append({
                        "id": person_id,
                        "identifiers": person["identifiers"],
                        "data": person["data"],
                        "confidence": person.get("confidence", 0),
                    })
                    seen_ids.add(person_id)
                    break
            
            # Проверяем данные
            if person_id in seen_ids:
                continue
            
            for key, values in person.get("data", {}).items():
                for item in values:
                    if not isinstance(item, dict):
                        continue
                    if query_lower in str(item.get("value", "")).lower():
                        results.append({
                            "id": person_id,
                            "identifiers": person["identifiers"],
                            "data": person["data"],
                            "confidence": person.get("confidence", 0),
                        })
                        seen_ids.add(person_id)
                        break
                if person_id in seen_ids:
                    break
    
    # Обновляем статистику
    dox_db["statistics"]["total_queries"] += 1
    dox_db["statistics"]["last_query"] = datetime.now().isoformat()
    save_dox_db()
    
    return results


def get_person_data(person_id):
    """Получить данные человека по ID"""
    return dox_db["people"].get(person_id)


def get_data_by_platform(person_id, platform):
    """Получить данные по конкретной платформе"""
    person = get_person_data(person_id)
    if not person:
        return None
    
    platform_lower = platform.lower()
    platform_data = {}
    
    for key, values in person.get("data", {}).items():
        if platform_lower in key.lower():
            platform_data[key] = values
    
    return platform_data

# ============================================================
# 8. ОБНОВЛЕНИЕ
# ============================================================

def update_person_data(person_id, new_data, source="unknown"):
    """Обновить данные человека"""
    if not person_id or not isinstance(new_data, dict):
        return False
    
    person = get_person_data(person_id)
    if not person:
        return False
    
    for key, value in new_data.items():
        if value is None:
            continue
        
        if key not in person["data"]:
            person["data"][key] = []
        
        exists = any(
            item.get("value") == value
            for item in person["data"][key]
            if isinstance(item, dict)
        )
        
        if not exists:
            person["data"][key].append({
                "value": value,
                "source": source,
                "found_at": datetime.now().isoformat(),
                "confidence": 0.5,
            })
            update_index(person_id, str(value), key)
    
    if source and source not in person["sources"]:
        person["sources"].append(source)
    
    person["last_updated"] = datetime.now().isoformat()
    save_dox_db()
    return True


def increase_confidence(person_id, key, value):
    """Увеличить уверенность в данных"""
    person = get_person_data(person_id)
    if not person:
        return False
    
    if key in person.get("data", {}):
        for item in person["data"][key]:
            if isinstance(item, dict) and item.get("value") == value:
                item["confidence"] = min(1.0, item.get("confidence", 0) + 0.2)
                save_dox_db()
                return True
    
    return False

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_dox_stats():
    """Получить статистику БД"""
    stats = dox_db["statistics"].copy()
    stats["people_count"] = len(dox_db["people"])
    stats["sources"] = len(dox_db["sources"])
    stats["index_size"] = len(dox_db["index"])
    
    total_data = 0
    for person in dox_db["people"].values():
        for key, values in person.get("data", {}).items():
            if isinstance(values, list):
                total_data += len(values)
    
    stats["total_data_points"] = total_data
    
    return stats


def format_dox_stats():
    """Форматировать статистику"""
    stats = get_dox_stats()
    
    lines = [
        "📊 СТАТИСТИКА БД ДОКСА:",
        f"👤 Людей: {stats['people_count']} / {MAX_PEOPLE}",
        f"📝 Точек данных: {stats['total_data_points']}",
        f"🔍 Запросов: {stats['total_queries']}",
        f"📡 Источников: {stats['sources']}",
        f"📇 Индексов: {stats['index_size']}",
    ]
    
    if stats.get("last_query"):
        lines.append(f"⏱ Последний запрос: {stats['last_query'][:16]}")
    
    return "\n".join(lines)

# ============================================================
# 10. ОЧИСТКА
# ============================================================

def clear_old_data(days=MAX_DATA_AGE_DAYS):
    """
    Удалить данные старше N дней.
    
    Returns:
        int: количество удалённых
    """
    now = datetime.now()
    deleted = 0
    
    for person_id in list(dox_db["people"].keys()):
        person = dox_db["people"][person_id]
        last_updated = person.get("last_updated")
        
        if not last_updated:
            continue
        
        try:
            updated_dt = datetime.fromisoformat(last_updated)
            if (now - updated_dt).days > days:
                del dox_db["people"][person_id]
                if person_id in dox_db["index"]:
                    del dox_db["index"][person_id]
                deleted += 1
        except (ValueError, TypeError):
            pass
    
    if deleted:
        dox_db["statistics"]["total_people"] = len(dox_db["people"])
        save_dox_db()
        print(f"🗑 Удалено старых записей: {deleted}")
    
    return deleted


def clear_all_data():
    """Полная очистка БД"""
    global dox_db
    
    dox_db["people"] = {}
    dox_db["sources"] = {}
    dox_db["queries"] = {}
    dox_db["index"] = {}
    dox_db["statistics"] = {
        "total_people": 0,
        "total_queries": 0,
        "last_query": None,
    }
    
    save_dox_db()
    print("🗑 БД докса полностью очищена")
    return True

# ============================================================
# 11. ЭКСПОРТ
# ============================================================

def export_person_data(person_id, output_file=None):
    """
    Экспортировать данные человека в файл.
    
    Returns:
        str или None: путь к файлу
    """
    person = get_person_data(person_id)
    if not person:
        return None
    
    if output_file is None:
        output_file = f"dox_export_{person_id}_{int(time.time())}.json"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(person, f, ensure_ascii=False, indent=2)
        return output_file
    except Exception as e:
        print(f"⚠️ Ошибка экспорта: {e}")
        return None

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("📊 База докса загружена (PC)")
print(f"👤 Людей в БД: {len(dox_db['people'])} / {MAX_PEOPLE}")
print(f"📇 Индексов: {len(dox_db['index'])}")
print(f"📡 Платформ: {len(dox_db['known_platforms'])}")