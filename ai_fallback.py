"""Fallback модели — обёртка над ai_request_handler и ai_huggingface. Без хардкодов."""

import json
import time
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import (
    OPENROUTER_KEY,
    OPENROUTER_KEYS,
    HUGGINGFACE_KEY,
    GEMINI_KEY,
)

# ============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 3. ПРЯМЫЕ ЗАПРОСЫ К ПРОВАЙДЕРАМ
# ============================================================

def ask_openrouter_direct(prompt, system_prompt=None, model="deepseek/deepseek-chat", max_tokens=200):
    """
    Прямой запрос к OpenRouter (без ротации).
    
    Returns:
        tuple: (answer, source) — answer=None при ошибке
    """
    key = _get_openrouter_key()
    if not key:
        return None, "❌ Нет ключа OpenRouter"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "Ты полезный ассистент."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content'].strip()
                if text:
                    return text, f"OpenRouter ({model})"
        
        if response.status_code == 429:
            return None, "OpenRouter: лимит"
        
        return None, f"OpenRouter: HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return None, "OpenRouter: таймаут"
    except Exception as e:
        return None, f"OpenRouter ошибка: {str(e)[:80]}"

def ask_huggingface_direct(prompt, system_prompt=None, model="microsoft/Phi-3.5-mini-instruct", max_tokens=200):
    """
    Прямой запрос к Hugging Face.
    
    Returns:
        tuple: (answer, source) — answer=None при ошибке
    """
    if not HUGGINGFACE_KEY:
        return None, "❌ Нет ключа Hugging Face"
    
    try:
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"}
        
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
            "options": {"wait_for_model": True}
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                text = data[0].get('generated_text', '')
                if full_prompt in text:
                    text = text.replace(full_prompt, '').strip()
                text = text.strip()
                if text:
                    return text, f"HuggingFace ({model.split('/')[-1]})"
        
        if response.status_code == 503:
            return None, "HuggingFace: модель загружается"
        
        return None, f"HuggingFace: HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return None, "HuggingFace: таймаут"
    except Exception as e:
        return None, f"HuggingFace ошибка: {str(e)[:80]}"

# ============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ — FALLBACK ЦЕПОЧКА
# ============================================================

def ask_with_fallback(prompt, system_prompt=None, max_tokens=200):
    """
    Запрос с fallback между провайдерами.
    
    Порядок:
    1. OpenRouter (deepseek-chat) — основной
    2. Gemini — быстрый fallback
    3. HuggingFace (Phi-3.5) — fallback
    4. HuggingFace (Mistral-7B) — последний шанс
    
    Args:
        prompt: запрос
        system_prompt: системный промт
        max_tokens: максимум токенов
    
    Returns:
        tuple: (answer, source)
    """
    
    # 1. OpenRouter
    result, source = ask_openrouter_direct(prompt, system_prompt, max_tokens=max_tokens)
    if result:
        return result, source
    
    print(f"⚠️ OpenRouter не сработал: {source}")
    
    # 2. Gemini
    try:
        from ai_gemini import ask_gemini_flash
        result, source = ask_gemini_flash(prompt, system_prompt, max_tokens=max_tokens)
        if result:
            return result, source
        print(f"⚠️ Gemini не сработал: {source}")
    except ImportError:
        print("⚠️ ai_gemini недоступен")
    except Exception as e:
        print(f"⚠️ Gemini ошибка: {e}")
    
    # 3. HuggingFace (Phi-3.5)
    result, source = ask_huggingface_direct(prompt, system_prompt, max_tokens=max_tokens)
    if result:
        return result, source
    
    print(f"⚠️ HuggingFace (Phi) не сработал: {source}")
    
    # 4. HuggingFace (Mistral-7B)
    result, source = ask_huggingface_direct(
        prompt, system_prompt,
        model="mistralai/Mistral-7B-Instruct-v0.3",
        max_tokens=max_tokens
    )
    if result:
        return result, source
    
    print(f"⚠️ HuggingFace (Mistral) не сработал: {source}")
    
    # 5. Всё сломалось
    return "❌ Все модели ИИ недоступны. Попробуй позже.", None

# ============================================================
# 5. ТЕСТ ВСЕХ ПРОВАЙДЕРОВ
# ============================================================

def test_all_providers():
    """
    Проверить всех провайдеров.
    
    Returns:
        dict: результаты по каждому провайдеру
    """
    results = {}
    
    # OpenRouter
    start = time.time()
    answer, source = ask_openrouter_direct("Скажи 'OK'", max_tokens=10)
    results["openrouter"] = {
        "available": bool(answer),
        "source": source,
        "time": round(time.time() - start, 2),
    }
    
    # Gemini
    try:
        from ai_gemini import ask_gemini_flash
        start = time.time()
        answer, source = ask_gemini_flash("Скажи 'OK'", max_tokens=10)
        results["gemini"] = {
            "available": bool(answer),
            "source": source,
            "time": round(time.time() - start, 2),
        }
    except Exception as e:
        results["gemini"] = {
            "available": False,
            "source": str(e)[:80],
            "time": 0,
        }
    
    # HuggingFace (Phi)
    start = time.time()
    answer, source = ask_huggingface_direct("Скажи 'OK'", max_tokens=10)
    results["huggingface_phi"] = {
        "available": bool(answer),
        "source": source,
        "time": round(time.time() - start, 2),
    }
    
    return results

def format_providers_status():
    """Форматировать статус провайдеров"""
    results = test_all_providers()
    
    lines = ["🔌 СТАТУС ПРОВАЙДЕРОВ ИИ:"]
    lines.append("")
    
    for provider, data in results.items():
        icon = "✅" if data["available"] else "❌"
        lines.append(f"  {icon} {provider}: {data['source']} ({data['time']}с)")
    
    return "\n".join(lines)

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("🤖 Модуль fallback ИИ загружен")
print(f"🔑 OpenRouter: {'✅' if OPENROUTER_KEYS or OPENROUTER_KEY else '❌'}")
print(f"🔑 Gemini: {'✅' if GEMINI_KEY else '❌'}")
print(f"🔑 HuggingFace: {'✅' if HUGGINGFACE_KEY else '❌'}")