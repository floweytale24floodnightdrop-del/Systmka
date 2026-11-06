"""Продвинутый анализатор ошибок — разбор, причины, решения, сохранение в БД"""

import os
import re
import json
import time
import hashlib
import traceback
import requests
from datetime import datetime
from collections import defaultdict

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

ERROR_DB_FILE = "error_database.json"
MAX_ERRORS = 500

# ============================================================
# 3. ДАННЫЕ
# ============================================================

error_database = {
    "errors": [],
    "patterns": {},
    "stats": {
        "total_errors": 0,
        "analyzed": 0,
        "fixed": 0,
        "failed": 0,
        "by_type": defaultdict(int),
        "by_file": defaultdict(int),
    },
    "solutions": [],
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def _convert_stats_for_json(stats):
    """Конвертировать defaultdict в обычный dict для JSON"""
    result = {}
    for k, v in stats.items():
        if isinstance(v, defaultdict):
            result[k] = dict(v)
        else:
            result[k] = v
    return result


def save_error_database():
    """Сохранить БД ошибок"""
    try:
        data = {
            "errors": error_database["errors"][-MAX_ERRORS:],
            "patterns": error_database["patterns"],
            "stats": _convert_stats_for_json(error_database["stats"]),
            "solutions": error_database["solutions"][-MAX_ERRORS:],
        }
        with open(ERROR_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения БД ошибок: {e}")
        return False


def load_error_database():
    """Загрузить БД ошибок"""
    global error_database
    try:
        if os.path.exists(ERROR_DB_FILE):
            with open(ERROR_DB_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                if isinstance(loaded.get("errors"), list):
                    error_database["errors"] = loaded["errors"]
                
                if isinstance(loaded.get("patterns"), dict):
                    error_database["patterns"] = loaded["patterns"]
                
                if isinstance(loaded.get("stats"), dict):
                    stats = loaded["stats"]
                    error_database["stats"]["total_errors"] = stats.get("total_errors", 0)
                    error_database["stats"]["analyzed"] = stats.get("analyzed", 0)
                    error_database["stats"]["fixed"] = stats.get("fixed", 0)
                    error_database["stats"]["failed"] = stats.get("failed", 0)
                    
                    if isinstance(stats.get("by_type"), dict):
                        error_database["stats"]["by_type"] = defaultdict(
                            int, stats["by_type"]
                        )
                    
                    if isinstance(stats.get("by_file"), dict):
                        error_database["stats"]["by_file"] = defaultdict(
                            int, stats["by_file"]
                        )
                
                if isinstance(loaded.get("solutions"), list):
                    error_database["solutions"] = loaded["solutions"]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON БД ошибок: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки БД ошибок: {e}")
        return False


load_error_database()

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def _clean_json_response(text):
    """Очистить ответ ИИ от markdown-обёртки"""
    if not text:
        return text
    
    text = text.strip()
    
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) >= 2:
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
    
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]
    
    return text.strip()

# ============================================================
# 6. СБОР ОШИБОК
# ============================================================

def collect_error(error_obj, context=None):
    """
    Собрать ошибку с полным контекстом.
    
    Args:
        error_obj: объект ошибки (Exception)
        context: дополнительный контекст (dict или str)
    
    Returns:
        dict: запись об ошибке
    """
    if error_obj is None:
        return None
    
    error_id = hashlib.md5(str(error_obj).encode()).hexdigest()[:12]
    
    # Проверяем дубликат
    for err in error_database["errors"]:
        if err.get("hash") == error_id:
            return err
    
    error_data = {
        "id": error_id,
        "type": error_obj.__class__.__name__,
        "message": str(error_obj),
        "file": None,
        "line": None,
        "column": None,
        "trace": traceback.format_exc(),
        "context": context,
        "analysis": None,
        "solution": None,
        "timestamp": datetime.now().isoformat(),
        "status": "new",
        "hash": error_id,
        "similar_to": [],
    }
    
    # Извлекаем информацию из traceback
    if hasattr(error_obj, "__traceback__") and error_obj.__traceback__:
        tb = traceback.extract_tb(error_obj.__traceback__)
        if tb:
            last_frame = tb[-1]
            error_data["file"] = last_frame.filename
            error_data["line"] = last_frame.lineno
    
    error_type = error_obj.__class__.__name__
    
    # Добавляем в БД
    error_database["errors"].append(error_data)
    
    if len(error_database["errors"]) > MAX_ERRORS:
        error_database["errors"] = error_database["errors"][-MAX_ERRORS:]
    
    error_database["stats"]["total_errors"] += 1
    error_database["stats"]["by_type"][error_type] += 1
    
    if error_data["file"]:
        error_database["stats"]["by_file"][error_data["file"]] += 1
    
    # Ищем похожие
    similar = find_similar_errors(error_data)
    error_data["similar_to"] = similar
    
    save_error_database()
    return error_data

# ============================================================
# 7. ПОИСК ПОХОЖИХ ОШИБОК
# ============================================================

def find_similar_errors(error_data):
    """
    Найти похожие ошибки в БД.
    
    Returns:
        list: список похожих
    """
    similar = []
    error_type = error_data.get("type")
    error_message = error_data.get("message", "")
    
    for err in error_database["errors"]:
        if err.get("id") == error_data.get("id"):
            continue
        
        if err.get("type") != error_type:
            continue
        
        similarity = 0.3
        err_message = err.get("message", "")
        
        if err_message == error_message:
            similarity += 0.5
        elif error_message and err_message:
            if (error_message[:50] in err_message
                    or err_message[:50] in error_message):
                similarity += 0.3
        
        if similarity >= 0.5:
            similar.append({
                "id": err.get("id"),
                "type": err.get("type"),
                "message": err_message[:100],
                "similarity": similarity,
                "solution": err.get("solution"),
            })
    
    return sorted(similar, key=lambda x: x["similarity"], reverse=True)[:5]

# ============================================================
# 8. АНАЛИЗ ОШИБКИ ЧЕРЕЗ ИИ
# ============================================================

def analyze_error_with_ai(error_data):
    """
    Глубокий анализ ошибки через ИИ.
    
    Returns:
        dict: анализ
    """
    if not error_data:
        return fallback_analysis({})
    
    key = _get_openrouter_key()
    if not key:
        return fallback_analysis(error_data)
    
    try:
        error_type = error_data.get("type", "")
        error_message = error_data.get("message", "")
        file_path = error_data.get("file", "")
        line = error_data.get("line", 0)
        trace = error_data.get("trace", "")
        
        prompt = (
            f"Проанализируй ошибку Python и предложи решение.\n\n"
            f"ТИП ОШИБКИ: {error_type}\n"
            f"СООБЩЕНИЕ: {error_message}\n"
            f"ФАЙЛ: {file_path}\n"
            f"СТРОКА: {line}\n\n"
            f"СТЕК ВЫЗОВОВ:\n{trace[:1500]}\n\n"
            "ОТВЕТЬ В ФОРМАТЕ:\n"
            "ПРИЧИНА: (кратко)\n"
            "РЕШЕНИЕ: (конкретно)\n"
            "ПРИМЕР: (код или команда)\n"
            "СЛОЖНОСТЬ: (легко/средне/сложно)\n"
            "ВРЕМЯ: (минуты)\n"
            "КАТЕГОРИЯ: (синтаксис/импорт/логика/тип/значение/доступ)"
        )
        
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
                            "Ты эксперт по Python и отладке. "
                            "Анализируй ошибки и предлагай решения."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 600,
                "temperature": 0.3,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0]['message']['content']
                analysis = parse_analysis(content)
                
                error_data["analysis"] = analysis
                error_data["status"] = "analyzed"
                error_database["stats"]["analyzed"] += 1
                save_error_database()
                
                return analysis
    except Exception as e:
        print(f"⚠️ Ошибка анализа через ИИ: {e}")
    
    return fallback_analysis(error_data)

# ============================================================
# 9. ПАРСИНГ АНАЛИЗА
# ============================================================

def parse_analysis(content):
    """
    Распарсить ответ ИИ.
    
    Returns:
        dict: анализ
    """
    analysis = {
        "cause": "",
        "solution": "",
        "example": "",
        "complexity": "средне",
        "time": 5,
        "category": "логика",
        "full_analysis": content,
        "timestamp": datetime.now().isoformat(),
    }
    
    if not content:
        return analysis
    
    cause_match = re.search(
        r'ПРИЧИНА:\s*(.+?)(?:\n|$)', content, re.IGNORECASE
    )
    if cause_match:
        analysis["cause"] = cause_match.group(1).strip()
    
    solution_match = re.search(
        r'РЕШЕНИЕ:\s*(.+?)(?:\n|$)', content, re.IGNORECASE | re.DOTALL
    )
    if solution_match:
        analysis["solution"] = solution_match.group(1).strip()
    
    example_match = re.search(
        r'ПРИМЕР:\s*(.+?)(?:\n|$)', content, re.IGNORECASE | re.DOTALL
    )
    if example_match:
        analysis["example"] = example_match.group(1).strip()
    
    complexity_match = re.search(
        r'СЛОЖНОСТЬ:\s*(.+?)(?:\n|$)', content, re.IGNORECASE
    )
    if complexity_match:
        analysis["complexity"] = complexity_match.group(1).strip().lower()
    
    time_match = re.search(r'ВРЕМЯ:\s*(\d+)', content, re.IGNORECASE)
    if time_match:
        try:
            analysis["time"] = int(time_match.group(1))
        except ValueError:
            pass
    
    category_match = re.search(
        r'КАТЕГОРИЯ:\s*(.+?)(?:\n|$)', content, re.IGNORECASE
    )
    if category_match:
        analysis["category"] = category_match.group(1).strip().lower()
    
    return analysis

# ============================================================
# 10. FALLBACK АНАЛИЗ
# ============================================================

def fallback_analysis(error_data):
    """
    Анализ ошибки без ИИ.
    
    Returns:
        dict: анализ
    """
    error_type = error_data.get("type", "")
    error_message = error_data.get("message", "")
    
    analysis = {
        "cause": "Неизвестная причина",
        "solution": "Проверьте код вручную",
        "example": "",
        "complexity": "средне",
        "time": 10,
        "category": "логика",
        "full_analysis": "",
        "timestamp": datetime.now().isoformat(),
    }
    
    # === SyntaxError ===
    if error_type == "SyntaxError":
        analysis["cause"] = "Синтаксическая ошибка в коде"
        analysis["solution"] = "Проверьте синтаксис в указанной строке"
        analysis["category"] = "синтаксис"
        analysis["complexity"] = "легко"
        
        if "unterminated string" in error_message:
            analysis["cause"] = "Незакрытая строка"
            analysis["solution"] = "Добавьте закрывающую кавычку"
        elif "invalid syntax" in error_message:
            analysis["cause"] = "Неверный синтаксис"
            analysis["solution"] = "Проверьте синтаксис в строке"
        elif "closing parenthesis" in error_message:
            analysis["cause"] = "Несовпадение скобок"
            analysis["solution"] = "Проверьте закрывающие скобки"
    
    # === NameError ===
    elif error_type == "NameError":
        match = re.search(r"name '(\w+)' is not defined", error_message)
        if match:
            name = match.group(1)
            analysis["cause"] = f"Переменная или функция '{name}' не определена"
            analysis["solution"] = (
                f"Определите '{name}' перед использованием или добавьте импорт"
            )
            analysis["category"] = "импорт"
            analysis["complexity"] = "легко"
    
    # === ImportError / ModuleNotFoundError ===
    elif error_type in ("ImportError", "ModuleNotFoundError"):
        match = re.search(r"No module named '(\w+)'", error_message)
        if match:
            module = match.group(1)
            analysis["cause"] = f"Модуль '{module}' не установлен"
            analysis["solution"] = f"Установите модуль: pip install {module}"
            analysis["category"] = "импорт"
            analysis["complexity"] = "легко"
    
    # === KeyError ===
    elif error_type == "KeyError":
        match = re.search(r"'(\w+)'", error_message)
        if match:
            key = match.group(1)
            analysis["cause"] = f"Ключ '{key}' не найден в словаре"
            analysis["solution"] = (
                f"Проверьте существование ключа или используйте dict.get('{key}')"
            )
            analysis["category"] = "значение"
            analysis["complexity"] = "средне"
    
    # === AttributeError ===
    elif error_type == "AttributeError":
        match = re.search(r"object has no attribute '(\w+)'", error_message)
        if match:
            attr = match.group(1)
            analysis["cause"] = f"Атрибут '{attr}' не существует"
            analysis["solution"] = (
                f"Проверьте наличие: hasattr(obj, '{attr}')"
            )
            analysis["category"] = "логика"
    
    # === TypeError ===
    elif error_type == "TypeError":
        analysis["cause"] = "Неверный тип данных"
        analysis["solution"] = "Проверьте типы данных перед операцией"
        analysis["category"] = "тип"
        
        if "NoneType" in error_message:
            analysis["cause"] = "Объект равен None"
            analysis["solution"] = "Проверьте, что объект не None"
    
    # === ValueError ===
    elif error_type == "ValueError":
        analysis["cause"] = "Неверное значение"
        analysis["solution"] = "Проверьте значение перед использованием"
        analysis["category"] = "значение"
    
    # === IndexError ===
    elif error_type == "IndexError":
        analysis["cause"] = "Индекс вне диапазона"
        analysis["solution"] = "Проверьте длину списка перед обращением"
        analysis["category"] = "логика"
    
    # === FileNotFoundError ===
    elif error_type == "FileNotFoundError":
        match = re.search(r"'(.*?)'", error_message)
        if match:
            filename = match.group(1)
            analysis["cause"] = f"Файл '{filename}' не найден"
            analysis["solution"] = (
                f"Проверьте существование файла или создайте его"
            )
            analysis["category"] = "доступ"
            analysis["complexity"] = "легко"
    
    # === PermissionError ===
    elif error_type == "PermissionError":
        analysis["cause"] = "Нет прав доступа"
        analysis["solution"] = "Проверьте права на файл/директорию"
        analysis["category"] = "доступ"
    
    return analysis

# ============================================================
# 11. ПОЛУЧЕНИЕ РЕШЕНИЯ
# ============================================================

def get_solution_for_error(error_data):
    """
    Получить решение для ошибки.
    
    Returns:
        str или None
    """
    if not error_data:
        return None
    
    if error_data.get("solution"):
        return error_data["solution"]
    
    # Пробуем найти в похожих
    similar = error_data.get("similar_to", [])
    for sim in similar:
        if sim.get("solution"):
            error_data["solution"] = sim["solution"]
            error_data["status"] = "resolved"
            save_error_database()
            return sim["solution"]
    
    # Пробуем через ИИ
    analysis = analyze_error_with_ai(error_data)
    if analysis and analysis.get("solution"):
        error_data["solution"] = analysis["solution"]
        error_data["status"] = "resolved"
        save_error_database()
        return analysis["solution"]
    
    return None

# ============================================================
# 12. СТАТИСТИКА
# ============================================================

def get_error_stats():
    """Получить статистику"""
    return {
        "total": error_database["stats"]["total_errors"],
        "analyzed": error_database["stats"]["analyzed"],
        "fixed": error_database["stats"]["fixed"],
        "failed": error_database["stats"]["failed"],
        "by_type": dict(error_database["stats"]["by_type"]),
        "by_file": dict(error_database["stats"]["by_file"]),
        "solutions": len(error_database["solutions"]),
        "patterns": len(error_database["patterns"]),
    }


def format_error_stats():
    """Форматировать статистику"""
    stats = get_error_stats()
    
    lines = [
        "🔬 СТАТИСТИКА АНАЛИЗАТОРА ОШИБОК:",
        f"📊 Всего ошибок: {stats['total']}",
        f"✅ Проанализировано: {stats['analyzed']}",
        f"🔧 Исправлено: {stats['fixed']}",
        f"❌ Не исправлено: {stats['failed']}",
        f"📚 Решений в базе: {stats['solutions']}",
        f"📊 Паттернов: {stats['patterns']}",
        "",
        "📋 ПО ТИПАМ:",
    ]
    
    for error_type, count in sorted(
        stats["by_type"].items(), key=lambda x: x[1], reverse=True
    )[:10]:
        lines.append(f"  • {error_type}: {count}")
    
    return "\n".join(lines)


def get_recent_errors(limit=10):
    """Получить последние ошибки"""
    return error_database["errors"][-limit:]


def get_errors_by_type(error_type):
    """Ошибки по типу"""
    return [
        e for e in error_database["errors"]
        if e.get("type") == error_type
    ]


def get_errors_by_file(file_path):
    """Ошибки по файлу"""
    return [
        e for e in error_database["errors"]
        if e.get("file") == file_path
    ]

# ============================================================
# 13. ИНТЕГРАЦИЯ С ERROR_FIXER
# ============================================================

def get_fix_for_error(error_obj, context=None):
    """
    Получить исправление для ошибки (для error_fixer).
    
    Returns:
        dict или None
    """
    error_data = collect_error(error_obj, context)
    if not error_data:
        return None
    
    solution = get_solution_for_error(error_data)
    
    if solution:
        return {
            "error_id": error_data["id"],
            "solution": solution,
            "analysis": error_data.get("analysis"),
            "category": error_data.get("analysis", {}).get("category", "логика"),
            "complexity": error_data.get("analysis", {}).get("complexity", "средне"),
        }
    
    return None

# ============================================================
# 14. ЗАГРУЗКА
# ============================================================

print("🔬 Продвинутый анализатор ошибок загружен (PC)")
print(f"📊 Всего ошибок в БД: {error_database['stats']['total_errors']}")
print(f"✅ Проанализировано: {error_database['stats']['analyzed']}")
print(f"🔧 Решений в базе: {len(error_database['solutions'])}")