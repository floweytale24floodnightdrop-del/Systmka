"""Google Gemini API — бесплатный доступ через config"""

import json
import time
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import GEMINI_KEY

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

# Модели Gemini
GEMINI_MODELS = {
    "flash": "gemini-2.0-flash",
    "flash-lite": "gemini-2.0-flash-lite",
    "pro": "gemini-2.5-pro",
}

# Дефолтная модель
DEFAULT_MODEL = "gemini-2.0-flash"

# Таймаут запроса
REQUEST_TIMEOUT = 30

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def is_available():
    """Проверить, есть ли ключ Gemini"""
    return bool(GEMINI_KEY and len(GEMINI_KEY) > 20)

# ============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def ask_gemini(prompt, system_prompt=None, model=DEFAULT_MODEL, max_tokens=200):
    """
    Запрос к Gemini API.
    
    Args:
        prompt: пользовательский запрос
        system_prompt: системный промт (опционально)
        model: имя модели (например, "gemini-2.0-flash")
        max_tokens: максимальное количество токенов в ответе
    
    Returns:
        tuple: (answer, source) — answer=None при ошибке
    """
    
    if not is_available():
        return None, "❌ Нет Gemini ключа"
    
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent?key={GEMINI_KEY}"
        )
        
        # Формируем промпт
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
                "topK": 40,
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                candidate = data['candidates'][0]
                content = candidate.get('content', {})
                parts = content.get('parts', [])
                if parts:
                    text = parts[0].get('text', '').strip()
                    if text:
                        return text, model
                return None, "Gemini: пустой ответ"
            else:
                return None, "Gemini: нет candidates"
        
        elif response.status_code == 429:
            return None, "Gemini: лимит запросов"
        
        elif response.status_code == 400:
            return None, "Gemini: неверный запрос"
        
        elif response.status_code == 403:
            return None, "Gemini: доступ запрещён (проверь ключ)"
        
        else:
            return None, f"Gemini: HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return None, "Gemini: таймаут"
    
    except requests.exceptions.ConnectionError:
        return None, "Gemini: нет соединения"
    
    except Exception as e:
        return None, f"Gemini ошибка: {str(e)[:80]}"

# ============================================================
# 5. ОБЁРТКИ ДЛЯ КОНКРЕТНЫХ МОДЕЛЕЙ
# ============================================================

def ask_gemini_flash(prompt, system_prompt=None, max_tokens=200):
    """Gemini 2.0 Flash (быстрый)"""
    return ask_gemini(prompt, system_prompt, "gemini-2.0-flash", max_tokens)

def ask_gemini_flash_lite(prompt, system_prompt=None, max_tokens=200):
    """Gemini 2.0 Flash Lite (очень быстрый)"""
    return ask_gemini(prompt, system_prompt, "gemini-2.0-flash-lite", max_tokens)

def ask_gemini_pro(prompt, system_prompt=None, max_tokens=400):
    """Gemini 2.5 Pro (мощный)"""
    return ask_gemini(prompt, system_prompt, "gemini-2.5-pro", max_tokens)

# ============================================================
# 6. ТЕСТ ДОСТУПНОСТИ
# ============================================================

def test_gemini():
    """
    Проверить доступность Gemini.
    
    Returns:
        dict: {available, model, response_time, error}
    """
    if not is_available():
        return {
            "available": False,
            "error": "Нет ключа",
        }
    
    start = time.time()
    answer, source = ask_gemini("Скажи 'OK'", max_tokens=10)
    response_time = round(time.time() - start, 2)
    
    if answer:
        return {
            "available": True,
            "model": source,
            "response_time": response_time,
            "answer": answer[:50],
        }
    else:
        return {
            "available": False,
            "error": source,
            "response_time": response_time,
        }

# ============================================================
# 7. СТАТУС
# ============================================================

def get_gemini_status():
    """Получить статус Gemini"""
    key_preview = f"{GEMINI_KEY[:15]}..." if GEMINI_KEY else "не установлен"
    
    return {
        "available": is_available(),
        "key_preview": key_preview,
        "models": list(GEMINI_MODELS.values()),
        "default_model": DEFAULT_MODEL,
    }

def format_gemini_status():
    """Форматировать статус Gemini"""
    status = get_gemini_status()
    
    lines = [
        "🤖 СТАТУС GEMINI:",
        f"  Доступен: {'✅' if status['available'] else '❌'}",
        f"  Ключ: {status['key_preview']}",
        f"  Модель по умолчанию: {status['default_model']}",
        f"  Моделей: {len(status['models'])}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🤖 Модуль Gemini загружен")
if is_available():
    print(f"🔑 Ключ: {GEMINI_KEY[:15]}...")
    print(f"📋 Модели: {', '.join(GEMINI_MODELS.values())}")
else:
    print("⚠️ Ключ Gemini не установлен")