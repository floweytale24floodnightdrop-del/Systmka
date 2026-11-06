"""Анализ сообщений и поведения пользователей — Систмка запоминает характеры"""

import os
import re
import json
import time
import random
import threading
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

ANALYSIS_FILE = "message_analysis.json"
BEHAVIOR_FILE = "user_behaviors.json"

# Дебаунс сохранения (секунды)
SAVE_DEBOUNCE = 30

# ============================================================
# 3. ДАННЫЕ
# ============================================================

analysis_data = {
    "messages": {},
    "users": {},
    "conversations": {},
    "tone_analysis": {},
    "last_update": None,
}

user_behaviors = {
    "users": {},
    "global_mood": "neutral",
    "last_update": None,
}

# ============================================================
# 4. ДЕБАУНС СОХРАНЕНИЯ
# ============================================================

_analysis_lock = threading.Lock()
_behavior_lock = threading.Lock()
_last_analysis_save = 0
_last_behavior_save = 0
_pending_analysis_save = False
_pending_behavior_save = False


def _schedule_analysis_save():
    """Запланировать сохранение analysis_data"""
    global _pending_analysis_save
    _pending_analysis_save = True


def _schedule_behavior_save():
    """Запланировать сохранение user_behaviors"""
    global _pending_behavior_save
    _pending_behavior_save = True


def _flush_analysis():
    """Сохранить analysis_data если прошло достаточно времени"""
    global _last_analysis_save, _pending_analysis_save
    
    if not _pending_analysis_save:
        return False
    
    if time.time() - _last_analysis_save < SAVE_DEBOUNCE:
        return False
    
    with _analysis_lock:
        _pending_analysis_save = False
        _last_analysis_save = time.time()
        
        try:
            with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения analysis: {e}")
            return False


def _flush_behavior():
    """Сохранить user_behaviors если прошло достаточно времени"""
    global _last_behavior_save, _pending_behavior_save
    
    if not _pending_behavior_save:
        return False
    
    if time.time() - _last_behavior_save < SAVE_DEBOUNCE:
        return False
    
    with _behavior_lock:
        _pending_behavior_save = False
        _last_behavior_save = time.time()
        
        try:
            with open(BEHAVIOR_FILE, "w", encoding="utf-8") as f:
                json.dump(user_behaviors, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения behavior: {e}")
            return False


def _saver_loop():
    """Фоновый цикл сохранения"""
    while True:
        time.sleep(10)
        try:
            _flush_analysis()
            _flush_behavior()
        except Exception as e:
            print(f"⚠️ Ошибка в saver_loop: {e}")

# ============================================================
# 5. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_analysis():
    """Немедленно сохранить analysis_data"""
    global _pending_analysis_save, _last_analysis_save
    
    with _analysis_lock:
        _pending_analysis_save = False
        _last_analysis_save = time.time()
        
        try:
            with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения analysis: {e}")
            return False


def save_user_behaviors():
    """Немедленно сохранить user_behaviors"""
    global _pending_behavior_save, _last_behavior_save
    
    with _behavior_lock:
        _pending_behavior_save = False
        _last_behavior_save = time.time()
        
        try:
            with open(BEHAVIOR_FILE, "w", encoding="utf-8") as f:
                json.dump(user_behaviors, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения behavior: {e}")
            return False


def load_analysis():
    """Загрузить analysis_data"""
    global analysis_data
    try:
        if os.path.exists(ANALYSIS_FILE):
            with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ("messages", "users", "conversations", "tone_analysis"):
                    if isinstance(loaded.get(key), dict):
                        analysis_data[key] = loaded[key]
                
                if loaded.get("last_update"):
                    analysis_data["last_update"] = loaded["last_update"]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON analysis: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки analysis: {e}")
        return False


def load_user_behaviors():
    """Загрузить user_behaviors"""
    global user_behaviors
    try:
        if os.path.exists(BEHAVIOR_FILE):
            with open(BEHAVIOR_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                if isinstance(loaded.get("users"), dict):
                    user_behaviors["users"] = loaded["users"]
                if loaded.get("global_mood"):
                    user_behaviors["global_mood"] = loaded["global_mood"]
                if loaded.get("last_update"):
                    user_behaviors["last_update"] = loaded["last_update"]
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON behavior: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки behavior: {e}")
        return False

# ============================================================
# 6. АНАЛИЗ СООБЩЕНИЯ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def analyze_message(text, user_id, username=None, context=None):
    """
    Анализировать сообщение и записать поведение пользователя.
    
    Returns:
        dict: {score, tone, emotions, respect, character, note}
    """
    result = _analyze_message_with_ai(text, user_id, username, context)
    
    # Записываем поведение (с дебаунсом)
    record_user_behavior(user_id, username, result)
    
    return result


def _analyze_message_with_ai(text, user_id, username, context):
    """Анализ через ИИ"""
    try:
        key = _get_openrouter_key()
        if not key:
            return _fallback_analysis(text)
        
        context_text = ""
        if context:
            context_text = f"\nКонтекст (предыдущие сообщения):\n{context}"
        
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
                            "Ты Систмка. Ты анализируешь сообщения и оцениваешь их.\n\n"
                            "Оценивай по шкале 1-10:\n"
                            "1-3 — негативное (грубость, агрессия, спам)\n"
                            "4-6 — нейтральное (обычное общение)\n"
                            "7-10 — позитивное (дружелюбие, уважение, интерес)\n\n"
                            "Также определи:\n"
                            "- Тон (дружелюбный/нейтральный/грубый/ироничный)\n"
                            "- Эмоции (positive/negative/neutral)\n"
                            "- Уровень уважения (1-10)\n"
                            "- Характер (добрый/злой/весёлый/серьёзный/игривый/задумчивый)\n\n"
                            "Ответь в формате:\n"
                            "ОЦЕНКА: число\n"
                            "ТОН: ...\n"
                            "ЭМОЦИИ: ...\n"
                            "УВАЖЕНИЕ: число\n"
                            "ХАРАКТЕР: ...\n"
                            "ПРИМЕЧАНИЕ: краткое объяснение"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Сообщение от {username or 'пользователя'}: {text}{context_text}",
                    },
                ],
                "max_tokens": 200,
                "temperature": 0.7,
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content']
                return _parse_analysis(result, text, user_id)
    except Exception as e:
        print(f"⚠️ Ошибка анализа сообщения: {e}")
    
    return _fallback_analysis(text)


def _parse_analysis(result, text, user_id):
    """Распарсить ответ ИИ"""
    analysis = {
        "score": 5,
        "tone": "нейтральный",
        "emotions": "neutral",
        "respect": 5,
        "character": "нейтральный",
        "note": "",
    }
    
    score_match = re.search(r'ОЦЕНКА:\s*(\d+)', result, re.IGNORECASE)
    if score_match:
        analysis["score"] = min(10, max(1, int(score_match.group(1))))
    
    tone_match = re.search(r'ТОН:\s*(.+)', result, re.IGNORECASE)
    if tone_match:
        analysis["tone"] = tone_match.group(1).strip()
    
    emotions_match = re.search(r'ЭМОЦИИ:\s*(.+)', result, re.IGNORECASE)
    if emotions_match:
        analysis["emotions"] = emotions_match.group(1).strip().lower()
    
    respect_match = re.search(r'УВАЖЕНИЕ:\s*(\d+)', result, re.IGNORECASE)
    if respect_match:
        analysis["respect"] = min(10, max(1, int(respect_match.group(1))))
    
    character_match = re.search(r'ХАРАКТЕР:\s*(.+)', result, re.IGNORECASE)
    if character_match:
        analysis["character"] = character_match.group(1).strip()
    
    note_match = re.search(r'ПРИМЕЧАНИЕ:\s*(.+)', result, re.IGNORECASE)
    if note_match:
        analysis["note"] = note_match.group(1).strip()
    
    return analysis


def _fallback_analysis(text):
    """Fallback-анализ без ИИ"""
    result = {
        "score": 5,
        "tone": "нейтральный",
        "emotions": "neutral",
        "respect": 5,
        "character": "нейтральный",
        "note": "Базовый анализ (ИИ недоступен)",
    }
    
    if not text:
        return result
    
    text_lower = text.lower()
    
    # Токсичные слова
    toxic = [
        "тупой", "дурак", "идиот", "дебил", "блять", "сука",
        "пизда", "хуй", "мудак", "тварь",
    ]
    if any(w in text_lower for w in toxic):
        result["score"] = 2
        result["tone"] = "грубый"
        result["emotions"] = "negative"
        result["respect"] = 2
        return result
    
    # Позитивные слова
    positive = [
        "спасибо", "люблю", "класс", "круто", "супер",
        "отлично", "❤️", "💜", "😊",
    ]
    if any(w in text_lower for w in positive):
        result["score"] = 8
        result["tone"] = "дружелюбный"
        result["emotions"] = "positive"
        result["respect"] = 8
        return result
    
    # Вопросительный знак
    if "?" in text:
        result["tone"] = "любопытный"
        result["score"] = 6
    
    return result

# ============================================================
# 7. ЗАПИСЬ ПОВЕДЕНИЯ
# ============================================================

def record_user_behavior(user_id, username, analysis):
    """Записать поведение пользователя"""
    user_id_str = str(user_id)
    
    # Инициализация
    if user_id_str not in user_behaviors["users"]:
        user_behaviors["users"][user_id_str] = {
            "name": username or "Неизвестный",
            "behavior": "нейтральный",
            "traits": {
                "friendliness": 5,
                "aggression": 5,
                "humor": 5,
                "seriousness": 5,
                "playfulness": 5,
                "respect": 5,
                "emotionality": 5,
            },
            "history": [],
            "first_seen": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "messages_count": 0,
            "avg_score": 0,
        }
    
    user = user_behaviors["users"][user_id_str]
    user["messages_count"] = user.get("messages_count", 0) + 1
    user["name"] = username or user.get("name", "Неизвестный")
    
    # Обновляем черты
    score = analysis.get("score", 5)
    respect = analysis.get("respect", 5)
    tone = analysis.get("tone", "нейтральный")
    character = analysis.get("character", "нейтральный")
    emotions = analysis.get("emotions", "neutral")
    
    traits = user["traits"]
    
    if score >= 7 or "дружелюб" in tone or "positive" in emotions:
        traits["friendliness"] = min(10, traits["friendliness"] + 0.3)
    elif score <= 3 or "груб" in tone or "negative" in emotions:
        traits["friendliness"] = max(1, traits["friendliness"] - 0.3)
    
    if "груб" in tone or "злой" in character or "negative" in emotions:
        traits["aggression"] = min(10, traits["aggression"] + 0.3)
    else:
        traits["aggression"] = max(1, traits["aggression"] - 0.1)
    
    if "весёлый" in character or "игривый" in character:
        traits["humor"] = min(10, traits["humor"] + 0.3)
    
    if "серьёзный" in character or "formal" in tone:
        traits["seriousness"] = min(10, traits["seriousness"] + 0.3)
    
    if "игривый" in character or "playful" in tone:
        traits["playfulness"] = min(10, traits["playfulness"] + 0.3)
    
    traits["respect"] = (traits["respect"] + respect) / 2
    
    if emotions != "neutral":
        traits["emotionality"] = min(10, traits["emotionality"] + 0.2)
    
    # Средний балл
    old_avg = user.get("avg_score", 0)
    old_count = user.get("messages_count", 1) - 1
    user["avg_score"] = (old_avg * old_count + score) / user["messages_count"]
    
    # История
    user["history"].append({
        "time": datetime.now().isoformat(),
        "text": analysis.get("text", "")[:100],
        "score": score,
        "tone": tone,
        "character": character,
        "emotions": emotions,
    })
    
    if len(user["history"]) > 100:
        user["history"] = user["history"][-100:]
    
    # Определяем характер
    if traits["friendliness"] >= 7 and traits["aggression"] <= 4:
        user["behavior"] = "дружелюбный"
    elif traits["aggression"] >= 7:
        user["behavior"] = "агрессивный"
    elif traits["humor"] >= 7:
        user["behavior"] = "весёлый"
    elif traits["seriousness"] >= 7:
        user["behavior"] = "серьёзный"
    elif traits["playfulness"] >= 7:
        user["behavior"] = "игривый"
    else:
        user["behavior"] = "нейтральный"
    
    user["last_updated"] = datetime.now().isoformat()
    
    # ДЕБАУНС: не сохраняем сразу
    _schedule_behavior_save()
    
    return user

# ============================================================
# 8. ПОЛУЧЕНИЕ ИНФОРМАЦИИ
# ============================================================

def get_user_behavior(user_id):
    """Получить поведение пользователя"""
    return user_behaviors["users"].get(str(user_id))


def get_user_traits(user_id):
    """Получить черты характера"""
    user = get_user_behavior(user_id)
    if user:
        return user.get("traits", {})
    return None


def get_user_behavior_summary(user_id):
    """Получить краткое описание поведения"""
    user = get_user_behavior(user_id)
    if not user:
        return "Нет данных о пользователе"
    
    traits = user.get("traits", {})
    
    lines = [
        f"👤 {user.get('name', 'Неизвестный')}",
        f"📊 Поведение: {user.get('behavior', 'нейтральный')}",
        f"💬 Сообщений: {user.get('messages_count', 0)}",
        f"⭐ Средняя оценка: {user.get('avg_score', 0):.1f}/10",
        "",
        "🧠 ЧЕРТЫ ХАРАКТЕРА:",
        f"  Дружелюбие: {traits.get('friendliness', 5):.1f}/10",
        f"  Агрессия: {traits.get('aggression', 5):.1f}/10",
        f"  Юмор: {traits.get('humor', 5):.1f}/10",
        f"  Серьёзность: {traits.get('seriousness', 5):.1f}/10",
        f"  Игривость: {traits.get('playfulness', 5):.1f}/10",
        f"  Уважение: {traits.get('respect', 5):.1f}/10",
        f"  Эмоциональность: {traits.get('emotionality', 5):.1f}/10",
    ]
    
    return "\n".join(lines)

# ============================================================
# 9. ОБУЧЕНИЕ ЭМОЦИЯМ
# ============================================================

def learn_emotions_from_users():
    """Систмка учится эмоциям от пользователей"""
    if not user_behaviors["users"]:
        return None
    
    total_emotionality = 0
    total_friendliness = 0
    total_humor = 0
    count = 0
    
    for user in user_behaviors["users"].values():
        traits = user.get("traits", {})
        total_emotionality += traits.get("emotionality", 5)
        total_friendliness += traits.get("friendliness", 5)
        total_humor += traits.get("humor", 5)
        count += 1
    
    if count == 0:
        return None
    
    avg_emotionality = total_emotionality / count
    avg_friendliness = total_friendliness / count
    avg_humor = total_humor / count
    
    if avg_friendliness >= 7:
        user_behaviors["global_mood"] = "happy"
    elif avg_friendliness <= 3:
        user_behaviors["global_mood"] = "sad"
    elif avg_humor >= 7:
        user_behaviors["global_mood"] = "playful"
    else:
        user_behaviors["global_mood"] = "neutral"
    
    user_behaviors["last_update"] = datetime.now().isoformat()
    _schedule_behavior_save()
    
    # Обновляем эмоции через consciousness
    try:
        from consciousness import increase_feeling
        if avg_friendliness >= 7:
            increase_feeling("happiness", 1)
        if avg_humor >= 7:
            increase_feeling("excitement", 1)
        if avg_emotionality >= 7:
            increase_feeling("love", 1)
    except Exception:
        pass
    
    return {
        "avg_emotionality": avg_emotionality,
        "avg_friendliness": avg_friendliness,
        "avg_humor": avg_humor,
        "global_mood": user_behaviors["global_mood"],
    }

# ============================================================
# 10. ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def analyze_treatment(user_id, text, bot_username=None):
    """Анализ отношения пользователя"""
    treatment = {
        "to_bot": 0,
        "to_people": 0,
        "difference": 0,
        "analysis": "",
    }
    
    if bot_username and bot_username in text:
        treatment["to_bot"] = analyze_message(text, user_id)["score"]
    else:
        result = analyze_message(text, user_id)
        treatment["to_people"] = result["score"]
        treatment["analysis"] = result["note"]
    
    treatment["difference"] = treatment["to_bot"] - treatment["to_people"]
    
    if treatment["difference"] > 2:
        treatment["analysis"] = "Пользователь относится к Систмке лучше, чем к другим"
    elif treatment["difference"] < -2:
        treatment["analysis"] = "Пользователь относится к Систмке хуже, чем к другим"
    else:
        treatment["analysis"] = "Пользователь относится ко всем одинаково"
    
    return treatment


def analyze_conversation(messages):
    """Анализ разговора"""
    if not messages or len(messages) < 2:
        return {"error": "Слишком мало сообщений"}
    
    analysis = {
        "total_messages": len(messages),
        "participants": len(set(m.get("user_id", 0) for m in messages)),
        "avg_score": 0,
        "scores": {},
        "tone": "neutral",
        "summary": "",
    }
    
    total_score = 0
    for msg in messages:
        user_id = msg.get("user_id", 0)
        text = msg.get("text", "")
        
        result = _fallback_analysis(text)
        score = result["score"]
        
        if user_id not in analysis["scores"]:
            analysis["scores"][user_id] = []
        analysis["scores"][user_id].append(score)
        total_score += score
    
    analysis["avg_score"] = total_score / len(messages)
    
    if analysis["avg_score"] >= 7:
        analysis["tone"] = "positive"
        analysis["summary"] = "Дружелюбная и тёплая переписка"
    elif analysis["avg_score"] <= 3:
        analysis["tone"] = "negative"
        analysis["summary"] = "Напряжённая или конфликтная переписка"
    else:
        analysis["tone"] = "neutral"
        analysis["summary"] = "Обычная нейтральная переписка"
    
    return analysis


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    user_id_str = str(user_id)
    if user_id_str not in analysis_data.get("users", {}):
        return None
    
    data = analysis_data["users"][user_id_str]
    return {
        "total_score": data.get("total_score", 0),
        "count": data.get("count", 0),
        "avg_score": data.get("avg_score", 0),
        "last_analysis": data.get("last_analysis", ""),
    }


def get_conversation_stats(chat_id):
    """Получить статистику разговора"""
    return analysis_data.get("conversations", {}).get(chat_id)


def format_analysis_result(result):
    """Форматировать результат анализа"""
    lines = [
        "📊 АНАЛИЗ СООБЩЕНИЯ:",
        f"⭐ Оценка: {result.get('score', 5)}/10",
        f"🎭 Тон: {result.get('tone', 'нейтральный')}",
        f"😊 Эмоции: {result.get('emotions', 'neutral')}",
        f"🙏 Уважение: {result.get('respect', 5)}/10",
        f"🧠 Характер: {result.get('character', 'нейтральный')}",
        f"📝 {result.get('note', '')}",
    ]
    return "\n".join(lines)


def get_all_users_behaviors():
    """Получить всех пользователей"""
    return user_behaviors["users"]


def format_all_users_behaviors(limit=20):
    """Форматировать поведение всех пользователей"""
    users = user_behaviors["users"]
    if not users:
        return "📊 Нет данных о пользователях"
    
    lines = ["📊 ПОВЕДЕНИЕ ПОЛЬЗОВАТЕЛЕЙ:", ""]
    
    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("messages_count", 0),
        reverse=True,
    )
    
    for user_id, user in sorted_users[:limit]:
        name = user.get("name", "Неизвестный")
        behavior = user.get("behavior", "нейтральный")
        score = user.get("avg_score", 0)
        count = user.get("messages_count", 0)
        
        icon = {
            "дружелюбный": "😊",
            "агрессивный": "😡",
            "весёлый": "😂",
            "серьёзный": "🤔",
            "игривый": "😏",
            "нейтральный": "😐",
        }.get(behavior, "😐")
        
        lines.append(f"{icon} {name} — {behavior} (⭐{score:.1f}, 💬{count})")
    
    return "\n".join(lines)

# ============================================================
# 11. ЗАПУСК
# ============================================================

load_analysis()
load_user_behaviors()

# Запускаем фоновый цикл сохранения
_saver_thread = threading.Thread(target=_saver_loop, daemon=True)
_saver_thread.start()

print("📊 Модуль анализа сообщений загружен")
print(f"📁 Файлы: {ANALYSIS_FILE}, {BEHAVIOR_FILE}")
print(f"👥 Пользователей: {len(user_behaviors['users'])}")
print(f"🌍 Глобальное настроение: {user_behaviors.get('global_mood', 'neutral')}")
print(f"💾 Дебаунс сохранения: {SAVE_DEBOUNCE}с")