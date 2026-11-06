"""Анализ ошибок и предложение исправлений (без ИИ)"""

import re

# ============================================================
# 1. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def analyze_error(error_type, error_message, content=None):
    """
    Проанализировать ошибку и вернуть структурированные данные.
    
    Args:
        error_type: тип ошибки (NameError, ImportError...)
        error_message: сообщение ошибки
        content: код (опционально)
    
    Returns:
        dict: анализ
    """
    analysis = {
        "type": error_type or "Unknown",
        "message": error_message or "",
        "location": None,
        "cause": None,
        "suggestions": [],
        "line": None,
        "column": None,
    }
    
    if not error_message:
        analysis["cause"] = "Нет сообщения об ошибке"
        analysis["suggestions"].append("Проверьте логи")
        return analysis
    
    # Извлекаем номер строки
    line_match = re.search(r'line (\d+)', error_message)
    if line_match:
        try:
            analysis["line"] = int(line_match.group(1))
        except ValueError:
            pass
    
    # === NameError ===
    if error_type == "NameError":
        _analyze_name_error(analysis, error_message)
    
    # === ImportError / ModuleNotFoundError ===
    elif error_type in ("ImportError", "ModuleNotFoundError"):
        _analyze_import_error(analysis, error_message)
    
    # === KeyError ===
    elif error_type == "KeyError":
        _analyze_key_error(analysis, error_message)
    
    # === AttributeError ===
    elif error_type == "AttributeError":
        _analyze_attribute_error(analysis, error_message)
    
    # === TypeError ===
    elif error_type == "TypeError":
        analysis["cause"] = "Неверный тип данных"
        analysis["suggestions"].append(
            "Проверьте типы данных перед операцией"
        )
        analysis["suggestions"].append(
            "Добавьте преобразование типов"
        )
        
        if "NoneType" in error_message:
            analysis["cause"] = "Объект равен None"
            analysis["suggestions"].append(
                "Проверьте, что объект не None перед использованием"
            )
    
    # === ValueError ===
    elif error_type == "ValueError":
        analysis["cause"] = "Неверное значение"
        analysis["suggestions"].append(
            "Проверьте значение перед использованием"
        )
        analysis["suggestions"].append(
            "Добавьте валидацию входных данных"
        )
    
    # === IndexError ===
    elif error_type == "IndexError":
        analysis["cause"] = "Индекс вне диапазона"
        analysis["suggestions"].append(
            "Проверьте длину списка перед обращением"
        )
        analysis["suggestions"].append(
            "Используйте try-except для доступа"
        )
    
    # === FileNotFoundError ===
    elif error_type == "FileNotFoundError":
        _analyze_file_error(analysis, error_message)
    
    # === PermissionError ===
    elif error_type == "PermissionError":
        analysis["cause"] = "Нет прав доступа"
        analysis["suggestions"].append(
            "Проверьте права на файл/директорию"
        )
        analysis["suggestions"].append(
            "Запустите с правами администратора"
        )
    
    # === SyntaxError ===
    elif error_type == "SyntaxError":
        _analyze_syntax_error(analysis, error_message)
    
    # === RuntimeError ===
    elif error_type == "RuntimeError":
        analysis["cause"] = "Ошибка выполнения"
        analysis["suggestions"].append(
            "Проверьте логику в указанной строке"
        )
    
    # === Неизвестный тип ===
    else:
        analysis["cause"] = "Неизвестная ошибка"
        analysis["suggestions"].append("Проверьте код вручную")
    
    return analysis

# ============================================================
# 2. АНАЛИЗАТОРЫ ПО ТИПАМ
# ============================================================

def _analyze_name_error(analysis, error_message):
    """Анализ NameError"""
    match = re.search(r"name '(\w+)' is not defined", error_message)
    if not match:
        return
    
    name = match.group(1)
    analysis["location"] = name
    analysis["cause"] = f"Переменная или функция '{name}' не определена"
    
    imports = {
        "random": "import random",
        "json": "import json",
        "os": "import os",
        "sys": "import sys",
        "time": "import time",
        "re": "import re",
        "requests": "import requests",
        "threading": "import threading",
        "telebot": "import telebot",
        "pytz": "import pytz",
    }
    
    if name in imports:
        analysis["suggestions"].append(
            f"Добавить импорт: {imports[name]}"
        )
    else:
        analysis["suggestions"].append(
            f"Определить переменную '{name}' перед использованием"
        )


def _analyze_import_error(analysis, error_message):
    """Анализ ImportError"""
    match = re.search(r"No module named '(\w+)'", error_message)
    if not match:
        return
    
    module = match.group(1)
    analysis["location"] = module
    analysis["cause"] = f"Модуль '{module}' не установлен"
    analysis["suggestions"].append(
        f"Установить модуль: pip install {module}"
    )
    analysis["suggestions"].append(
        "Или добавить try-except для импорта"
    )


def _analyze_key_error(analysis, error_message):
    """Анализ KeyError"""
    match = re.search(r"'(\w+)'", error_message)
    if not match:
        return
    
    key = match.group(1)
    analysis["location"] = key
    analysis["cause"] = f"Ключ '{key}' не найден в словаре"
    analysis["suggestions"].append(
        f"Проверить существование ключа: if '{key}' in dict"
    )
    analysis["suggestions"].append(
        f"Использовать dict.get('{key}')"
    )


def _analyze_attribute_error(analysis, error_message):
    """Анализ AttributeError"""
    match = re.search(r"object has no attribute '(\w+)'", error_message)
    if not match:
        return
    
    attr = match.group(1)
    analysis["location"] = attr
    analysis["cause"] = f"Атрибут '{attr}' не существует"
    analysis["suggestions"].append(
        f"Проверить наличие: hasattr(obj, '{attr}')"
    )
    analysis["suggestions"].append(f"Добавить атрибут '{attr}'")


def _analyze_file_error(analysis, error_message):
    """Анализ FileNotFoundError"""
    match = re.search(r"'(.*?)'", error_message)
    if not match:
        return
    
    filename = match.group(1)
    analysis["location"] = filename
    analysis["cause"] = f"Файл '{filename}' не найден"
    analysis["suggestions"].append(
        f"Проверить существование: os.path.exists('{filename}')"
    )
    analysis["suggestions"].append("Создать файл если его нет")


def _analyze_syntax_error(analysis, error_message):
    """Анализ SyntaxError"""
    analysis["cause"] = "Синтаксическая ошибка в коде"
    
    if "unterminated string" in error_message:
        analysis["suggestions"].append("Закрыть строку кавычкой")
    elif "invalid syntax" in error_message:
        analysis["suggestions"].append(
            "Проверить синтаксис в указанной строке"
        )
    elif "unexpected indent" in error_message:
        analysis["suggestions"].append("Проверить отступы")
    elif "closing parenthesis" in error_message:
        analysis["suggestions"].append("Проверить закрывающие скобки")
    else:
        analysis["suggestions"].append(
            "Проверить синтаксис в указанной строке"
        )

# ============================================================
# 3. ПОИСК МЕСТА ОШИБКИ
# ============================================================

def find_error_location(file_path, error_message):
    """
    Найти точное место ошибки в файле.
    
    Args:
        file_path: путь к файлу
        error_message: сообщение ошибки
    
    Returns:
        list: [(line_index, text), ...]
    """
    if not file_path or not error_message:
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        error_lines = []
        
        # Извлекаем ключевое слово для поиска
        error_parts = error_message.split(':')
        search_term = error_parts[0] if error_parts else error_message
        
        # Убираем кавычки
        search_term = search_term.strip().strip('"\'')
        
        if not search_term:
            return []
        
        for i, line in enumerate(lines):
            if search_term in line:
                error_lines.append((i, line.strip()))
        
        return error_lines
    except Exception as e:
        print(f"⚠️ Ошибка поиска локации: {e}")
        return []

# ============================================================
# 4. ПРЕДЛОЖЕНИЕ ИСПРАВЛЕНИЙ
# ============================================================

def suggest_fix(error_type, error_message, content=None):
    """
    Предложить исправление на основе анализа.
    
    Совместимо с import_core:
    - Принимает либо (error_type, error_message)
    - Либо (analysis_dict, content)
    - Либо (error_type, error_message, content)
    
    Returns:
        dict: анализ с предложениями
    """
    # Случай 1: первый аргумент — dict (analysis)
    if isinstance(error_type, dict):
        analysis = error_type
        content = error_message if isinstance(error_message, str) else content
        return analysis
    
    # Случай 2: обычный вызов
    return analyze_error(error_type, error_message, content)


def suggest_fix_for_content(content, analysis=None):
    """
    Предложить исправление кода на основе анализа.
    
    Args:
        content: исходный код
        analysis: dict анализа (опционально)
    
    Returns:
        str: исправленный код
    """
    if not content:
        return content
    
    if not analysis or not isinstance(analysis, dict):
        return content
    
    error_type = analysis.get("type", "")
    location = analysis.get("location", "")
    
    fixed = content
    
    # === NameError ===
    if error_type == "NameError" and location:
        imports = {
            "random": "import random",
            "json": "import json",
            "os": "import os",
            "sys": "import sys",
            "time": "import time",
            "re": "import re",
            "requests": "import requests",
            "threading": "import threading",
            "telebot": "import telebot",
        }
        if location in imports and imports[location] not in content:
            fixed = imports[location] + '\n' + fixed
    
    # === KeyError ===
    elif error_type == "KeyError" and location:
        pattern = r"([a-zA-Z_]\w*)\['" + re.escape(location) + r"'\]"
        replacement = r"\1.get('" + location + r"')"
        fixed = re.sub(pattern, replacement, fixed)
    
    # === AttributeError ===
    elif error_type == "AttributeError" and location:
        pattern = r"([a-zA-Z_]\w*)\." + re.escape(location)
        replacement = r"hasattr(\1, '" + location + "') and \\1." + location
        fixed = re.sub(pattern, replacement, fixed)
    
    # === FileNotFoundError ===
    elif error_type == "FileNotFoundError" and location:
        pattern = r"open\('" + re.escape(location) + r"'"
        replacement = (
            r"open('" + location + "' if os.path.exists('" +
            location + "') else ''"
        )
        fixed = re.sub(pattern, replacement, fixed)
    
    # === SyntaxError ===
    elif error_type == "SyntaxError":
        # Двойное равно
        fixed = re.sub(r'([^=!<>])=([^=])', r'\1==\2', fixed)
    
    return fixed

# ============================================================
# 5. ФОРМАТИРОВАНИЕ
# ============================================================

def format_analysis(analysis):
    """Форматировать анализ ошибки"""
    if not analysis:
        return "❌ Нет анализа"
    
    lines = [
        "🔬 АНАЛИЗ ОШИБКИ:",
        f"  Тип: {analysis.get('type', '?')}",
    ]
    
    if analysis.get("line"):
        lines.append(f"  Строка: {analysis['line']}")
    
    if analysis.get("cause"):
        lines.append(f"  Причина: {analysis['cause']}")
    
    suggestions = analysis.get("suggestions", [])
    if suggestions:
        lines.append("  Решения:")
        for s in suggestions:
            lines.append(f"    • {s}")
    
    return "\n".join(lines)

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("🔬 Модуль анализа ошибок загружен (PC)")
print(f"📋 Типов ошибок: 10")
print(f"🔧 Функций: analyze_error, suggest_fix, find_error_location")