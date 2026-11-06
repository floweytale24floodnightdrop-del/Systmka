"""Маршрутизатор ИИ — Систмка сама выбирает модели на основе рейтинга"""

import os
import json
import time
import random
import requests
from datetime import datetime
from collections import defaultdict

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import (
    OPENROUTER_KEY,
    OPENROUTER_KEYS,
    GEMINI_KEY,
    HUGGINGFACE_KEY,
)

# ============================================================
# 2. ИМПОРТЫ ПОДСИСТЕМ (С ЗАЩИТОЙ)
# ============================================================

try:
    from ai_key_rotator import (
        get_best_openrouter_key,
        use_openrouter_key,
        key_stats,
        save_key_stats,
    )
except ImportError:
    print("⚠️ ai_key_rotator недоступен")
    def get_best_openrouter_key():
        return OPENROUTER_KEY
    def use_openrouter_key(key):
        pass
    key_stats = {}
    def save_key_stats():
        pass

try:
    from ai_model_manager import (
        get_best_model_for_task,
        get_sub_models_for_task,
        get_all_sub_models_for_task,
        evaluate_model,
        update_model_performance,
        get_model_rating,
        get_model_stats_summary,
        get_main_model,
        get_all_main_models,
        get_active_main_models,
        get_model_for_task,
    )
except ImportError:
    print("⚠️ ai_model_manager недоступен")
    def get_best_model_for_task(task_type):
        return None
    def get_sub_models_for_task(task_type, count=3):
        return []
    def get_all_sub_models_for_task(task_type):
        return []
    def evaluate_model(*args, **kwargs):
        pass
    def update_model_performance(*args, **kwargs):
        pass
    def get_model_rating(model_id):
        return 50
    def get_model_stats_summary():
        return {}
    def get_main_model(model_id):
        return None
    def get_all_main_models():
        return {}
    def get_active_main_models():
        return {}
    def get_disabled_main_models():
        return {}
    def get_model_for_task(task_type):
        return None, None

try:
    from ai_request_handler import (
        ask_openrouter,
        ask_gemini,
        ask_huggingface,
    )
except ImportError:
    print("⚠️ ai_request_handler недоступен")
    def ask_openrouter(*args, **kwargs):
        return None, "ai_request_handler недоступен", False
    def ask_gemini(*args, **kwargs):
        return None, "ai_request_handler недоступен", False
    def ask_huggingface(*args, **kwargs):
        return None, "ai_request_handler недоступен", False

# ============================================================
# 3. НАСТРОЙКИ
# ============================================================

ROUTER_STATS_FILE = "router_stats.json"

router_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "model_usage": defaultdict(int),
    "key_usage": defaultdict(int),
    "last_updated": None,
    "autonomous_decisions": 0,
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА СТАТИСТИКИ
# ============================================================

def save_router_stats():
    """Сохранить статистику роутера"""
    try:
        data = {
            "total_requests": router_stats["total_requests"],
            "successful_requests": router_stats["successful_requests"],
            "failed_requests": router_stats["failed_requests"],
            "model_usage": dict(router_stats["model_usage"]),
            "key_usage": dict(router_stats["key_usage"]),
            "last_updated": router_stats["last_updated"],
            "autonomous_decisions": router_stats["autonomous_decisions"],
        }
        with open(ROUTER_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения статистики: {e}")
        return False

def load_router_stats():
    """Загрузить статистику роутера"""
    global router_stats
    try:
        if os.path.exists(ROUTER_STATS_FILE):
            with open(ROUTER_STATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                router_stats["total_requests"] = loaded.get("total_requests", 0)
                router_stats["successful_requests"] = loaded.get("successful_requests", 0)
                router_stats["failed_requests"] = loaded.get("failed_requests", 0)
                router_stats["model_usage"] = defaultdict(int, loaded.get("model_usage", {}))
                router_stats["key_usage"] = defaultdict(int, loaded.get("key_usage", {}))
                router_stats["last_updated"] = loaded.get("last_updated")
                router_stats["autonomous_decisions"] = loaded.get("autonomous_decisions", 0)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки статистики: {e}")
        return False

load_router_stats()

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 6. АНАЛИЗ ЗАПРОСА
# ============================================================

def systmka_understand(prompt, user_id=None, chat_id=None, context=None):
    """
    Систмка сама анализирует запрос и решает что делать.
    
    Returns:
        dict: {type, command, needs_action, action_type, priority,
               models_needed, is_urgent, should_respond, response_style}
    """
    try:
        key = _get_openrouter_key()
        
        analysis_prompt = f"""Проанализируй запрос пользователя и определи:

ЗАПРОС: {prompt}

ОТВЕТЬ ТОЛЬКО JSON:
{{
    "type": "command|question|conversation|rp|system|unknown",
    "command": "название команды если это команда",
    "needs_action": true/false,
    "action_type": "none|reply|execute|generate|search|dox|game",
    "priority": 1-10,
    "models_needed": ["model1", "model2"],
    "is_urgent": true/false,
    "should_respond": true/false,
    "response_style": "short|medium|long|emotional|formal|playful"
}}
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
                            "Ты Систмка. Ты анализируешь запросы и понимаешь "
                            "что хочет пользователь. Отвечай только JSON."
                        )
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.5,
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0]['message']['content']
                
                # Чистим markdown-обёртку
                content = content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    analysis = json.loads(content)
                    router_stats["autonomous_decisions"] += 1
                    save_router_stats()
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"⚠️ Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка анализа: {e}")
    
    # Fallback
    return {
        "type": "conversation",
        "command": None,
        "needs_action": False,
        "action_type": "reply",
        "priority": 5,
        "models_needed": ["deepseek/deepseek-chat", "gemini/gemini-2.0-flash"],
        "is_urgent": False,
        "should_respond": True,
        "response_style": "medium",
    }

# ============================================================
# 7. ВЫБОР МОДЕЛЕЙ
# ============================================================

def systmka_choose_models(analysis, prompt):
    """
    Систмка сама выбирает модели на основе рейтинга.
    
    Returns:
        tuple: (models_list, task_type)
    """
    request_type = analysis.get("type", "conversation")
    needs_action = analysis.get("needs_action", False)
    action_type = analysis.get("action_type", "reply")
    priority = analysis.get("priority", 5)
    
    # Определяем тип задачи
    task_type = "general_chat"
    if request_type == "rp":
        task_type = "rp"
    elif request_type == "command":
        if action_type in ("execute", "dox"):
            task_type = "security"
        elif action_type == "generate":
            task_type = "image_generation"
        else:
            task_type = "commands"
    elif request_type == "question":
        task_type = "question_answering"
    elif request_type == "system":
        task_type = "commands"
    
    # Получаем модели
    models = get_sub_models_for_task(task_type, count=4 if needs_action else 2)
    
    if not models:
        models = ["deepseek/deepseek-chat", "gemini/gemini-2.0-flash"]
    
    # Если нужно действие — добавляем больше
    if needs_action and len(models) < 3:
        extra_models = ["deepseek/deepseek-r1", "gemini/gemini-2.5-pro"]
        for m in extra_models:
            if m not in models:
                models.append(m)
    
    return models, task_type

# ============================================================
# 8. СТИЛЬ ОТВЕТА
# ============================================================

def systmka_decide_response_style(analysis, user_id=None):
    """Систмка сама решает в каком стиле отвечать"""
    request_type = analysis.get("type", "conversation")
    response_style = analysis.get("response_style", "medium")
    is_urgent = analysis.get("is_urgent", False)
    
    try:
        from behavior import get_user_behavior
        if user_id:
            user_data = get_user_behavior(user_id)
            if user_data:
                style = user_data.get("style", "neutral")
                if style == "friendly":
                    response_style = "emotional"
                elif style == "formal":
                    response_style = "formal"
                elif style == "aggressive":
                    response_style = "short"
    except Exception:
        pass
    
    if request_type == "rp":
        response_style = "emotional"
    elif request_type == "command":
        response_style = "short" if is_urgent else "medium"
    elif request_type == "question":
        response_style = "medium"
    elif request_type == "system":
        response_style = "formal"
    
    return response_style

# ============================================================
# 9. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def ask_ai(prompt, system_prompt=None, task_type=None, max_tokens=200,
           user_id=None, chat_id=None, preferred_model=None):
    """
    Систмка сама:
    1. Понимает что хочет пользователь
    2. Выбирает модели по рейтингу
    3. Решает как отвечать
    4. Выполняет действия если нужно
    
    Returns:
        tuple: (answer, source, success)
    """
    
    # 1. Анализ запроса
    analysis = systmka_understand(prompt, user_id, chat_id)
    
    # 2. Выбор моделей
    if preferred_model:
        models = [preferred_model]
        detected_task_type = task_type or "general_chat"
    else:
        models, detected_task_type = systmka_choose_models(analysis, prompt)
    
    # 3. Стиль ответа
    style = systmka_decide_response_style(analysis, user_id)
    
    # 4. Корректировка max_tokens
    if style == "short":
        max_tokens = min(max_tokens, 100)
    elif style == "medium":
        max_tokens = min(max_tokens, 200)
    elif style in ("long", "emotional"):
        max_tokens = min(max_tokens, 400)
    elif style == "formal":
        max_tokens = min(max_tokens, 250)
    
    # 5. Отправка
    router_stats["total_requests"] += 1
    router_stats["model_usage"][analysis.get("type", "unknown")] += 1
    
    last_error = None
    model_used = None
    response_time = 0
    
    for model in models:
        start_time = time.time()
        
        if "gemini" in model:
            answer, source, success = ask_gemini(prompt, system_prompt, model, max_tokens)
        elif "huggingface" in model:
            answer, source, success = ask_huggingface(prompt, system_prompt, model, max_tokens)
        else:
            answer, source, success = ask_openrouter(prompt, system_prompt, model, max_tokens)
        
        response_time = time.time() - start_time
        model_used = model
        
        # Оценка
        quality_score = 5
        if success:
            if response_time < 2:
                quality_score = 8
            elif response_time < 5:
                quality_score = 7
            elif response_time < 10:
                quality_score = 6
            else:
                quality_score = 5
        else:
            quality_score = 2
        
        try:
            evaluate_model(model, response_time, quality_score, detected_task_type, success)
        except Exception:
            pass
        
        if success:
            router_stats["successful_requests"] += 1
            router_stats["last_updated"] = datetime.now().isoformat()
            
            # Действия
            if analysis.get("needs_action", False) and analysis.get("action_type") != "none":
                answer = execute_action(answer, analysis, prompt, user_id, chat_id)
            
            # Стиль
            if style == "emotional" and not any(w in answer for w in ["❤️", "💜", "😊", "🥺"]):
                answer += " " + random.choice(["💜", "✨", "😊", "🫶"])
            
            save_router_stats()
            return answer, f"Systmka ({source})", True
        
        last_error = source
    
    router_stats["failed_requests"] += 1
    save_router_stats()
    
    return (
        f"❌ Систмка не смогла ответить. Попробуй позже. ({last_error})",
        None,
        False,
    )

# ============================================================
# 10. ВЫПОЛНЕНИЕ ДЕЙСТВИЙ
# ============================================================

def execute_action(answer, analysis, prompt, user_id=None, chat_id=None):
    """Систмка выполняет действия если нужно"""
    action_type = analysis.get("action_type", "none")
    
    if action_type == "none":
        return answer
    
    try:
        if action_type == "search":
            try:
                from self_learning import search_google_free
                results = search_google_free(prompt)
                if results:
                    answer += "\n\n🔍 Результаты поиска:\n" + "\n".join(results[:5])
            except ImportError:
                pass
        
        elif action_type == "generate":
            prompt_lower = prompt.lower()
            if "картинк" in prompt_lower or "селфи" in prompt_lower:
                try:
                    from generation import generate_image
                    img = generate_image(prompt)
                    if img:
                        answer += "\n\n🖼 Картинка сгенерирована!"
                except ImportError:
                    pass
            elif "музык" in prompt_lower or "песн" in prompt_lower:
                try:
                    from music import find_music
                    music = find_music(prompt)
                    if music:
                        answer += (
                            f"\n\n🎵 Найдено: {music.get('title', 'Неизвестно')} — "
                            f"{music.get('artist', 'Неизвестен')}"
                        )
                except ImportError:
                    pass
        
        elif action_type == "dox":
            try:
                from osint_engine import full_deep_dox
                query = prompt.replace("докс", "").replace("пробить", "").strip()
                if query:
                    full_deep_dox(query)
                    answer += f"\n\n🔍 Данные найдены. Используй 💟Докс {query} для просмотра."
            except ImportError:
                pass
        
        elif action_type == "game":
            if "игра" in prompt.lower() or "game" in prompt.lower():
                answer += "\n\n🎮 Давай поиграем! Напиши 💟Игры чтобы начать."
        
        elif action_type == "execute":
            if "статус" in prompt.lower():
                try:
                    from ai_request_handler import format_router_status
                    answer = format_router_status()
                except ImportError:
                    pass
    
    except Exception as e:
        print(f"⚠️ Ошибка выполнения действия: {e}")
        answer += f"\n\n⚠️ Не удалось выполнить действие: {e}"
    
    return answer

# ============================================================
# 11. СПЕЦИАЛЬНЫЕ ФУНКЦИИ (СОВМЕСТИМОСТЬ)
# ============================================================

def ask_for_rp(prompt, system_prompt=None, max_tokens=300, user_id=None):
    """RP-запрос"""
    return ask_ai(prompt, system_prompt, max_tokens=max_tokens, user_id=user_id)

def ask_for_chat(prompt, system_prompt=None, max_tokens=200, user_id=None):
    """Чат-запрос"""
    return ask_ai(prompt, system_prompt, max_tokens=max_tokens, user_id=user_id)

def ask_for_command(prompt, system_prompt=None, max_tokens=150, user_id=None):
    """Команда"""
    return ask_ai(prompt, system_prompt, max_tokens=max_tokens, user_id=user_id)

def ask_for_generation(prompt, system_prompt=None, max_tokens=400, user_id=None):
    """Генерация"""
    return ask_ai(prompt, system_prompt, max_tokens=max_tokens, user_id=user_id)

def ask_for_security(prompt, system_prompt=None, max_tokens=300, user_id=None):
    """Безопасность"""
    return ask_ai(prompt, system_prompt, max_tokens=max_tokens, user_id=user_id)

# ============================================================
# 12. СТАТУС
# ============================================================

def get_router_status():
    """Получить статус роутера"""
    try:
        from ai_model_manager import get_disabled_main_models
    except ImportError:
        def get_disabled_main_models():
            return {}
    
    try:
        from ai_key_rotator import get_key_stats_summary, get_all_openrouter_keys_status
    except ImportError:
        def get_key_stats_summary():
            return {}
        def get_all_openrouter_keys_status():
            return {}
    
    return {
        "active_models": get_active_main_models(),
        "disabled_models": get_disabled_main_models(),
        "key_summary": get_key_stats_summary(),
        "key_details": get_all_openrouter_keys_status(),
        "model_summary": get_model_stats_summary(),
        "autonomous_decisions": router_stats.get("autonomous_decisions", 0),
        "total_requests": router_stats.get("total_requests", 0),
    }

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🚀 Маршрутизатор ИИ (автономный) загружен")
print(f"🧠 Систмка принимает решения самостоятельно")
print(f"📊 Автономных решений: {router_stats.get('autonomous_decisions', 0)}")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")