"""Анализатор файлов — PC-версия"""

import os
import re
import ast
import json
import time
import threading
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

# Что игнорировать при анализе
IGNORE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "trash", "personality_notes", "prompt_notes",
    "error_backups", "error_guardian_backups", "debug_logs",
    "temp_music", "voice_clones", "node_modules",
}

# Максимальный размер файла для чтения (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Поддерживаемые расширения
SUPPORTED_EXTENSIONS = {
    ".py", ".json", ".txt", ".md", ".log", ".cfg", ".ini",
    ".yaml", ".yml", ".toml", ".xml", ".html", ".css", ".js",
}

# ============================================================
# 2. ЧТЕНИЕ ФАЙЛОВ
# ============================================================

def read_any_file(filename):
    """
    Прочитать файл любого типа.
    
    Args:
        filename: путь к файлу
    
    Returns:
        str или bytes или None
    """
    if not os.path.exists(filename):
        return None
    
    try:
        # Проверяем размер
        if os.path.getsize(filename) > MAX_FILE_SIZE:
            print(f"⚠️ Файл слишком большой: {filename}")
            return None
        
        ext = os.path.splitext(filename)[1].lower()
        
        # Текстовые файлы
        if ext in SUPPORTED_EXTENSIONS or ext == "":
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # Пробуем другую кодировку
                try:
                    with open(filename, "r", encoding="cp1251") as f:
                        return f.read()
                except Exception:
                    pass
        
        # Бинарные файлы
        with open(filename, "rb") as f:
            return f.read()
    
    except PermissionError:
        print(f"⚠️ Нет доступа к файлу: {filename}")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка чтения {filename}: {e}")
        return None

def read_file_safe(filename, max_size=100000):
    """Прочитать файл с ограничением размера"""
    content = read_any_file(filename)
    if isinstance(content, str) and len(content) > max_size:
        return content[:max_size]
    return content

# ============================================================
# 3. АНАЛИЗ ФАЙЛА
# ============================================================

def analyze_file_content(filename):
    """
    Проанализировать содержимое файла.
    
    Returns:
        dict или None
    """
    content = read_any_file(filename)
    if content is None:
        return None
    
    analysis = {
        "filename": filename,
        "size": len(content) if isinstance(content, str) else len(content),
        "type": "text" if isinstance(content, str) else "binary",
        "lines": len(content.split("\n")) if isinstance(content, str) else 0,
    }
    
    if isinstance(content, str):
        # Анализ Python-кода
        analysis["functions"] = re.findall(r'def\s+(\w+)\s*\(', content)
        analysis["classes"] = re.findall(r'class\s+(\w+)\s*[\(:]', content)
        analysis["imports"] = re.findall(r'^\s*import\s+(\w+)', content, re.MULTILINE)
        analysis["from_imports"] = re.findall(r'^\s*from\s+(\w+)\s+import', content, re.MULTILINE)
        
        # Проверка синтаксиса
        if filename.endswith(".py"):
            try:
                ast.parse(content)
                analysis["syntax"] = "OK"
            except SyntaxError as e:
                analysis["syntax"] = f"ERROR: {e}"
        
        # Проверка JSON
        if filename.endswith(".json"):
            try:
                json.loads(content)
                analysis["json_valid"] = True
            except json.JSONDecodeError as e:
                analysis["json_valid"] = False
                analysis["json_error"] = str(e)
    
    return analysis

def analyze_all_files(directory="."):
    """
    Проанализировать все файлы в папке.
    
    Returns:
        dict: {filename: analysis}
    """
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # Пропускаем игнорируемые папки
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                filepath = os.path.join(root, filename)
                analysis = analyze_file_content(filepath)
                if analysis:
                    results[filepath] = analysis
    
    return results

# ============================================================
# 4. ПОИСК ОШИБОК
# ============================================================

def find_errors_in_files(directory="."):
    """
    Найти ошибки во всех .py файлах.
    
    Returns:
        list: [{file, error, type}, ...]
    """
    errors = []
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for filename in files:
            if not filename.endswith(".py"):
                continue
            
            filepath = os.path.join(root, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            # Синтаксические ошибки
            try:
                ast.parse(content, filename=filepath)
            except SyntaxError as e:
                errors.append({
                    "file": filepath,
                    "error": str(e),
                    "type": "SyntaxError",
                    "line": e.lineno,
                })
    
    return errors

# ============================================================
# 5. СТАТИСТИКА
# ============================================================

def get_file_stats(directory="."):
    """
    Статистика файлов.
    
    Returns:
        dict: {total_files, total_functions, total_classes, total_lines, errors}
    """
    files = analyze_all_files(directory)
    
    total_functions = 0
    total_classes = 0
    total_lines = 0
    
    for filepath, analysis in files.items():
        total_functions += len(analysis.get("functions", []))
        total_classes += len(analysis.get("classes", []))
        total_lines += analysis.get("lines", 0)
    
    errors = find_errors_in_files(directory)
    
    return {
        "total_files": len(files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_lines": total_lines,
        "errors": errors,
    }

def format_file_stats(directory="."):
    """Форматировать статистику файлов"""
    stats = get_file_stats(directory)
    
    lines = [
        "📊 СТАТИСТИКА ФАЙЛОВ:",
        f"  📁 Файлов: {stats['total_files']}",
        f"  📝 Функций: {stats['total_functions']}",
        f"  🏛 Классов: {stats['total_classes']}",
        f"  📄 Строк: {stats['total_lines']}",
    ]
    
    if stats["errors"]:
        lines.append("")
        lines.append(f"❌ Ошибки ({len(stats['errors'])}):")
        for err in stats["errors"][:10]:
            lines.append(f"  • {err['file']}:{err.get('line', '?')}")
            lines.append(f"    {err['error'][:100]}")
        
        if len(stats["errors"]) > 10:
            lines.append(f"  ... и ещё {len(stats['errors']) - 10}")
    else:
        lines.append("")
        lines.append("✅ Ошибок нет")
    
    return "\n".join(lines)

# ============================================================
# 6. НАБЛЮДЕНИЕ ЗА ФАЙЛАМИ
# ============================================================

_watcher_thread = None
_watcher_stop = threading.Event()

def watch_files_loop(directory=".", interval=5, callback=None):
    """
    Наблюдение за изменениями файлов.
    
    Args:
        directory: папка для наблюдения
        interval: интервал проверки в секундах
        callback: функция, которая вызывается при изменении
                  callback(filepath, event_type)
    """
    last_modified = {}
    
    # Первый проход — запоминаем состояние
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                try:
                    last_modified[filepath] = os.path.getmtime(filepath)
                except Exception:
                    pass
    
    while not _watcher_stop.is_set():
        if _watcher_stop.wait(interval):
            break
        
        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for filename in files:
                    if not filename.endswith(".py"):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    
                    try:
                        mtime = os.path.getmtime(filepath)
                    except Exception:
                        continue
                    
                    if filepath not in last_modified:
                        # Новый файл
                        last_modified[filepath] = mtime
                        if callback:
                            callback(filepath, "created")
                    elif mtime != last_modified[filepath]:
                        # Изменён
                        last_modified[filepath] = mtime
                        if callback:
                            callback(filepath, "modified")
            
            # Проверяем удалённые файлы
            existing = set(last_modified.keys())
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for filename in files:
                    if filename.endswith(".py"):
                        existing.discard(os.path.join(root, filename))
            
            for deleted in existing:
                del last_modified[deleted]
                if callback:
                    callback(deleted, "deleted")
        
        except Exception as e:
            print(f"⚠️ Ошибка в watch_files_loop: {e}")

def start_watcher(directory=".", callback=None):
    """
    Запустить наблюдение за файлами в фоне.
    
    Returns:
        threading.Thread
    """
    global _watcher_thread
    
    if _watcher_thread and _watcher_thread.is_alive():
        return _watcher_thread
    
    _watcher_stop.clear()
    _watcher_thread = threading.Thread(
        target=watch_files_loop,
        args=(directory, 5, callback),
        daemon=True
    )
    _watcher_thread.start()
    print(f"👁 Наблюдение за файлами запущено: {directory}")
    return _watcher_thread

def stop_watcher():
    """Остановить наблюдение"""
    _watcher_stop.set()
    if _watcher_thread:
        _watcher_thread.join(timeout=5)
    print("👁 Наблюдение за файлами остановлено")

# ============================================================
# 7. ПОИСК ПО СОДЕРЖИМОМУ
# ============================================================

def search_in_files(pattern, directory=".", file_ext=".py"):
    """
    Поиск по содержимому файлов.
    
    Args:
        pattern: регулярное выражение или строка
        directory: папка для поиска
        file_ext: расширение файлов
    
    Returns:
        list: [{file, line, text}, ...]
    """
    results = []
    
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        # Если не regex — ищем как строку
        regex = re.compile(re.escape(pattern), re.IGNORECASE)
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for filename in files:
            if file_ext and not filename.endswith(file_ext):
                continue
            
            filepath = os.path.join(root, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file": filepath,
                                "line": line_num,
                                "text": line.strip()[:150],
                            })
            except Exception:
                continue
    
    return results

def format_search_results(results, limit=20):
    """Форматировать результаты поиска"""
    if not results:
        return "🔍 Ничего не найдено"
    
    lines = [f"🔍 Найдено совпадений: {len(results)}", ""]
    
    for r in results[:limit]:
        lines.append(f"📄 {r['file']}:{r['line']}")
        lines.append(f"   {r['text']}")
        lines.append("")
    
    if len(results) > limit:
        lines.append(f"... и ещё {len(results) - limit}")
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🔍 Анализатор файлов загружен (PC)")
print(f"📁 Игнорируется папок: {len(IGNORE_DIRS)}")
print(f"📄 Поддерживаемых расширений: {len(SUPPORTED_EXTENSIONS)}")
print(f"💾 Макс. размер файла: {MAX_FILE_SIZE // (1024 * 1024)}MB")