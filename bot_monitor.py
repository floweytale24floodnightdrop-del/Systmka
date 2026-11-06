"""Мониторинг логов бота в реальном времени"""

import os
import time
import threading
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

# Ключевые слова для поиска ошибок
ERROR_KEYWORDS = [
    "Error", "Exception", "Traceback",
    "NameError", "ImportError", "KeyError",
    "AttributeError", "TypeError", "ModuleNotFoundError",
    "FileNotFoundError", "PermissionError", "SyntaxError",
    "ValueError", "RuntimeError", "IndexError",
    "IndentationError", "UnboundLocalError", "ZeroDivisionError",
]

# Ключевые слова для "успешных" сообщений
SUCCESS_KEYWORDS = [
    "✅", "успешно", "загружен", "готов",
    "ОК", "OK", "Готово",
]

# Ключевые слова для предупреждений
WARNING_KEYWORDS = [
    "⚠️", "предупреждение", "внимание", "WARNING",
]

# Максимум строк в логе (при очистке)
MAX_LOG_LINES = 200

# Максимальный размер лога (1MB)
MAX_LOG_SIZE = 1024 * 1024

# ============================================================
# 2. ОЧИСТКА ЛОГОВ
# ============================================================

def clean_logs(bot_dir=None):
    """
    Очистить логи (обрезать до MAX_LOG_LINES строк).
    
    Args:
        bot_dir: папка бота (если None — текущая)
    
    Returns:
        bool: успех
    """
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    cleaned = []
    log_files = ["bot.log", "boot.log", "error.log"]
    
    for log_name in log_files:
        log_file = os.path.join(bot_dir, log_name)
        
        if not os.path.exists(log_file):
            continue
        
        try:
            file_size = os.path.getsize(log_file)
            
            # Если файл маленький — не трогаем
            if file_size < MAX_LOG_SIZE:
                continue
            
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            if len(lines) > MAX_LOG_LINES:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[-MAX_LOG_LINES:])
                
                cleaned.append(log_name)
                print(f"✂️ {log_name} обрезан до {MAX_LOG_LINES} строк")
            else:
                print(f"✅ {log_name}: {len(lines)} строк")
        except Exception as e:
            print(f"⚠️ Ошибка очистки {log_name}: {e}")
    
    return len(cleaned) > 0

# ============================================================
# 3. ПОИСК ОШИБОК В ЛОГАХ
# ============================================================

def find_errors_in_log(bot_dir=None, log_file="bot.log"):
    """
    Найти все ошибки в логе.
    
    Args:
        bot_dir: папка бота (если None — текущая)
        log_file: имя файла лога
    
    Returns:
        list: список строк с ошибками
    """
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    errors = []
    log_path = os.path.join(bot_dir, log_file)
    
    if not os.path.exists(log_path):
        return errors
    
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ищем ключевые слова
            if any(word in line for word in ERROR_KEYWORDS):
                errors.append(line)
    except Exception as e:
        print(f"⚠️ Ошибка поиска ошибок в логе: {e}")
    
    return errors

def print_errors_from_log(bot_dir=None, limit=30):
    """
    Вывести ошибки из лога в консоль.
    
    Args:
        bot_dir: папка бота
        limit: максимум ошибок для вывода
    
    Returns:
        int: количество найденных ошибок
    """
    errors = find_errors_in_log(bot_dir)
    
    if errors:
        print("\n" + "=" * 60)
        print(f"❌ НАЙДЕНО ОШИБОК: {len(errors)}")
        print("=" * 60)
        
        for error in errors[-limit:]:
            # Обрезаем длинные строки
            if len(error) > 200:
                error = error[:200] + "..."
            print(f"  {error}")
        
        print("=" * 60 + "\n")
    else:
        print("✅ Ошибок в логе нет")
    
    return len(errors)

# ============================================================
# 4. МОНИТОРИНГ В РЕАЛЬНОМ ВРЕМЕНИ
# ============================================================

_log_monitor_active = False

def monitor_logs(bot_dir=None, log_file="bot.log", interval=2):
    """
    Мониторинг логов в реальном времени.
    
    Args:
        bot_dir: папка бота
        log_file: имя файла лога
        interval: интервал проверки в секундах
    """
    global _log_monitor_active
    
    if _log_monitor_active:
        return
    _log_monitor_active = True
    
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    log_path = os.path.join(bot_dir, log_file)
    last_position = 0
    
    # Ждём появления файла
    wait_count = 0
    while not os.path.exists(log_path) and wait_count < 30:
        time.sleep(1)
        wait_count += 1
    
    if not os.path.exists(log_path):
        print("⚠️ Файл логов не найден, мониторинг отключён")
        _log_monitor_active = False
        return
    
    print(f"📋 Мониторинг логов: {log_path}")
    
    while True:
        try:
            # Проверяем, не изменился ли файл
            current_size = os.path.getsize(log_path)
            if current_size < last_position:
                last_position = 0  # файл обрезан
            
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()
            
            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Окрашиваем по типу
                if any(word in line for word in ERROR_KEYWORDS):
                    print(f"❌ {line[:200]}")
                elif any(word in line for word in SUCCESS_KEYWORDS):
                    print(f"✅ {line[:200]}")
                elif any(word in line for word in WARNING_KEYWORDS):
                    print(f"⚠️ {line[:200]}")
                elif "🚀" in line:
                    print(f"🚀 {line[:200]}")
                elif "🔧" in line or "🔨" in line:
                    print(f"🔧 {line[:200]}")
                elif "📦" in line:
                    print(f"📦 {line[:200]}")
                elif "💜" in line or "❤️" in line:
                    print(f"💜 {line[:200]}")
                else:
                    print(f"   {line[:200]}")
            
            time.sleep(interval)
        except Exception as e:
            print(f"⚠️ Ошибка мониторинга логов: {e}")
            time.sleep(5)

def start_log_monitor(bot_dir=None, log_file="bot.log"):
    """
    Запустить мониторинг логов в потоке.
    
    Returns:
        threading.Thread
    """
    thread = threading.Thread(
        target=monitor_logs,
        args=(bot_dir, log_file),
        daemon=True
    )
    thread.start()
    print("📋 Мониторинг логов запущен")
    return thread

# ============================================================
# 5. СТАТИСТИКА ЛОГОВ
# ============================================================

def get_log_stats(bot_dir=None, log_file="bot.log"):
    """
    Получить статистику логов.
    
    Returns:
        dict: {exists, size_bytes, size_kb, lines, errors, last_modified}
    """
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    stats = {
        "exists": False,
        "size_bytes": 0,
        "size_kb": 0,
        "lines": 0,
        "errors": 0,
        "last_modified": None,
        "file": log_file,
    }
    
    log_path = os.path.join(bot_dir, log_file)
    
    try:
        if os.path.exists(log_path):
            stats["exists"] = True
            stats["size_bytes"] = os.path.getsize(log_path)
            stats["size_kb"] = round(stats["size_bytes"] / 1024, 2)
            stats["last_modified"] = datetime.fromtimestamp(
                os.path.getmtime(log_path)
            ).strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                stats["lines"] = len(lines)
            
            errors = find_errors_in_log(bot_dir, log_file)
            stats["errors"] = len(errors)
    except Exception as e:
        print(f"⚠️ Ошибка получения статистики логов: {e}")
    
    return stats

def format_log_stats(bot_dir=None, log_file="bot.log"):
    """Форматировать статистику логов"""
    stats = get_log_stats(bot_dir, log_file)
    
    lines = [
        f"📊 СТАТИСТИКА ЛОГОВ ({log_file}):",
        f"  📁 Файл существует: {'✅' if stats['exists'] else '❌'}",
        f"  💾 Размер: {stats['size_kb']}KB",
        f"  📄 Строк: {stats['lines']}",
        f"  ❌ Ошибок: {stats['errors']}",
    ]
    
    if stats["last_modified"]:
        lines.append(f"  🕐 Изменён: {stats['last_modified']}")
    
    return "\n".join(lines)

# ============================================================
# 6. ОБЩИЙ ОТЧЁТ ПО ВСЕМ ЛОГАМ
# ============================================================

def get_all_logs_stats(bot_dir=None):
    """Получить статистику по всем логам"""
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    all_logs = ["bot.log", "boot.log", "error.log"]
    results = {}
    
    for log_file in all_logs:
        results[log_file] = get_log_stats(bot_dir, log_file)
    
    return results

def format_all_logs_stats(bot_dir=None):
    """Форматировать статистику по всем логам"""
    all_stats = get_all_logs_stats(bot_dir)
    
    lines = ["📊 СТАТИСТИКА ВСЕХ ЛОГОВ:"]
    
    total_size = 0
    total_errors = 0
    
    for log_file, stats in all_stats.items():
        if stats["exists"]:
            lines.append(f"\n📄 {log_file}:")
            lines.append(f"  💾 {stats['size_kb']}KB, {stats['lines']} строк")
            lines.append(f"  ❌ Ошибок: {stats['errors']}")
            total_size += stats["size_kb"]
            total_errors += stats["errors"]
    
    lines.append("")
    lines.append(f"📊 ВСЕГО:")
    lines.append(f"  💾 Размер: {round(total_size, 2)}KB")
    lines.append(f"  ❌ Ошибок: {total_errors}")
    
    return "\n".join(lines)

# ============================================================
# 7. ОЧИСТКА И РОТАЦИЯ
# ============================================================

def rotate_logs(bot_dir=None):
    """
    Ротация логов: удалить старые > 7 дней.
    
    Returns:
        int: количество удалённых
    """
    if bot_dir is None:
        bot_dir = os.getcwd()
    
    deleted = 0
    now = time.time()
    week_seconds = 7 * 24 * 3600
    
    try:
        for filename in os.listdir(bot_dir):
            if not filename.endswith(".log"):
                continue
            
            filepath = os.path.join(bot_dir, filename)
            
            try:
                file_age = now - os.path.getmtime(filepath)
                
                if file_age > week_seconds:
                    os.remove(filepath)
                    deleted += 1
                    print(f"🗑 Удалён старый лог: {filename}")
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ Ошибка ротации логов: {e}")
    
    return deleted

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("📋 Модуль мониторинга логов загружен")
print(f"🔍 Ключевых слов ошибок: {len(ERROR_KEYWORDS)}")
print(f"📊 Максимум строк в логе: {MAX_LOG_LINES}")