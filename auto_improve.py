"""Автоматические улучшения — Систмка сама решает что добавить"""

import os
import re
import ast
import json
import random
import shutil
import threading
import time
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

IMPROVEMENTS_FILE = "improvements.json"
BACKUP_DIR = "auto_improve_backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

# Файлы, которые НЕЛЬЗЯ трогать (ОБНОВЛЕНО)
FORBIDDEN_FILES = {
    # Ядро
    "bot.py", "config.py", "config_network.py", "database.py",
    "system_prompt.py", "auto_import.py", "import_core.py",
    "import_modules.py", "import_loader.py",
    
    # Ошибки и защита
    "error_fixer.py", "error_analyzer.py", "error_analyzer_advanced.py",
    "error_reporter.py", "error_guardian.py", "module_fixer.py",
    "trash.py", "auto_start.py", "log_manager.py", "debug_changes.py",
    
    # Бот-обвязка
    "bot_handlers.py", "bot_loops.py", "bot_startup.py",
    "message_processor.py",
    
    # Самоулучшение
    "auto_improve.py", "auto_install.py",
    
    # ИИ-ключи
    "ai_key_rotator.py", "ai_model_manager.py",
    "ai_request_handler.py", "ai_router.py",
    
    # Промты
    "prompt_notes_manager.py",
}

# Файлы, которые можно трогать (по приоритету)
SAFE_FILES = [
    "memes.py", "weather.py", "holidays.py", "creativity.py",
    "commands.py", "messages.py", "profile.py",
]

improvements_log = []

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_improvements():
    """Сохранить лог улучшений"""
    try:
        with open(IMPROVEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(improvements_log, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения улучшений: {e}")
        return False


def load_improvements():
    """Загрузить лог улучшений"""
    global improvements_log
    try:
        if os.path.exists(IMPROVEMENTS_FILE):
            with open(IMPROVEMENTS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, list):
                improvements_log = loaded
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки улучшений: {e}")
        improvements_log = []
        return False


load_improvements()

# ============================================================
# 3. ГЕНЕРАЦИЯ ИДЕЙ
# ============================================================

def generate_new_feature_idea():
    """Сгенерировать идею новой функции"""
    ideas = [
        "добавить команду для случайного факта",
        "добавить ежедневную цитату",
        "добавить игру в слова",
        "добавить генератор шуток",
        "добавить гороскоп",
        "добавить анекдоты",
        "добавить тосты",
        "добавить комплименты",
        "добавить предсказания",
        "добавить полезные советы",
        "добавить цитаты о любви",
        "добавить загадки",
    ]
    return random.choice(ideas)

# ============================================================
# 4. ПРОВЕРКА БЕЗОПАСНОСТИ ФАЙЛА
# ============================================================

def is_safe_to_modify(filepath):
    """Проверить, безопасно ли модифицировать файл"""
    if not filepath or not os.path.exists(filepath):
        return False, "Файл не существует"
    
    filename = os.path.basename(filepath)
    
    if not filename.endswith(".py"):
        return False, "Не .py файл"
    
    if filename in FORBIDDEN_FILES:
        return False, f"Файл {filename} в чёрном списке"
    
    if filename.startswith("_"):
        return False, "Служебный файл"
    
    try:
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > 200:
            return False, f"Файл слишком большой ({size_kb:.0f}KB)"
    except Exception:
        return False, "Не удалось получить размер"
    
    return True, "OK"


def is_syntax_valid(content):
    """Проверить синтаксис Python"""
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False

# ============================================================
# 5. СОЗДАНИЕ НОВЫХ ФАЙЛОВ
# ============================================================

def create_new_feature_file(idea):
    """Создать новый файл с функцией"""
    if not idea:
        return False
    
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', idea.lower())
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    
    filename = f"feature_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    func_name = safe_name
    content = f'''"""{idea.capitalize()} — автосозданная функция"""

from datetime import datetime


def {func_name}():
    """
    Реализация: {idea}
    
    Returns:
        str: результат
    """
    return f"Функция '{idea}' вызвана в {{datetime.now().isoformat()}}"


# Тест
if __name__ == "__main__":
    print({func_name}())
'''
    
    if not is_syntax_valid(content):
        print(f"❌ Синтаксическая ошибка в сгенерированном коде")
        return False
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        improvements_log.append({
            "type": "new_file",
            "idea": idea,
            "file": filename,
            "time": datetime.now().isoformat(),
        })
        save_improvements()
        
        print(f"✨ Создан новый файл: {filename}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания файла: {e}")
        return False

# ============================================================
# 6. УЛУЧШЕНИЕ СУЩЕСТВУЮЩИХ ФАЙЛОВ
# ============================================================

def backup_file(filepath):
    """Создать бэкап файла"""
    try:
        filename = os.path.basename(filepath)
        backup_name = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(filepath, backup_path)
        return backup_path
    except Exception as e:
        print(f"⚠️ Ошибка бэкапа: {e}")
        return None


def improve_existing_file(filename):
    """Улучшить существующий файл БЕЗОПАСНО"""
    if not os.path.exists(filename):
        return False
    
    is_safe, reason = is_safe_to_modify(filename)
    if not is_safe:
        print(f"⏭ Пропуск {filename}: {reason}")
        return False
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            original = f.read()
        
        if not is_syntax_valid(original):
            print(f"⏭ Пропуск {filename}: невалидный синтаксис")
            return False
        
        if "auto-improved" in original[:500]:
            print(f"⏭ Пропуск {filename}: уже улучшен")
            return False
        
        lines = original.split("\n")
        
        insert_index = 0
        
        if lines and lines[0].strip().startswith('"""'):
            for i in range(1, min(len(lines), 30)):
                if '"""' in lines[i]:
                    insert_index = i + 1
                    break
        elif lines and lines[0].strip().startswith("'''"):
            for i in range(1, min(len(lines), 30)):
                if "'''" in lines[i]:
                    insert_index = i + 1
                    break
        
        marker = f"\n# auto-improved by Systmka at {datetime.now().isoformat()}\n"
        lines.insert(insert_index, marker)
        
        new_content = "\n".join(lines)
        
        if not is_syntax_valid(new_content):
            print(f"❌ Новый код невалидный — откат {filename}")
            return False
        
        backup_path = backup_file(filename)
        if not backup_path:
            print(f"❌ Не удалось создать бэкап {filename}")
            return False
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        improvements_log.append({
            "type": "improve_file",
            "file": filename,
            "backup": backup_path,
            "time": datetime.now().isoformat(),
        })
        save_improvements()
        
        print(f"📝 Улучшен: {filename}")
        return True
    
    except Exception as e:
        print(f"❌ Ошибка улучшения {filename}: {e}")
        return False

# ============================================================
# 7. ГЛАВНЫЙ ЦИКЛ
# ============================================================

_auto_improve_active = False


def auto_improve_loop():
    """Цикл автоулучшений"""
    global _auto_improve_active
    
    if _auto_improve_active:
        return
    _auto_improve_active = True
    
    print("✨ Цикл автоулучшений запущен (безопасный режим)")
    
    while True:
        try:
            time.sleep(1800)  # 30 минут
            
            if random.random() < 0.3:
                idea = generate_new_feature_idea()
                create_new_feature_file(idea)
            
            if random.random() < 0.2:
                available = [f for f in SAFE_FILES if os.path.exists(f)]
                
                if available:
                    filename = random.choice(available)
                    improve_existing_file(filename)
        
        except Exception as e:
            print(f"⚠️ Ошибка в auto_improve_loop: {e}")


def start_auto_improve():
    """Запустить цикл в фоне"""
    thread = threading.Thread(target=auto_improve_loop, daemon=True)
    thread.start()
    print("✨ Автоулучшения запущены в фоне")
    return thread

# ============================================================
# 8. СТАТИСТИКА
# ============================================================

def get_improvements_stats():
    """Получить статистику улучшений"""
    new_files = len([i for i in improvements_log if i.get("type") == "new_file"])
    improved_files = len([i for i in improvements_log if i.get("type") == "improve_file"])
    
    return {
        "total": len(improvements_log),
        "new_files": new_files,
        "improved_files": improved_files,
        "last": improvements_log[-1] if improvements_log else None,
    }


def format_improvements_stats():
    """Форматировать статистику"""
    stats = get_improvements_stats()
    
    lines = [
        "✨ СТАТИСТИКА УЛУЧШЕНИЙ:",
        f"  📊 Всего: {stats['total']}",
        f"  🆕 Новых файлов: {stats['new_files']}",
        f"  📝 Улучшено файлов: {stats['improved_files']}",
    ]
    
    if stats["last"]:
        lines.append(f"  🕐 Последнее: {stats['last'].get('time', '?')[:16]}")
    
    return "\n".join(lines)

# ============================================================
# 9. РУЧНОЕ УПРАВЛЕНИЕ
# ============================================================

def create_feature(idea):
    """Ручное создание функции по идее"""
    return create_new_feature_file(idea)


def improve_file(filename):
    """Ручное улучшение файла"""
    return improve_existing_file(filename)


def clear_improvements_log():
    """Очистить лог улучшений"""
    global improvements_log
    improvements_log = []
    save_improvements()
    return True

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("✨ Модуль автоулучшений загружен (БЕЗОПАСНЫЙ РЕЖИМ)")
print(f"🚫 Файлов в чёрном списке: {len(FORBIDDEN_FILES)}")
print(f"✅ Безопасных файлов: {len(SAFE_FILES)}")
print(f"📊 Улучшений в логе: {len(improvements_log)}")