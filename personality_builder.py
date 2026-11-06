"""Систмка создаёт и постоянно обновляет впечатления и мысли о файлах"""

import os
import sys
import json
import re
import time
import random
import threading
from datetime import datetime

# ============================================================
# 0. ОБЁРТКА UTF-8 УБРАНА
# ============================================================
# ВАЖНО: обёртка sys.stdout должна быть ТОЛЬКО в auto_start.py
# (или в bot.py, если он запускается отдельно).
#
# Если обернуть sys.stdout второй раз — старая обёртка закрывается
# автоматически, вместе с buffer, и любой print() падает с
# ValueError: I/O operation on closed file.
#
# Поэтому здесь НЕТ обёртки. auto_start.py уже её сделал.

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from personality_analyzer import generate_deep_impression, detect_mood

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

PERSONALITY_FOLDER = "personality_notes"
MAX_IMPRESSIONS_PER_FILE = 20
MIN_UPDATE_INTERVAL_HOURS = 2

os.makedirs(PERSONALITY_FOLDER, exist_ok=True)

# ============================================================
# 3. ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ
# ============================================================

def get_impression_file_path(filename):
    """Получить путь к файлу впечатления"""
    base_name = os.path.splitext(filename)[0]
    return os.path.join(PERSONALITY_FOLDER, f"{base_name}_impression.json")


def load_impression(filename):
    """Загрузить впечатление о файле"""
    file_path = get_impression_file_path(filename)
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON впечатления {filename}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки впечатления {filename}: {e}")
    return None


def save_impression(filename, data):
    """Сохранить впечатление о файле"""
    file_path = get_impression_file_path(filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения впечатления {filename}: {e}")
        return False


def get_all_impression_files():
    """Получить список всех файлов впечатлений"""
    files = []
    try:
        for f in os.listdir(PERSONALITY_FOLDER):
            if f.endswith("_impression.json"):
                files.append(f)
    except Exception as e:
        print(f"⚠️ Ошибка чтения папки впечатлений: {e}")
    return files


def get_all_impressions():
    """Получить все впечатления"""
    result = {}
    for f in get_all_impression_files():
        filename = f.replace("_impression.json", ".py")
        data = load_impression(filename)
        if data:
            result[filename] = data
    return result


def get_impression(filename):
    """Получить впечатление о конкретном файле"""
    return load_impression(filename)

# ============================================================
# 4. ГЕНЕРАЦИЯ НОВОЙ МЫСЛИ (СОВМЕСТИМОСТЬ)
# ============================================================

def generate_new_thought(filename, content, old_impression=""):
    """
    Генерирует новую мысль о файле на основе старого впечатления.
    
    ВАЖНО: эта функция нужна для impression_manager.
    
    Args:
        filename: имя файла
        content: содержимое файла или текст общения
        old_impression: старое впечатление
    
    Returns:
        str: новая мысль
    """
    try:
        from impression_generator import generate_new_thought as _gen
        return _gen(filename, content, old_impression)
    except ImportError:
        # Fallback — используем generate_deep_impression
        try:
            if content and len(str(content)) > 30:
                return generate_deep_impression(filename, str(content))
        except Exception:
            pass
        
        # Последний fallback
        return f"Хм, {filename} всё ещё интересный файл."

# ============================================================
# 5. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def create_or_update_impression(filename, content=None, force=False):
    """Создать или обновить впечатление для конкретного файла"""
    
    if not os.path.exists(filename):
        return None
    
    if content is None:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ Ошибка чтения {filename}: {e}")
            return None
    
    existing = load_impression(filename)
    
    # Если файла нет — создаём
    if existing is None:
        new_text = generate_deep_impression(filename, content)
        data = {
            "impression": new_text,
            "thoughts": [],
            "mood": detect_mood(new_text),
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "version": 1,
            "usage_count": 0,
            "impression_size_kb": len(new_text) / 1024 if new_text else 0,
            "has_likes": "НРАВИТСЯ" in new_text,
            "has_dislikes": "БЕСИТ" in new_text,
            "has_wants": "ХОЧЕТСЯ ИЗМЕНИТЬ" in new_text,
            "has_best_part": "ЛУЧШАЯ ЧАСТЬ" in new_text,
            "has_emotion": "ЭМОЦИОНАЛЬНАЯ" in new_text,
        }
        save_impression(filename, data)
        return data
    
    # Если принудительное обновление или прошло достаточно времени
    if force:
        new_text = generate_deep_impression(filename, content)
        thoughts = existing.get("thoughts", [])
        thoughts.append({
            "text": new_text[:200] + "...",
            "date": datetime.now().isoformat(),
        })
        if len(thoughts) > MAX_IMPRESSIONS_PER_FILE:
            thoughts = thoughts[-MAX_IMPRESSIONS_PER_FILE:]
        
        data = {
            "impression": new_text,
            "thoughts": thoughts,
            "mood": detect_mood(new_text),
            "updated": datetime.now().isoformat(),
            "version": existing.get("version", 0) + 1,
            "usage_count": existing.get("usage_count", 0),
            "impression_size_kb": len(new_text) / 1024,
            "has_likes": "НРАВИТСЯ" in new_text,
            "has_dislikes": "БЕСИТ" in new_text,
            "has_wants": "ХОЧЕТСЯ ИЗМЕНИТЬ" in new_text,
            "has_best_part": "ЛУЧШАЯ ЧАСТЬ" in new_text,
            "has_emotion": "ЭМОЦИОНАЛЬНАЯ" in new_text,
        }
        save_impression(filename, data)
        return data
    
    # Проверяем, нужно ли обновить
    updated = existing.get("updated")
    if updated:
        try:
            last_update = datetime.fromisoformat(updated)
            if (datetime.now() - last_update).total_seconds() < MIN_UPDATE_INTERVAL_HOURS * 3600:
                return existing
        except Exception:
            pass
    
    # Обновляем
    new_text = generate_deep_impression(filename, content)
    thoughts = existing.get("thoughts", [])
    thoughts.append({
        "text": new_text[:200] + "...",
        "date": datetime.now().isoformat(),
    })
    if len(thoughts) > MAX_IMPRESSIONS_PER_FILE:
        thoughts = thoughts[-MAX_IMPRESSIONS_PER_FILE:]
    
    data = {
        "impression": new_text,
        "thoughts": thoughts,
        "mood": detect_mood(new_text),
        "updated": datetime.now().isoformat(),
        "version": existing.get("version", 0) + 1,
        "usage_count": existing.get("usage_count", 0),
        "impression_size_kb": len(new_text) / 1024,
        "has_likes": "НРАВИТСЯ" in new_text,
        "has_dislikes": "БЕСИТ" in new_text,
        "has_wants": "ХОЧЕТСЯ ИЗМЕНИТЬ" in new_text,
        "has_best_part": "ЛУЧШАЯ ЧАСТЬ" in new_text,
        "has_emotion": "ЭМОЦИОНАЛЬНАЯ" in new_text,
    }
    
    save_impression(filename, data)
    return data


def increment_usage(filename):
    """Увеличить счётчик использования впечатления"""
    data = load_impression(filename)
    if data:
        data["usage_count"] = data.get("usage_count", 0) + 1
        save_impression(filename, data)
        return True
    return False


def force_update_all_impressions():
    """Принудительно обновить все мнения"""
    all_files = [
        f for f in os.listdir(".")
        if f.endswith(".py") and not f.startswith("_")
    ]
    updated = 0
    
    print("🔄 Принудительное обновление всех мнений...")
    for filename in all_files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            result = create_or_update_impression(filename, content, force=True)
            if result:
                updated += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Ошибка обновления {filename}: {e}")
    
    print(f"✅ Обновлено мнений: {updated}")
    return updated

# ============================================================
# 6. ФОРМАТИРОВАНИЕ
# ============================================================

def format_impressions(limit=20):
    """Форматировать впечатления для вывода"""
    all_impressions = get_all_impressions()
    
    if not all_impressions:
        return "😐 Пока нет мнений"
    
    lines = ["🎭 МНЕНИЯ О ФАЙЛАХ"]
    lines.append("=" * 60)
    
    for filename, data in list(all_impressions.items())[:limit]:
        lines.append(f"\n📄 {filename}")
        impression = data.get('impression', 'Нет мнения')
        size_kb = data.get('impression_size_kb', 0)
        mood = data.get('mood', 'neutral')
        mood_icon = "😊" if mood == "positive" else "😠" if mood == "negative" else "😐"
        
        lines.append(f"  {mood_icon} {impression[:400]}...")
        lines.append(f"  📊 Размер: {size_kb:.1f}KB")
        
        parts = []
        if data.get("has_likes"):
            parts.append("❤️")
        if data.get("has_dislikes"):
            parts.append("💢")
        if data.get("has_wants"):
            parts.append("🔧")
        if data.get("has_best_part"):
            parts.append("⭐")
        if data.get("has_emotion"):
            parts.append("😊")
        lines.append(f"  📋 Разделы: {' '.join(parts) if parts else 'базовое'}")
        lines.append(f"  🕐 Версия: {data.get('version', 1)}")
    
    return "\n".join(lines)


def format_single_impression(filename):
    """Форматировать одно впечатление"""
    data = get_impression(filename)
    if not data:
        return f"❌ Нет мнения о {filename}"
    
    lines = [
        f"📄 {filename}",
        f"💬 {data.get('impression', 'Нет мнения')}",
    ]
    
    thoughts = data.get("thoughts", [])
    if thoughts:
        lines.append(f"\n💭 ИСТОРИЯ МЫСЛЕЙ ({len(thoughts)}):")
        for thought in thoughts[-5:]:
            lines.append(f"  • {thought.get('text', '')}")
    
    lines.append(f"\n📊 Размер: {data.get('impression_size_kb', 0):.1f}KB")
    lines.append(f"🎭 Настроение: {data.get('mood', 'neutral')}")
    lines.append(f"🕐 Версия: {data.get('version', 1)}")
    lines.append(f"📅 Создано: {data.get('created', '?')[:16]}")
    lines.append(f"📅 Обновлено: {data.get('updated', '?')[:16]}")
    
    return "\n".join(lines)

# ============================================================
# 7. АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ
# ============================================================

def auto_update_thoughts_loop():
    """Цикл автообновления мыслей о файлах"""
    while True:
        time.sleep(MIN_UPDATE_INTERVAL_HOURS * 3600)
        try:
            print("🔄 Обновляю мнения о файлах...")
            all_files = [
                f for f in os.listdir(".")
                if f.endswith(".py") and not f.startswith("_")
            ]
            
            updated = 0
            for filename in all_files:
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        content = f.read()
                    result = create_or_update_impression(filename, content)
                    if result:
                        updated += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ Ошибка обновления {filename}: {e}")
            
            print(f"✅ Обновлено мнений о {updated} файлах")
            
        except Exception as e:
            print(f"⚠️ Ошибка автообновления мнений: {e}")


def start_auto_thought_updater():
    """Запустить автообновление мыслей в фоне"""
    thread = threading.Thread(target=auto_update_thoughts_loop, daemon=True)
    thread.start()
    print("🧠 Автообновление мнений запущено (каждые 2 часа)")

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🎭 Модуль мнений загружен")
print(f"📁 Папка: {PERSONALITY_FOLDER}/")
print(f"📊 Файлов с мнениями: {len(get_all_impression_files())}")

start_auto_thought_updater()