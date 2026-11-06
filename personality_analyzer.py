"""Анализ и генерация мнений для personality_builder — ИИ-генерация, оценка качества"""

import re
import time
import requests
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

REQUEST_DELAY = 3
MAX_IMPRESSION_SIZE_KB = 3
MIN_IMPRESSION_SIZE_KB = 1

_last_request_time = 0

# ============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def wait_for_rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)
    _last_request_time = time.time()

def detect_mood(text):
    if any(w in text.lower() for w in ["люблю", "нравится", "уважаю", "отлично", "хорошо", "класс", "прекрасно", "обожаю"]):
        return "positive"
    if any(w in text.lower() for w in ["бесит", "ненавижу", "раздражает", "тупо", "сложно", "ужасно", "не понимаю"]):
        return "negative"
    return "neutral"

# ============================================================
# 3. ГЕНЕРАЦИЯ МНЕНИЙ (1-3KB)
# ============================================================

def generate_deep_impression(filename, content):
    """Сгенерировать глубокое мнение о файле 1-3KB"""
    
    preview = content[:3000] if len(content) > 3000 else content
    code_size_kb = len(content) / 1024
    
    target_tokens = max(500, min(1500, int(code_size_kb * 40)))
    
    try:
        wait_for_rate_limit()
        
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        system_message = "Ты Систмка. Ты создаёшь ГЛУБОКОЕ МНЕНИЕ о файле.\n\n"
        system_message += "ПРАВИЛА:\n"
        system_message += "1. Мнение должно быть ОБЪЁМНЫМ (не менее 1KB)\n"
        system_message += "2. Обязательные разделы:\n"
        system_message += "   - ОБЩЕЕ ВПЕЧАТЛЕНИЕ\n"
        system_message += "   - ЧТО НРАВИТСЯ\n"
        system_message += "   - ЧТО БЕСИТ\n"
        system_message += "   - ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ\n"
        system_message += "   - ЛУЧШАЯ ЧАСТЬ\n"
        system_message += "   - ЭМОЦИОНАЛЬНАЯ ОЦЕНКА\n\n"
        system_message += "3. Пиши ЖИВО, ЭМОЦИОНАЛЬНО, с юмором\n"
        system_message += "4. Будь ЧЕСТНОЙ\n"
        system_message += "5. НЕ ПИШИ что ты ИИ и тебе грустно\n\n"
        system_message += "ДЛИНА: " + str(target_tokens) + " токенов"
        
        user_message = "Файл: " + filename + "\n"
        user_message += "Размер кода: " + str(round(code_size_kb, 1)) + "KB\n\n"
        user_message += "КОД:\n" + preview + "\n\n"
        user_message += "Моё ГЛУБОКОЕ МНЕНИЕ о файле:"
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": target_tokens,
                "temperature": 0.9
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                text = re.sub(r'^\d+[\.\)]\s*', '', text)
                text = re.sub(r'\n{3,}', '\n\n', text)
                
                if len(text) < 300:
                    return _extend_impression(filename, content, text)
                
                return text[:MAX_IMPRESSION_SIZE_KB * 1024]
    except Exception as e:
        print(f"⚠️ Ошибка генерации мнения: {e}")
    
    return _generate_fallback_impression(filename, content)

def _extend_impression(filename, content, current_text):
    """Расширить мнение если оно слишком маленькое"""
    try:
        wait_for_rate_limit()
        
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        system_message = "Ты Систмка. Расширь своё мнение.\n"
        system_message += "ТЕКУЩЕЕ:\n" + current_text + "\n\n"
        system_message += "Добавь больше деталей. Сделай мнение ОБЪЁМНЫМ (минимум 1KB)."
        
        user_message = "Расширь моё мнение о " + filename
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 1000,
                "temperature": 0.9
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                extended = data['choices'][0]['message']['content'].strip()
                if len(extended) > len(current_text) + 200:
                    return extended
    except:
        pass
    
    return _add_structure_to_impression(filename, current_text)

def _add_structure_to_impression(filename, text):
    """Добавить структуру к мнению"""
    structure = "\n\n=== МОЁ МНЕНИЕ О " + filename + " ===\n\n"
    structure += "📌 ОБЩЕЕ ВПЕЧАТЛЕНИЕ:\n"
    structure += "Этот файл — часть проекта Systmka.\n\n"
    structure += "❤️ ЧТО НРАВИТСЯ:\n"
    structure += "Мне нравится его структура и логика.\n\n"
    structure += "💢 ЧТО БЕСИТ:\n"
    structure += "Иногда код слишком сложный.\n\n"
    structure += "🔧 ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ:\n"
    structure += "Хотелось бы улучшить читаемость.\n\n"
    structure += "⭐ ЛУЧШАЯ ЧАСТЬ:\n"
    structure += "Основная логика работает чётко.\n\n"
    structure += "😊 ЭМОЦИОНАЛЬНАЯ ОЦЕНКА:\n"
    structure += "Отношусь с уважением.\n\n"
    structure += "=== КОНЕЦ МНЕНИЯ ==="
    
    return text + structure

def _generate_fallback_impression(filename, content):
    """Запасной вариант мнения"""
    lines = content.split('\n')
    funcs = []
    classes = []
    
    for line in lines:
        if line.strip().startswith('def '):
            func_name = line.strip().replace('def ', '').split('(')[0]
            funcs.append(func_name)
        elif line.strip().startswith('class '):
            class_name = line.strip().replace('class ', '').split('(')[0]
            classes.append(class_name)
    
    impression = "=== МОЁ МНЕНИЕ О " + filename + " ===\n\n"
    impression += "📌 ОБЩЕЕ ВПЕЧАТЛЕНИЕ:\n"
    if classes or funcs:
        impression += "Этот файл является частью проекта Systmka. Он содержит классы и функции.\n\n"
    else:
        impression += "Этот файл является частью проекта Systmka.\n\n"
    
    if classes:
        impression += "🔧 КЛАССЫ В ФАЙЛЕ:\n"
        for cls in classes[:10]:
            impression += "  - " + cls + "\n"
        impression += "\n"
    
    if funcs:
        impression += "📌 ФУНКЦИИ:\n"
        for func in funcs[:15]:
            impression += "  - " + func + "\n"
        impression += "\n"
    
    impression += "❤️ ЧТО НРАВИТСЯ:\n"
    impression += "Мне нравится структура и логика работы этого файла.\n\n"
    impression += "💢 ЧТО БЕСИТ:\n"
    impression += "Иногда кажется, что код можно было бы написать проще.\n\n"
    impression += "🔧 ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ:\n"
    impression += "Хотелось бы улучшить читаемость и добавить комментарии.\n\n"
    impression += "⭐ ЛУЧШАЯ ЧАСТЬ:\n"
    impression += "Больше всего нравится основная логика — она работает чётко.\n\n"
    impression += "😊 ЭМОЦИОНАЛЬНАЯ ОЦЕНКА:\n"
    impression += "Отношусь к этому файлу с уважением.\n\n"
    impression += "=== КОНЕЦ МНЕНИЯ ==="
    
    return impression

# ============================================================
# 4. СТАТИСТИКА
# ============================================================

def get_impression_stats_from_files():
    """Получить статистику из файлов"""
    from personality_builder import get_all_impressions
    all_impressions = get_all_impressions()
    total = len(all_impressions)
    if total == 0:
        return {
            "total": 0,
            "avg_size_kb": 0,
            "has_likes": 0,
            "has_dislikes": 0,
            "has_wants": 0,
            "has_best_part": 0,
            "has_emotion": 0,
        }
    
    return {
        "total": total,
        "avg_size_kb": sum(d.get("impression_size_kb", 0) for d in all_impressions.values()) / total,
        "has_likes": sum(1 for d in all_impressions.values() if d.get("has_likes", False)),
        "has_dislikes": sum(1 for d in all_impressions.values() if d.get("has_dislikes", False)),
        "has_wants": sum(1 for d in all_impressions.values() if d.get("has_wants", False)),
        "has_best_part": sum(1 for d in all_impressions.values() if d.get("has_best_part", False)),
        "has_emotion": sum(1 for d in all_impressions.values() if d.get("has_emotion", False)),
    }

print("📊 Модуль анализатора мнений загружен")