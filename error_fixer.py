"""Автоматическое исправление ошибок — бэкапы, все типы ошибок, откат"""

import os
import sys
import re
import ast
import json
import time
import shutil
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

ERROR_LOG_FILE = "error_fixer_log.json"
FIXED_ERRORS_FILE = "fixed_errors.json"
FIX_STATS_FILE = "fix_stats.json"
BACKUP_DIR = "error_backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

# Файлы, которые НЕ трогаем (ОБНОВЛЕНО)
SYSTEM_FILES = {
    # Ядро
    "bot.py", "config.py", "config_network.py", "database.py",
    "system_prompt.py", "auto_import.py", "import_core.py",
    "import_modules.py", "import_loader.py",
    
    # Ошибки и защита
    "error_fixer.py", "error_analyzer.py", "error_analyzer_advanced.py",
    "error_reporter.py", "error_guardian.py", "module_fixer.py",
    "trash.py", "log_manager.py", "debug_changes.py",
    
    # Бот-обвязка
    "bot_handlers.py", "bot_loops.py", "bot_startup.py",
    "message_processor.py", "auto_start.py",
    
    # ИИ-ключи (чтобы не сломать)
    "ai_key_rotator.py", "ai_model_manager.py",
    "ai_request_handler.py", "ai_router.py",
    
    # Промты
    "prompt_notes_manager.py",
    
    # Самоулучшение
    "auto_improve.py", "auto_install.py",
}

# Папки для игнора
IGNORE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "trash", "personality_notes", "prompt_notes",
    "error_backups", "error_guardian_backups", "debug_logs",
    "auto_improve_backups", "temp_music", "voice_clones",
    "leaks",
}

# Максимальное число попыток
MAX_ATTEMPTS = 3

# ============================================================
# 3. ДАННЫЕ
# ============================================================

error_history = []
fixed_errors = {}

fix_stats = {
    "total_errors_found": 0,
    "total_fixed": 0,
    "total_failed": 0,
    "last_fix_time": None,
    "attempt_count": 0,
    "max_attempts": MAX_ATTEMPTS,
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def _save_json(file_path, data):
    """Безопасно сохранить JSON"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения {file_path}: {e}")
        return False


def _load_json(file_path, default):
    """Безопасно загрузить JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, type(default)):
                    return loaded
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {file_path}: {e}")
    return default


def save_fixed_errors():
    """Сохранить исправленные ошибки"""
    return _save_json(FIXED_ERRORS_FILE, fixed_errors)


def load_fixed_errors():
    """Загрузить исправленные ошибки"""
    global fixed_errors
    fixed_errors = _load_json(FIXED_ERRORS_FILE, {})
    return True


def save_error_history():
    """Сохранить историю ошибок"""
    return _save_json(ERROR_LOG_FILE, error_history)


def load_error_history():
    """Загрузить историю ошибок"""
    global error_history
    error_history = _load_json(ERROR_LOG_FILE, [])
    return True


def save_fix_stats():
    """Сохранить статистику исправлений в файл"""
    try:
        with open(FIX_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(fix_stats, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения fix_stats: {e}")
        return False


def load_fix_stats():
    """Загрузить статистику исправлений"""
    global fix_stats
    try:
        if os.path.exists(FIX_STATS_FILE):
            with open(FIX_STATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    fix_stats.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки fix_stats: {e}")
        return False


load_fixed_errors()
load_error_history()
load_fix_stats()

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def get_file_hash(file_path):
    """Получить хэш файла"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"⚠️ Ошибка хэша {file_path}: {e}")
        return None


def is_system_file(file_path):
    """Проверить, системный ли файл"""
    return os.path.basename(file_path) in SYSTEM_FILES


def _should_skip_dir(dir_path):
    """Проверить, нужно ли пропустить папку"""
    for ignored in IGNORE_DIRS:
        if ignored in dir_path:
            return True
    return False

# ============================================================
# 6. ПОИСК ОШИБОК
# ============================================================

def find_error_location(file_path, error_message):
    """Найти строки с ошибкой в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        error_lines = []
        search_terms = [
            error_message.split(':')[0] if ':' in error_message else error_message,
            error_message.split('"')[0] if '"' in error_message else error_message,
        ]
        
        for i, line in enumerate(lines):
            for term in search_terms:
                if term and term.strip() and term.strip() in line:
                    error_lines.append((i, line.strip()))
                    break
        
        return error_lines
    except Exception as e:
        print(f"⚠️ Ошибка поиска локации: {e}")
        return []


def find_all_errors():
    """Найти все синтаксические ошибки в проекте"""
    errors = []
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if not file.endswith('.py') or file.startswith('_'):
                continue
            
            file_path = os.path.join(root, file)
            
            if is_system_file(file_path):
                continue
            
            current_hash = get_file_hash(file_path)
            if file_path in fixed_errors:
                fixed_hash = fixed_errors[file_path].get("hash")
                if fixed_hash == current_hash:
                    continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                try:
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    errors.append({
                        'file': file_path,
                        'line': e.lineno or 0,
                        'column': e.offset or 0,
                        'error_type': 'SyntaxError',
                        'error_message': str(e),
                        'text': e.text or '',
                        'timestamp': datetime.now().isoformat(),
                        'hash': current_hash,
                        'context_lines': find_error_location(file_path, str(e)),
                    })
            except Exception as e:
                print(f"⚠️ Ошибка проверки {file_path}: {e}")
    
    return errors


def find_logic_errors(content, file_path):
    """Найти логические ошибки через ИИ"""
    if not content or len(content) < 100:
        return []
    
    key = _get_openrouter_key()
    if not key:
        return []
    
    errors = []
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты эксперт по Python. Найди потенциальные логические "
                            "ошибки в коде.\n"
                            "Ошибки: NameError, KeyError, AttributeError, "
                            "TypeError, ValueError, IndexError, "
                            "PermissionError, FileNotFoundError.\n"
                            "Ответь в формате JSON:\n"
                            '[{"line": число, "error_type": "тип", '
                            '"error_message": "описание"}]'
                        ),
                    },
                    {"role": "user", "content": f"Код:\n{content[:2000]}"},
                ],
                "max_tokens": 500,
                "temperature": 0.3,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content_result = data['choices'][0]['message']['content']
                
                content_result = content_result.strip()
                first = content_result.find("[")
                last = content_result.rfind("]")
                if first != -1 and last != -1:
                    content_result = content_result[first:last + 1]
                
                try:
                    parsed = json.loads(content_result)
                    if isinstance(parsed, list):
                        for err in parsed:
                            if isinstance(err, dict):
                                err['file'] = file_path
                                err['timestamp'] = datetime.now().isoformat()
                                err['hash'] = get_file_hash(file_path)
                                errors.append(err)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"⚠️ Ошибка поиска логических ошибок: {e}")
    
    return errors


def find_runtime_errors_from_logs(log_file="bot.log", lines=200):
    """Найти ошибки из логов"""
    errors = []
    
    if not os.path.exists(log_file):
        return errors
    
    error_keywords = [
        "Error", "Exception", "Traceback", "NameError",
        "ImportError", "KeyError", "AttributeError",
        "TypeError", "ModuleNotFoundError", "FileNotFoundError",
        "SyntaxError", "ValueError", "RuntimeError", "IndexError",
    ]
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        for i, line in enumerate(recent_lines):
            if not any(word in line for word in error_keywords):
                continue
            
            error_hash = hashlib.md5(line.encode()).hexdigest()
            if error_hash in fixed_errors:
                continue
            
            error_type = 'RuntimeError'
            for keyword in error_keywords:
                if keyword in line:
                    error_type = keyword
                    break
            
            errors.append({
                'file': log_file,
                'line': len(all_lines) - len(recent_lines) + i + 1,
                'error_type': error_type,
                'error_message': line.strip()[:200],
                'timestamp': datetime.now().isoformat(),
                'hash': error_hash,
            })
    except Exception as e:
        print(f"⚠️ Ошибка чтения логов: {e}")
    
    return errors

# ============================================================
# 7. ИСПРАВЛЕНИЕ
# ============================================================

def analyze_and_fix_line(line, error_type, error_message, context):
    """Проанализировать и исправить одну строку"""
    fixed_line = line
    description = "Исправлено"
    
    # === NameError ===
    if error_type == 'NameError':
        match = re.search(r"name '(\w+)' is not defined", error_message)
        if match:
            name = match.group(1)
            
            common_typos = {
                'randon': 'random',
                'requets': 'requests',
                'threding': 'threading',
                'datatime': 'datetime',
                'telebote': 'telebot',
            }
            for typo, correct in common_typos.items():
                if typo in fixed_line.lower():
                    fixed_line = fixed_line.replace(typo, correct)
                    return fixed_line, f"Исправлена опечатка '{typo}' → '{correct}'"
            
            imports = {
                'random': 'import random',
                'json': 'import json',
                'os': 'import os',
                'sys': 'import sys',
                'time': 'import time',
                're': 'import re',
                'requests': 'import requests',
                'threading': 'import threading',
                'telebot': 'import telebot',
            }
            if name in imports:
                return fixed_line, f"Нужно добавить: {imports[name]}"
    
    # === KeyError ===
    if error_type == 'KeyError':
        match = re.search(r"'(\w+)'", error_message)
        if match:
            key = match.group(1)
            if f'["{key}"]' in fixed_line or f"['{key}']" in fixed_line:
                fixed_line = fixed_line.replace(
                    f'["{key}"]', f'.get("{key}", "")'
                )
                fixed_line = fixed_line.replace(
                    f"['{key}']", f".get('{key}', '')"
                )
                return fixed_line, f"KeyError: .get('{key}')"
    
    # === SyntaxError ===
    if error_type == 'SyntaxError':
        if "unterminated string" in error_message:
            if fixed_line.count('"') % 2 != 0:
                fixed_line = fixed_line + '"'
                return fixed_line, "Добавлена закрывающая кавычка"
            if fixed_line.count("'") % 2 != 0:
                fixed_line = fixed_line + "'"
                return fixed_line, "Добавлена закрывающая кавычка"
        
        open_parens = fixed_line.count('(') - fixed_line.count(')')
        if open_parens > 0:
            fixed_line = fixed_line + ')' * open_parens
            return fixed_line, "Добавлены закрывающие скобки"
        
        open_brackets = fixed_line.count('[') - fixed_line.count(']')
        if open_brackets > 0:
            fixed_line = fixed_line + ']' * open_brackets
            return fixed_line, "Добавлены закрывающие скобки"
        
        open_braces = fixed_line.count('{') - fixed_line.count('}')
        if open_braces > 0:
            fixed_line = fixed_line + '}' * open_braces
            return fixed_line, "Добавлены закрывающие скобки"
    
    return None, "Не удалось исправить"


def fix_error_in_file(file_path, error_info):
    """Исправить ошибку в файле"""
    if not file_path or not os.path.exists(file_path):
        return False, "Файл не найден"
    
    if is_system_file(file_path):
        return False, "Системный файл — не трогаем"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_lines = f.readlines()
        
        error_line = error_info.get('line', 0)
        error_type = error_info.get('error_type', '')
        error_message = error_info.get('error_message', '')
        
        if error_line <= 0 or error_line > len(original_lines):
            return False, "Неверная строка"
        
        problem_line = original_lines[error_line - 1]
        context_start = max(0, error_line - 3)
        context_end = min(len(original_lines), error_line + 3)
        context = original_lines[context_start:context_end]
        
        fixed_line, fix_description = analyze_and_fix_line(
            problem_line, error_type, error_message, context
        )
        
        if not fixed_line or fixed_line == problem_line:
            return False, "Не удалось исправить строку"
        
        try:
            backup_path = os.path.join(
                BACKUP_DIR,
                f"{Path(file_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            )
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            print(f"⚠️ Ошибка бэкапа: {e}")
        
        original_lines[error_line - 1] = fixed_line
        new_content = ''.join(original_lines)
        
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return False, f"Ошибка в исправлении: {e}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        new_hash = get_file_hash(file_path)
        fixed_errors[file_path] = {
            "hash": new_hash,
            "fixed_at": datetime.now().isoformat(),
            "error": error_message,
            "fix_description": fix_description,
        }
        save_fixed_errors()
        
        # Обновляем статистику
        fix_stats["total_fixed"] = fix_stats.get("total_fixed", 0) + 1
        fix_stats["last_fix_time"] = datetime.now().isoformat()
        save_fix_stats()
        
        return True, fix_description
    
    except Exception as e:
        return False, str(e)

# ============================================================
# 8. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def auto_fix_all():
    """Найти и исправить все ошибки"""
    results = {
        'fixed': [],
        'failed': [],
        'errors_found': [],
        'stats': {
            'total': 0,
            'fixed_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
        },
    }
    
    syntax_errors = find_all_errors()
    log_errors = find_runtime_errors_from_logs()
    all_errors = syntax_errors + log_errors
    
    seen = set()
    unique_errors = []
    for error in all_errors:
        key = (
            f"{error.get('file', '')}:"
            f"{error.get('error_type', '')}:"
            f"{error.get('hash', '')}"
        )
        if key not in seen:
            seen.add(key)
            unique_errors.append(error)
    
    results['errors_found'] = unique_errors
    results['stats']['total'] = len(unique_errors)
    
    if not unique_errors:
        save_fix_stats()
        return results
    
    for error in unique_errors:
        file_path = error.get('file', '')
        
        if is_system_file(file_path):
            results['stats']['skipped_count'] += 1
            continue
        
        success, message = fix_error_in_file(file_path, error)
        
        if success:
            results['fixed'].append(file_path)
            results['stats']['fixed_count'] += 1
            
            error_history.append({
                'file': file_path,
                'error': error.get('error_message', '')[:200],
                'fix': message,
                'time': datetime.now().isoformat(),
            })
            save_error_history()
        else:
            results['failed'].append({
                'file': file_path,
                'reason': message,
            })
            results['stats']['failed_count'] += 1
    
    fix_stats["total_errors_found"] += results['stats']['total']
    fix_stats["total_failed"] += results['stats']['failed_count']
    
    if results['stats']['fixed_count'] > 0:
        fix_stats["last_fix_time"] = datetime.now().isoformat()
    
    fix_stats["attempt_count"] += 1
    
    # СОХРАНЯЕМ СТАТИСТИКУ
    save_fix_stats()
    
    return results

# ============================================================
# 9. ВАТЧДОГ
# ============================================================

def watchdog_loop():
    """Автоматический мониторинг ошибок"""
    while True:
        try:
            time.sleep(60)
            
            errors = find_all_errors()
            
            if errors and len(errors) <= 10:
                results = auto_fix_all()
                
                if results['stats']['fixed_count'] > 0:
                    print(f"🔧 Исправлено: {results['stats']['fixed_count']}")
                
                if results['stats']['failed_count'] > 0:
                    print(f"⚠️ Не исправлено: {results['stats']['failed_count']}")
        except Exception as e:
            print(f"⚠️ Ошибка в watchdog: {e}")
            time.sleep(30)

# ============================================================
# 10. СТАТИСТИКА
# ============================================================

def get_fix_stats():
    """Получить статистику"""
    return {
        "total_errors_found": fix_stats.get("total_errors_found", 0),
        "total_fixed": fix_stats.get("total_fixed", 0),
        "total_failed": fix_stats.get("total_failed", 0),
        "last_fix_time": fix_stats.get("last_fix_time"),
        "attempt_count": fix_stats.get("attempt_count", 0),
        "history_count": len(error_history),
        "fixed_files": len(fixed_errors),
    }


def format_fix_stats():
    """Форматировать статистику"""
    stats = get_fix_stats()
    
    lines = [
        "🔧 СТАТИСТИКА ИСПРАВЛЕНИЙ:",
        f"📊 Найдено ошибок: {stats['total_errors_found']}",
        f"✅ Исправлено: {stats['total_fixed']}",
        f"❌ Не исправлено: {stats['total_failed']}",
        f"📁 Файлов в истории: {stats['fixed_files']}",
        f"📝 Записей в истории: {stats['history_count']}",
        f"🔄 Попыток: {stats['attempt_count']}",
    ]
    
    if stats['last_fix_time']:
        lines.append(f"🕐 Последнее: {stats['last_fix_time'][:16]}")
    
    return "\n".join(lines)

# ============================================================
# 11. ЗАГРУЗКА
# ============================================================

print("🔧 Модуль исправления ошибок загружен (PC)")
print(f"📌 Системных файлов (не трогаем): {len(SYSTEM_FILES)}")
print(f"📁 Бэкапы: {BACKUP_DIR}/")
print(f"✅ Уже исправлено файлов: {len(fixed_errors)}")
print(f"📊 Исправлений в статистике: {fix_stats.get('total_fixed', 0)}")