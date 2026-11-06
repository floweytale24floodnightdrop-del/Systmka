"""Hugging Face API — бесплатные модели через config"""

import json
import time
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import HUGGINGFACE_KEY

# ============================================================
# 2. МОДЕЛИ
# ============================================================

HF_MODELS = {
    "phi-3.5-mini": "microsoft/Phi-3.5-mini-instruct",
    "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
    "llama-3.2-3b": "meta-llama/Llama-3.2-3B-Instruct",
}

# Дефолтная модель
DEFAULT_MODEL = "phi-3.5-mini"

# Таймаут запроса
REQUEST_TIMEOUT = 30

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def is_available():
    """Проверить, есть ли ключ Hugging Face"""
    return bool(HUGGINGFACE_KEY and len(HUGGINGFACE_KEY) > 20)

# ============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def ask_huggingface(prompt, system_prompt=None, model=DEFAULT_MODEL, max_tokens=200):
    """
    Запрос к Hugging Face API.
    
    Args:
        prompt: пользовательский запрос
        system_prompt: системный промт
        model: короткое имя модели ("phi-3.5-mini", "mistral-7b", "llama-3.2-3b")
        max_tokens: максимальное количество токенов в ответе
    
    Returns:
        tuple: (answer, source) — answer=None при ошибке
    """
    
    if not is_available():
        return None, "❌ Нет Hugging Face ключа"
    
    # Получаем полное имя модели
    if model not in HF_MODELS:
        model = DEFAULT_MODEL
    
    model_id = HF_MODELS[model]
    
    try:
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"}
        
        # Формируем промпт
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.8,
                "do_sample": True,
                "top_p": 0.95,
                "return_full_text": False,
            },
            "options": {
                "wait_for_model": True,
            }
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and data:
                text = data[0].get('generated_text', '')
                
                # Убираем повтор промпта
                if full_prompt in text:
                    text = text.replace(full_prompt, '').strip()
                
                text = text.strip()
                if text:
                    return text, model
                return None, "HuggingFace: пустой ответ"
            
            return None, "HuggingFace: неверный формат"
        
        elif response.status_code == 503:
            return None, "HuggingFace: модель загружается (попробуй позже)"
        
        elif response.status_code == 429:
            return None, "HuggingFace: лимит запросов"
        
        elif response.status_code == 401:
            return None, "HuggingFace: неверный ключ"
        
        elif response.status_code == 404:
            return None, f"HuggingFace: модель {model_id} не найдена"
        
        else:
            return None, f"HuggingFace: HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return None, "HuggingFace: таймаут"
    
    except requests.exceptions.ConnectionError:
        return None, "HuggingFace: нет соединения"
    
    except Exception as e:
        return None, f"HuggingFace ошибка: {str(e)[:80]}"

# ============================================================
# 5. ОБЁРТКИ ДЛЯ КОНКРЕТНЫХ МОДЕЛЕЙ
# ============================================================

def ask_phi(prompt, system_prompt=None, max_tokens=200):
    """Phi-3.5 Mini (быстрый)"""
    return ask_huggingface(prompt, system_prompt, "phi-3.5-mini", max_tokens)

def ask_mistral(prompt, system_prompt=None, max_tokens=200):
    """Mistral 7B (баланс)"""
    return ask_huggingface(prompt, system_prompt, "mistral-7b", max_tokens)

def ask_llama(prompt, system_prompt=None, max_tokens=200):
    """Llama 3.2 3B (лёгкий)"""
    return ask_huggingface(prompt, system_prompt, "llama-3.2-3b", max_tokens)

# ============================================================
# 6. ТЕСТ ДОСТУПНОСТИ
# ============================================================

def test_huggingface(model=DEFAULT_MODEL):
    """
    Проверить доступность Hugging Face.
    
    Returns:
        dict: {available, model, response_time, error}
    """
    if not is_available():
        return {
            "available": False,
            "error": "Нет ключа",
        }
    
    start = time.time()
    answer, source = ask_huggingface("Скажи 'OK'", max_tokens=10, model=model)
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

def get_huggingface_status():
    """Получить статус Hugging Face"""
    key_preview = f"{HUGGINGFACE_KEY[:10]}..." if HUGGINGFACE_KEY else "не установлен"
    
    return {
        "available": is_available(),
        "key_preview": key_preview,
        "models": list(HF_MODELS.keys()),
        "default_model": DEFAULT_MODEL,
    }

def format_huggingface_status():
    """Форматировать статус Hugging Face"""
    status = get_huggingface_status()
    
    lines = [
        "🤗 СТАТУС HUGGING FACE:",
        f"  Доступен: {'✅' if status['available'] else '❌'}",
        f"  Ключ: {status['key_preview']}",
        f"  Модель по умолчанию: {status['default_model']}",
        f"  Моделей: {len(status['models'])}",
        f"  Список: {', '.join(status['models'])}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🤗 Модуль Hugging Face загружен")
if is_available():
    print(f"🔑 Ключ: {HUGGINGFACE_KEY[:10]}...")
    print(f"📋 Модели: {', '.join(HF_MODELS.keys())}")
else:
    print("⚠️ Ключ Hugging Face не установлен")