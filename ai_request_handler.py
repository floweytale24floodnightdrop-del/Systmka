"""Обработчик запросов к ИИ — отправка через OpenRouter, Gemini, Hugging Face"""

import time
import requests
import json
import os
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEYS, GEMINI_KEY, HUGGINGFACE_KEY
from ai_key_rotator import (
    get_best_openrouter_key, use_openrouter_key, 
    use_gemini_key, use_huggingface_key, 
    save_key_stats, key_stats
)
from ai_model_manager import evaluate_model

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

REQUEST_TIMEOUT = 45

# ============================================================
# 3. ОТПРАВКА ЧЕРЕЗ OPENROUTER
# ============================================================

def ask_openrouter(prompt, system_prompt=None, model=None, max_tokens=200):
    """Отправить запрос через OpenRouter с ротацией ключей"""
    
    key = get_best_openrouter_key()
    if not key:
        return None, "❌ Все ключи OpenRouter исчерпаны", False
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/SystmkaAI_bot",
                "X-Title": "Systmka AI"
            },
            json={
                "model": model or "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt or "Ты полезный ассистент."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8,
            },
            timeout=REQUEST_TIMEOUT
        )
        
        response_time = time.time() - start_time
        
        # Используем ключ (увеличиваем счётчик)
        use_openrouter_key(key)
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                answer = data['choices'][0]['message']['content'].strip()
                # Передаём успешный результат в систему оценки
                quality_score = evaluate_response_quality(answer, response_time, True)
                evaluate_model(model or "deepseek/deepseek-chat", response_time, quality_score, "general", True)
                return answer, key, True
        
        elif response.status_code == 429:
            if key in key_stats["openrouter"]:
                key_stats["openrouter"][key]["status"] = "exhausted"
                key_stats["openrouter"][key]["remaining"] = 0
                save_key_stats()
            # Передаём неудачный результат
            evaluate_model(model or "deepseek/deepseek-chat", response_time, 2, "general", False)
            return None, f"Лимит ключа {key[:10]}...", False
        
        else:
            # Передаём неудачный результат
            evaluate_model(model or "deepseek/deepseek-chat", response_time, 2, "general", False)
            return None, f"HTTP {response.status_code}", False
            
    except Exception as e:
        response_time = time.time() - start_time
        evaluate_model(model or "deepseek/deepseek-chat", response_time, 2, "general", False)
        return None, str(e), False

# ============================================================
# 4. ОТПРАВКА ЧЕРЕЗ GEMINI
# ============================================================

def ask_gemini(prompt, system_prompt=None, model="gemini-2.0-flash", max_tokens=200):
    """Отправить запрос через Gemini"""
    
    if not GEMINI_KEY:
        return None, "❌ Нет Gemini ключа", False
    
    start_time = time.time()
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            }
        }
        
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        
        response_time = time.time() - start_time
        
        use_gemini_key()
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                text = data['candidates'][0]['content']['parts'][0]['text']
                # Передаём успешный результат
                quality_score = evaluate_response_quality(text, response_time, True)
                evaluate_model(model, response_time, quality_score, "general", True)
                return text, "Gemini", True
        
        # Передаём неудачный результат
        evaluate_model(model, response_time, 2, "general", False)
        return None, f"Gemini HTTP {response.status_code}", False
        
    except Exception as e:
        response_time = time.time() - start_time
        evaluate_model(model, response_time, 2, "general", False)
        return None, str(e), False

# ============================================================
# 5. ОТПРАВКА ЧЕРЕЗ HUGGING FACE
# ============================================================

def ask_huggingface(prompt, system_prompt=None, model="microsoft/Phi-3.5-mini-instruct", max_tokens=200):
    """Отправить запрос через Hugging Face"""
    
    if not HUGGINGFACE_KEY:
        return None, "❌ Нет Hugging Face ключа", False
    
    start_time = time.time()
    
    try:
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"}
        
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.8,
                "do_sample": True,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        
        response_time = time.time() - start_time
        
        use_huggingface_key()
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                text = data[0].get('generated_text', '')
                if full_prompt in text:
                    text = text.replace(full_prompt, '').strip()
                # Передаём успешный результат
                quality_score = evaluate_response_quality(text, response_time, True)
                evaluate_model(model, response_time, quality_score, "general", True)
                return text, "Hugging Face", True
        
        # Передаём неудачный результат
        evaluate_model(model, response_time, 2, "general", False)
        return None, f"Hugging Face HTTP {response.status_code}", False
        
    except Exception as e:
        response_time = time.time() - start_time
        evaluate_model(model, response_time, 2, "general", False)
        return None, str(e), False

# ============================================================
# 6. ОЦЕНКА КАЧЕСТВА ОТВЕТА
# ============================================================

def evaluate_response_quality(answer, response_time, success):
    """Оценить качество ответа"""
    
    if not success or not answer:
        return 2
    
    score = 5
    
    # Длина
    words = len(answer.split())
    if 10 <= words <= 50:
        score += 1
    elif words > 50:
        score += 0.5
    elif words < 5:
        score -= 1
    
    # Человечность
    ai_phrases = ["чем могу помочь", "обращайтесь", "я здесь чтобы помочь", "рада помочь"]
    human_phrases = ["ага", "ну", "хм", "ой", "ээ", "крч", "типа"]
    
    if any(p in answer.lower() for p in ai_phrases):
        score -= 1
    if any(p in answer.lower() for p in human_phrases):
        score += 0.5
    
    # Смайлики
    emojis = ["❤️", "💜", "😊", "🔥", "🥰", "🫶"]
    if any(e in answer for e in emojis):
        score += 0.5
    
    # Скорость
    if response_time < 2:
        score += 1
    elif response_time < 5:
        score += 0.5
    elif response_time > 15:
        score -= 1
    
    return max(1, min(10, score))

# ============================================================
# 7. СТАТУС
# ============================================================

def get_router_status():
    from ai_model_manager import get_active_main_models, get_disabled_main_models, get_model_stats_summary
    from ai_key_rotator import get_key_stats_summary, get_all_openrouter_keys_status
    
    return {
        "active_models": get_active_main_models(),
        "disabled_models": get_disabled_main_models(),
        "key_summary": get_key_stats_summary(),
        "key_details": get_all_openrouter_keys_status(),
        "model_summary": get_model_stats_summary(),
    }

def format_router_status():
    status = get_router_status()
    
    lines = [
        "🤖 СТАТУС ИИ-СИСТЕМЫ SYSTMKA",
        "═" * 50,
        "",
        "═══ ГЛАВНЫЕ МОДЕЛИ ═══",
    ]
    
    for model_id, model in status.get("active_models", {}).items():
        icon = model.get("icon", "✅")
        name = model.get("name", model_id)
        stats = status.get("model_summary", {}).get(model_id, {})
        total = stats.get("total_uses", 0)
        rating = stats.get("rating", 50)
        lines.append(f"{icon} {name} — АКТИВНА")
        lines.append(f"   ├── Запросов: {total}")
        lines.append(f"   ├── Рейтинг: {rating:.1f}/100")
        lines.append(f"   └── Под-моделей: {len(model.get('sub_models', []))}")
    
    if status.get("disabled_models"):
        lines.append("")
        lines.append("═══ ОТКЛЮЧЁННЫЕ МОДЕЛИ ═══")
        for model_id, model in status["disabled_models"].items():
            icon = model.get("icon", "❌")
            name = model.get("name", model_id)
            lines.append(f"{icon} {name} — ОТКЛЮЧЕНА")
    
    lines.append("")
    lines.append("═══ КЛЮЧИ OPENROUTER ═══")
    
    for key, data in status.get("key_details", {}).items():
        email = data.get("email", key[:20] + "...")
        remaining = data.get("remaining", 0)
        total = data.get("total", 5000)
        percent = (remaining / total) * 100 if total > 0 else 0
        status_icon = "✅" if data.get("status") == "active" else "⚠️" if data.get("status") == "low" else "🔴"
        
        bar_len = 10
        filled = int((percent / 100) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        lines.append(f"{status_icon} {email}")
        lines.append(f"   ├── {remaining}/{total} ({percent:.1f}%) {bar}")
        lines.append(f"   └── Статус: {data.get('status', 'unknown')}")
    
    lines.append("")
    lines.append("═══ ДОП. КЛЮЧИ ═══")
    lines.append(f"🔑 Gemini: {status.get('key_summary', {}).get('gemini_remaining', 0)}")
    lines.append(f"🔑 Hugging Face: {status.get('key_summary', {}).get('huggingface_remaining', 0)}")
    
    lines.append("")
    lines.append("═══ ОБЩАЯ СТАТИСТИКА ═══")
    lines.append(f"📊 Всего запросов: {status.get('key_summary', {}).get('total_used', 0)}")
    lines.append(f"📈 Осталось: {status.get('key_summary', {}).get('total_remaining', 0)}")
    lines.append(f"⏱ За час: {status.get('key_summary', {}).get('requests_last_hour', 0)}")
    lines.append(f"⏱ За 24 часа: {status.get('key_summary', {}).get('requests_24h', 0)}")
    lines.append(f"🟢 Активных ключей: {status.get('key_summary', {}).get('active_keys', 0)}/{status.get('key_summary', {}).get('total_keys', 0)}")
    
    return "\n".join(lines)

print("📨 AI Request Handler загружен")