"""Анализ ошибок через ИИ — причина, решения, категория, перевод RU/EN"""

import re
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from error_common import safe_print

try:
    from config import OPENROUTER_KEY, OPENROUTER_KEYS
except ImportError:
    OPENROUTER_KEY = None
    OPENROUTER_KEYS = []

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

REQUEST_TIMEOUT = 30
MAX_ANALYSIS_LENGTH = 3000

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 4. АНАЛИЗ ЧЕРЕЗ ИИ
# ============================================================

def analyze_error_with_ai(module_name, error_text, traceback_text=""):
    """
    Глубокий анализ ошибки через ИИ.
    
    Args:
        module_name: имя модуля
        error_text: текст ошибки
        traceback_text: traceback
    
    Returns:
        dict: {
            "error_en": str,
            "error_ru": str,
            "cause": str,
            "category": str,
            "solutions": list,
            "complexity": str,
            "full_analysis": str,
        }
    """
    key = _get_openrouter_key()
    if not key:
        return fallback_analysis(module_name, error_text)
    
    try:
        prompt = f"""Модуль '{module_name}' упал при импорте.

ОШИБКА:
{error_text}

TRACEBACK:
{traceback_text[:2000]}

Проанализируй ошибку. Ответь СТРОГО в формате:

ОШИБКА_EN: <оригинальный текст ошибки на английском>
ОШИБКА_RU: <перевод ошибки на русский>
ПРИЧИНА: <почему это произошло — 1-2 предложения>
КАТЕГОРИЯ: <синтаксис|импорт|логика|тип|значение|доступ|зависимость|другое>
СЛОЖНОСТЬ: <легко|средне|сложно>
РЕШЕНИЕ_1: <первое решение — конкретно>
РЕШЕНИЕ_2: <второе решение — конкретно>
РЕШЕНИЕ_3: <третье решение — конкретно>
"""
        
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
                            "Анализируй ошибки и давай конкретные решения."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0]['message']['content']
                return parse_ai_analysis(content, error_text)
    except Exception as e:
        safe_print(f"⚠️ Ошибка анализа через ИИ: {e}")
    
    return fallback_analysis(module_name, error_text)

# ============================================================
# 5. ПАРСИНГ ОТВЕТА ИИ
# ============================================================

def parse_ai_analysis(content, original_error):
    """Распарсить ответ ИИ"""
    result = {
        "error_en": original_error,
        "error_ru": "",
        "cause": "",
        "category": "другое",
        "solutions": [],
        "complexity": "средне",
        "full_analysis": content,
    }
    
    match = re.search(r'ОШИБКА_EN:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if match:
        result["error_en"] = match.group(1).strip()
    
    match = re.search(r'ОШИБКА_RU:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if match:
        result["error_ru"] = match.group(1).strip()
    
    match = re.search(r'ПРИЧИНА:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if match:
        result["cause"] = match.group(1).strip()
    
    match = re.search(r'КАТЕГОРИЯ:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if match:
        result["category"] = match.group(1).strip().lower()
    
    match = re.search(r'СЛОЖНОСТЬ:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if match:
        result["complexity"] = match.group(1).strip().lower()
    
    # Решения (1-5)
    for i in range(1, 6):
        match = re.search(
            rf'РЕШЕНИЕ_{i}:\s*(.+?)(?:\n|$)',
            content, re.IGNORECASE
        )
        if match:
            solution = match.group(1).strip()
            if solution and solution.lower() not in ("нет", "отсутствует"):
                result["solutions"].append(solution)
    
    return result

# ============================================================
# 6. FALLBACK АНАЛИЗ (БЕЗ ИИ)
# ============================================================

def fallback_analysis(module_name, error_text):
    """Анализ без ИИ"""
    error_lower = error_text.lower()
    
    result = {
        "error_en": error_text,
        "error_ru": "",
        "cause": "Неизвестная причина",
        "category": "другое",
        "solutions": [],
        "complexity": "средне",
        "full_analysis": "",
    }
    
    if "no module named" in error_lower:
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_text)
        module = match.group(1) if match else "?"
        result["cause"] = f"Модуль '{module}' не установлен"
        result["error_ru"] = f"Модуль '{module}' не найден"
        result["category"] = "зависимость"
        result["complexity"] = "легко"
        result["solutions"] = [
            f"Установить пакет: pip install {module}",
            f"Проверить правильность имени: {module}",
            f"Добавить в auto_install.py: \"{module}\": \"{module}\"",
        ]
    
    elif "cannot import name" in error_lower:
        match = re.search(r"cannot import name ['\"](\w+)['\"]", error_text)
        name = match.group(1) if match else "?"
        result["cause"] = f"Не удалось импортировать имя '{name}' из модуля"
        result["error_ru"] = f"Имя '{name}' не найдено в модуле"
        result["category"] = "импорт"
        result["solutions"] = [
            f"Проверить, что '{name}' определён в исходном модуле",
            f"Проверить циклический импорт",
            f"Проверить опечатку в имени '{name}'",
        ]
    
    elif "syntax" in error_lower:
        result["cause"] = "Синтаксическая ошибка в коде"
        result["error_ru"] = "Синтаксическая ошибка"
        result["category"] = "синтаксис"
        result["complexity"] = "легко"
        result["solutions"] = [
            "Проверить синтаксис в указанной строке",
            "Проверить незакрытые скобки/кавычки",
            "Запустить: python -m py_compile <файл>",
        ]
    
    elif "indentation" in error_lower:
        result["cause"] = "Неправильные отступы"
        result["error_ru"] = "Ошибка отступов"
        result["category"] = "синтаксис"
        result["complexity"] = "легко"
        result["solutions"] = [
            "Проверить отступы (должны быть 4 пробела)",
            "Не смешивать табы и пробелы",
        ]
    
    else:
        result["solutions"] = [
            "Проверить код модуля вручную",
            "Запустить модуль отдельно: python -c \"import <модуль>\"",
            "Попробовать исправить через ИИ",
        ]
    
    return result

# ============================================================
# 7. ФОРМАТИРОВАНИЕ ОТЧЁТА
# ============================================================

def format_error_report(module_name, error_text, traceback_text, analysis):
    """Сформировать полный отчёт об ошибке"""
    lines = []
    lines.append("")
    lines.append("═" * 70)
    lines.append(f"❌ ОШИБКА ИМПОРТА: {module_name}")
    lines.append("═" * 70)
    lines.append("")
    
    # Тип ошибки
    error_type = "ImportError"
    if "ModuleNotFoundError" in error_text:
        error_type = "ModuleNotFoundError"
    elif "SyntaxError" in error_text:
        error_type = "SyntaxError"
    elif "IndentationError" in error_text:
        error_type = "IndentationError"
    elif "NameError" in error_text:
        error_type = "NameError"
    elif "AttributeError" in error_text:
        error_type = "AttributeError"
    
    lines.append(f"📋 ТИП: {error_type}")
    lines.append("")
    
    # Ошибка EN
    lines.append("🔴 ОШИБКА (EN):")
    lines.append(f"   {analysis.get('error_en', error_text)[:300]}")
    lines.append("")
    
    # Ошибка RU
    error_ru = analysis.get("error_ru", "")
    if error_ru:
        lines.append("🔴 ОШИБКА (RU):")
        lines.append(f"   {error_ru[:300]}")
        lines.append("")
    
    # Traceback
    if traceback_text:
        lines.append("📚 TRACEBACK (последние 5 строк):")
        tb_lines = traceback_text.strip().split("\n")[-5:]
        for line in tb_lines:
            lines.append(f"   {line[:150]}")
        lines.append("")
    
    # Анализ
    lines.append("🔍 АНАЛИЗ:")
    lines.append(f"   Причина: {analysis.get('cause', '?')}")
    lines.append(f"   Категория: {analysis.get('category', '?')}")
    lines.append(f"   Сложность: {analysis.get('complexity', '?')}")
    lines.append("")
    
    # Решения
    solutions = analysis.get("solutions", [])
    if solutions:
        lines.append(f"💡 РЕШЕНИЯ ({len(solutions)}):")
        for i, solution in enumerate(solutions, 1):
            lines.append(f"   {i}. {solution}")
        lines.append("")
    
    lines.append("═" * 70)
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🛡️ error_analyzer_ai загружен")
print(f"🔑 OpenRouter: {'✅' if _get_openrouter_key() else '❌'}")