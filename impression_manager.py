"""Управление впечатлениями — инициализация, обновление при общении"""

import os
import time
import random
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from personality_builder import (
    get_all_impression_files, load_impression, save_impression,
    create_or_update_impression, generate_new_thought,
    MAX_IMPRESSIONS_PER_FILE, PERSONALITY_FOLDER
)

# ============================================================
# 2. ИНИЦИАЛИЗАЦИЯ (ДЛЯ ВСЕХ ФАЙЛОВ)
# ============================================================

def initialize_impressions():
    """Создать впечатления для всех файлов"""
    existing_files = get_all_impression_files()
    existing_names = [f.replace("_impression.json", ".py") for f in existing_files]
    
    all_files = [f for f in os.listdir(".") if f.endswith(".py") and not f.startswith("_")]
    
    new_files = [f for f in all_files if f not in existing_names]
    
    if not new_files:
        print(f"🎭 Все файлы уже имеют впечатления ({len(existing_files)})")
        return 0, 0
    
    print(f"🎭 Создаю впечатления для {len(new_files)} новых файлов...")
    
    created = 0
    for i, filename in enumerate(new_files):
        try:
            print(f"  [{i+1}/{len(new_files)}] {filename}...", end=" ")
            
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            
            result = create_or_update_impression(filename, content)
            
            if result:
                created += 1
                print("✅ создано")
            else:
                print("⏭ пропущено")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ ошибка: {e}")
    
    print(f"🎭 Создано: {created} новых впечатлений")
    return created, 0

# ============================================================
# 3. ОБНОВЛЕНИЕ ПРИ ОБЩЕНИИ (НОВОЕ!)
# ============================================================

def update_impression_on_chat(filename, chat_text):
    """Обновить впечатление о файле на основе общения"""
    data = load_impression(filename)
    if not data:
        return None
    
    # Проверяем, нужно ли обновить (раз в час)
    updated = data.get("updated")
    if updated:
        try:
            last_update = datetime.fromisoformat(updated)
            if (datetime.now() - last_update).total_seconds() < 3600:
                return data
        except:
            pass
    
    # Генерируем новую мысль на основе общения
    new_thought = generate_new_thought(filename, chat_text, data.get("impression", ""))
    
    if new_thought:
        thoughts = data.get("thoughts", [])
        thoughts.append({
            "text": new_thought,
            "date": datetime.now().isoformat(),
        })
        if len(thoughts) > MAX_IMPRESSIONS_PER_FILE:
            thoughts = thoughts[-MAX_IMPRESSIONS_PER_FILE:]
        
        data["thoughts"] = thoughts
        data["updated"] = datetime.now().isoformat()
        data["version"] = data.get("version", 0) + 1
        
        save_impression(filename, data)
        return data
    
    return data

def update_random_impression_on_chat(chat_text):
    """Обновить случайное впечатление на основе общения"""
    impression_files = get_all_impression_files()
    if not impression_files:
        return None
    
    random_file = random.choice(impression_files)
    filename = random_file.replace("_impression.json", ".py")
    
    if os.path.exists(filename):
        return update_impression_on_chat(filename, chat_text)
    
    return None

# ============================================================
# 4. ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ВСЕХ ВПЕЧАТЛЕНИЙ
# ============================================================

def refresh_all_impressions():
    """Принудительно обновить все впечатления"""
    all_files = [f for f in os.listdir(".") if f.endswith(".py") and not f.startswith("_")]
    
    updated = 0
    failed = 0
    
    print(f"🔄 Обновляю впечатления для {len(all_files)} файлов...")
    
    for i, filename in enumerate(all_files):
        try:
            print(f"  [{i+1}/{len(all_files)}] {filename}...", end=" ")
            
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            
            result = create_or_update_impression(filename, content)
            
            if result:
                updated += 1
                print("✅ обновлено")
            else:
                failed += 1
                print("❌ ошибка")
            
            time.sleep(2)
            
        except Exception as e:
            failed += 1
            print(f"❌ ошибка: {e}")
    
    print(f"🔄 Обновлено: {updated}, ошибок: {failed}")
    return updated, failed

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("🎭 Менеджер впечатлений загружен")
print(f"📁 Папка: {PERSONALITY_FOLDER}/")