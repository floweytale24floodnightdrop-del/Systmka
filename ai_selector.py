"""Выбор лучших ИИ-моделей для каждой задачи — с Gemini и Hugging Face"""

import time
import random
from datetime import datetime

from ai_performance import (
    get_best_models, update_model_stats, get_daily_stats,
    increment_daily_requests, get_model_stats
)
from ai_models import FREE_MODELS
from ai_gemini import ask_gemini_flash, ask_gemini_pro
from ai_huggingface import ask_phi, ask_mistral

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

MAX_REQUESTS_PER_DAY = 200  # Увеличиваем лимит (Gemini бесплатный)

# ============================================================
# 2. ФУНКЦИИ ДЛЯ РАЗНЫХ ТИПОВ МОДЕЛЕЙ
# ============================================================

def ask_model_direct(prompt, system_prompt, model_id):
    """Напрямую запросить модель по ID"""
    
    # OpenRouter
    if model_id.startswith("deepseek/") or model_id.startswith("google/") or model_id.startswith("meta-llama/") or model_id.startswith("microsoft/"):
        from ai_router import ask_ai
        return ask_ai(prompt, system_prompt, preferred_model=model_id)
    
    # Gemini
    elif model_id.startswith("gemini/"):
        if "pro" in model_id:
            result, source = ask_gemini_pro(prompt, system_prompt)
        else:
            result, source = ask_gemini_flash(prompt, system_prompt)
        return result, source, result is not None
    
    # Hugging Face
    elif model_id.startswith("huggingface/"):
        model_name = model_id.replace("huggingface/", "")
        if "mistral" in model_name:
            result, source = ask_mistral(prompt, system_prompt)
        else:
            result, source = ask_phi(prompt, system_prompt)
        return result, source, result is not None
    
    return None, None, False

# ============================================================
# 3. ВЫБОР МОДЕЛЕЙ
# ============================================================

def select_models_for_task(task_type, count=3):
    """Выбрать модели для конкретной задачи"""
    
    # Приоритет: сначала Gemini, потом OpenRouter, потом HF
    priority_order = [
        "gemini/gemini-2.0-flash",
        "gemini/gemini-2.5-pro",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1",
        "huggingface/mistral-7b",
        "huggingface/phi-3.5-mini",
    ]
    
    available_models = []
    for model_id in priority_order:
        if model_id in FREE_MODELS and FREE_MODELS[model_id].get("available", False):
            # Проверяем, не заморожена ли модель
            from ai_stats import get_disabled_models
            disabled = get_disabled_models()
            if model_id not in disabled:
                available_models.append(model_id)
    
    # Добавляем лучшие модели из статистики
    best_models = get_best_models(task_type, count)
    for model_id in best_models:
        if model_id not in available_models and model_id in FREE_MODELS:
            if FREE_MODELS[model_id].get("available", False):
                available_models.append(model_id)
    
    # Если нет доступных — берём любые
    if not available_models:
        for model_id in FREE_MODELS:
            if FREE_MODELS[model_id].get("available", False):
                available_models.append(model_id)
                if len(available_models) >= count:
                    break
    
    return available_models[:count]

# ============================================================
# 4. ОТПРАВКА ЗАПРОСА
# ============================================================

def ask_with_selection(prompt, system_prompt=None, task_type="general", max_tokens=200):
    """Отправить запрос с автоматическим выбором модели"""
    
    # Проверяем лимиты
    can_request, msg = check_daily_limit()
    if not can_request:
        return msg, None, False, "limit_exceeded"
    
    # Выбираем модели
    models = select_models_for_task(task_type, 3)
    
    if not models:
        return "❌ Нет доступных моделей", None, False, "no_models"
    
    last_error = None
    for model_id in models:
        start_time = time.time()
        
        try:
            # Отправляем запрос
            answer, source, success = ask_model_direct(prompt, system_prompt, model_id)
            
            response_time = time.time() - start_time
            
            # Обновляем статистику
            update_model_stats(model_id, success, response_time, task_type)
            
            if success:
                increment_daily_requests()
                return answer, source, True, "success"
            
            last_error = answer or "Неизвестная ошибка"
            
        except Exception as e:
            response_time = time.time() - start_time
            update_model_stats(model_id, False, response_time, task_type)
            last_error = str(e)
            continue
    
    return f"❌ Все модели не ответили. Последняя ошибка: {last_error}", None, False, "all_failed"

# ============================================================
# 5. СТАТУС
# ============================================================

def get_ai_status():
    """Получить статус всех моделей"""
    
    from ai_stats import get_router_stats, get_available_models, get_disabled_models
    
    stats = get_router_stats()
    available = get_available_models()
    disabled = get_disabled_models()
    daily = get_daily_stats()
    
    return {
        "total_models": stats.get("models", 0),
        "available_models": len(available),
        "disabled_models": disabled,
        "daily_requests": daily.get("total_requests", 0),
        "daily_limit": MAX_REQUESTS_PER_DAY,
        "requests_left": MAX_REQUESTS_PER_DAY - daily.get("total_requests", 0),
        "models": available,
    }

def format_ai_status():
    """Форматировать статус для вывода"""
    
    status = get_ai_status()
    
    lines = [
        "🤖 СТАТУС ИИ-МОДЕЛЕЙ:",
        f"📊 Всего моделей: {status['total_models']}",
        f"✅ Доступно: {status['available_models']}",
        f"🔒 Заморожено: {len(status['disabled_models'])}",
        "",
        f"📈 ЗАПРОСЫ ЗА ДЕНЬ:",
        f"   Использовано: {status['daily_requests']}/{status['daily_limit']}",
        f"   Осталось: {status['requests_left']}",
    ]
    
    if status['models']:
        lines.append("\n📋 ДОСТУПНЫЕ МОДЕЛИ:")
        # Сортируем по провайдеру
        for m in sorted(status['models'], key=lambda x: x.get('provider', '')):
            lines.append(f"  • {m['name']} ({m['provider']})")
    
    if status['disabled_models']:
        lines.append("\n🔒 ЗАМОРОЖЕННЫЕ МОДЕЛИ:")
        for m in status['disabled_models'][:5]:
            lines.append(f"  • {m}")
    
    return "\n".join(lines)

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("🎯 Модуль выбора ИИ-моделей загружен")
print(f"📊 Дневной лимит: {MAX_REQUESTS_PER_DAY} запросов")
print(f"🤖 Модели: OpenRouter + Gemini + Hugging Face")