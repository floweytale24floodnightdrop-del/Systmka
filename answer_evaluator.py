"""Реальная оценка ответов Систмки — сравнение с другими, подстройка под пользователя"""

import os
import json
import random
import requests
from datetime import datetime
from collections import defaultdict
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

EVALUATION_FILE = "answer_evaluations.json"

evaluation_data = {
    "users": {},          # {user_id: {"style": str, "trust": float, "interactions": int, "avg_score": float}}
    "answers": [],        # [{user_id, question, answer, score, criteria, time}]
    "styles": {           # Стили общения, которые Систмка может использовать
        "friendly": {"warmth": 8, "formality": 2, "humor": 7, "sarcasm": 3},
        "formal": {"warmth": 3, "formality": 9, "humor": 2, "sarcasm": 1},
        "playful": {"warmth": 7, "formality": 1, "humor": 9, "sarcasm": 6},
        "sarcastic": {"warmth": 4, "formality": 3, "humor": 8, "sarcasm": 9},
        "neutral": {"warmth": 5, "formality": 5, "humor": 5, "sarcasm": 5},
        "professional": {"warmth": 4, "formality": 8, "humor": 3, "sarcasm": 2},
    },
    "stats": {
        "total_evaluations": 0,
        "avg_score": 0,
        "high_scores": 0,
        "low_scores": 0,
    }
}

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_evaluation_data():
    try:
        with open(EVALUATION_FILE, "w", encoding="utf-8") as f:
            json.dump(evaluation_data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_evaluation_data():
    global evaluation_data
    try:
        if os.path.exists(EVALUATION_FILE):
            with open(EVALUATION_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                evaluation_data.update(loaded)
        return True
    except:
        return False

load_evaluation_data()

# ============================================================
# 3. ОЦЕНКА ОТВЕТА ПО КРИТЕРИЯМ
# ============================================================

def evaluate_answer(question, answer, user_id, context=None):
    """Оценить ответ Систмки по 10 критериям"""
    
    criteria = {
        "relevance": 0,      # Соответствие вопросу
        "clarity": 0,        # Понятность
        "length": 0,         # Длина (не слишком коротко/длинно)
        "humanity": 0,       # Человечность (не ИИ-шность)
        "emotion": 0,        # Эмоциональность
        "humor": 0,          # Юмор
        "sarcasm": 0,        # Сарказм (умеренный)
        "respect": 0,        # Уважение к пользователю
        "helpfulness": 0,    # Полезность
        "uniqueness": 0,     # Уникальность (не шаблонность)
    }
    
    # 1. Relevance — соответствие вопросу
    if question and answer:
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words & answer_words)
        criteria["relevance"] = min(10, (overlap / max(1, len(question_words))) * 10 + 2)
    
    # 2. Clarity — понятность
    if answer:
        sentences = answer.count('.') + answer.count('!') + answer.count('?')
        if sentences >= 2:
            criteria["clarity"] = 8
        elif sentences >= 1:
            criteria["clarity"] = 6
        else:
            criteria["clarity"] = 4
    
    # 3. Length — длина
    words = len(answer.split()) if answer else 0
    if 10 <= words <= 50:
        criteria["length"] = 9
    elif 5 <= words <= 80:
        criteria["length"] = 7
    elif 3 <= words <= 100:
        criteria["length"] = 5
    else:
        criteria["length"] = 3
    
    # 4. Humanity — человечность (не ИИ-шность)
    ai_phrases = ["чем могу помочь", "обращайтесь", "я здесь чтобы помочь", "рада помочь", "я всего лишь"]
    human_phrases = ["ага", "ну", "хм", "ой", "ээ", "крч", "типа", "прикол", "кек"]
    
    ai_score = sum(1 for p in ai_phrases if p in answer.lower()) * 2
    human_score = sum(1 for p in human_phrases if p in answer.lower()) * 2
    
    criteria["humanity"] = max(1, min(10, 5 + human_score - ai_score))
    
    # 5. Emotion — эмоциональность
    emotion_words = ["❤️", "💜", "😊", "🥺", "😢", "🔥", "😈", "🤘", "😎", "💔", "🥰", "🫶"]
    criteria["emotion"] = min(10, sum(1 for e in emotion_words if e in answer))
    
    # 6. Humor — юмор
    humor_words = ["😂", "🤣", "лол", "кек", "хаха", "смешно", "ржака", "угар", "прикол"]
    criteria["humor"] = min(10, sum(1 for h in humor_words if h in answer.lower()) * 2)
    
    # 7. Sarcasm — сарказм
    sarcasm_words = ["ага", "ну-ну", "конечно", "ясно", "ха-ха", "ну да", "разумеется"]
    criteria["sarcasm"] = min(10, sum(1 for s in sarcasm_words if s in answer.lower()) * 1.5)
    
    # 8. Respect — уважение
    if user_id in evaluation_data["users"]:
        user_data = evaluation_data["users"][user_id]
        if user_data.get("trust", 0) > 5:
            criteria["respect"] = 8
        else:
            criteria["respect"] = 5
    else:
        criteria["respect"] = 6
    
    # 9. Helpfulness — полезность
    helpful_words = ["вот", "так", "это", "можно", "нужно", "попробуй", "сделай", "посмотри"]
    criteria["helpfulness"] = min(10, sum(1 for h in helpful_words if h in answer.lower()) + 3)
    
    # 10. Uniqueness — уникальность
    if len(answer) > 20:
        criteria["uniqueness"] = min(10, len(set(answer.split())) / max(1, len(answer.split())) * 5 + 3)
    else:
        criteria["uniqueness"] = 5
    
    # Итоговый балл
    total_score = sum(criteria.values()) / 10
    
    # Сохраняем оценку
    evaluation_data["answers"].append({
        "user_id": user_id,
        "question": question[:100],
        "answer": answer[:200],
        "score": total_score,
        "criteria": criteria,
        "time": datetime.now().isoformat()
    })
    
    if len(evaluation_data["answers"]) > 500:
        evaluation_data["answers"] = evaluation_data["answers"][-500:]
    
    # Обновляем статистику пользователя
    if user_id not in evaluation_data["users"]:
        evaluation_data["users"][user_id] = {
            "style": "neutral",
            "trust": 5.0,
            "interactions": 0,
            "avg_score": 0,
            "scores_history": []
        }
    
    user_data = evaluation_data["users"][user_id]
    user_data["interactions"] += 1
    user_data["scores_history"].append(total_score)
    if len(user_data["scores_history"]) > 50:
        user_data["scores_history"] = user_data["scores_history"][-50:]
    user_data["avg_score"] = sum(user_data["scores_history"]) / len(user_data["scores_history"])
    
    # Обновляем общую статистику
    evaluation_data["stats"]["total_evaluations"] += 1
    evaluation_data["stats"]["avg_score"] = (
        (evaluation_data["stats"]["avg_score"] * (evaluation_data["stats"]["total_evaluations"] - 1) + total_score) /
        evaluation_data["stats"]["total_evaluations"]
    )
    
    if total_score >= 7:
        evaluation_data["stats"]["high_scores"] += 1
    elif total_score <= 3:
        evaluation_data["stats"]["low_scores"] += 1
    
    # Обновляем стиль пользователя
    update_user_style(user_id)
    
    save_evaluation_data()
    
    return total_score, criteria

# ============================================================
# 4. ОПРЕДЕЛЕНИЕ СТИЛЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def update_user_style(user_id):
    """Обновить стиль общения пользователя на основе оценок"""
    if user_id not in evaluation_data["users"]:
        return
    
    user_data = evaluation_data["users"][user_id]
    recent_scores = user_data.get("scores_history", [])[-20:]
    
    if len(recent_scores) < 3:
        return
    
    avg = sum(recent_scores) / len(recent_scores)
    
    # Определяем стиль
    if avg >= 8:
        user_data["style"] = "friendly"
        user_data["trust"] = min(10, user_data.get("trust", 5) + 0.5)
    elif avg >= 6:
        user_data["style"] = "neutral"
        user_data["trust"] = min(10, user_data.get("trust", 5) + 0.2)
    elif avg >= 4:
        user_data["style"] = "professional"
        user_data["trust"] = max(1, user_data.get("trust", 5) - 0.2)
    else:
        user_data["style"] = "sarcastic"
        user_data["trust"] = max(1, user_data.get("trust", 5) - 0.5)
    
    save_evaluation_data()

# ============================================================
# 5. СРАВНЕНИЕ С ДРУГИМИ ПОЛЬЗОВАТЕЛЯМИ
# ============================================================

def compare_with_others(user_id, answer_score):
    """Сравнить оценку с оценками других пользователей"""
    all_scores = [a.get("score", 0) for a in evaluation_data["answers"] if a.get("user_id") != user_id]
    
    if not all_scores:
        return "Нет данных для сравнения"
    
    avg_others = sum(all_scores) / len(all_scores)
    diff = answer_score - avg_others
    
    if diff > 2:
        return f"Лучше, чем у других (на {diff:.1f} балла)"
    elif diff > 0.5:
        return f"Немного лучше других (на {diff:.1f} балла)"
    elif diff > -0.5:
        return "Так же, как и у других"
    elif diff > -2:
        return f"Немного хуже других (на {abs(diff):.1f} балла)"
    else:
        return f"Хуже, чем у других (на {abs(diff):.1f} балла)"

# ============================================================
# 6. ПОДСТРОЙКА ПОД ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_style_for_user(user_id):
    """Получить стиль общения для пользователя"""
    if user_id in evaluation_data["users"]:
        style = evaluation_data["users"][user_id].get("style", "neutral")
        return evaluation_data["styles"].get(style, evaluation_data["styles"]["neutral"])
    return evaluation_data["styles"]["neutral"]

def should_adapt_to_user(user_id):
    """Должна ли Систмка подстраиваться под пользователя"""
    if user_id not in evaluation_data["users"]:
        return True  # По умолчанию подстраиваемся
    
    user_data = evaluation_data["users"][user_id]
    trust = user_data.get("trust", 5)
    interactions = user_data.get("interactions", 0)
    
    # Подстраиваемся если доверие высокое или было много взаимодействий
    if trust >= 6 or interactions >= 10:
        return True
    return False

# ============================================================
# 7. ПОЛУЧЕНИЕ СТАТИСТИКИ
# ============================================================

def get_user_evaluation_stats(user_id):
    if user_id not in evaluation_data["users"]:
        return None
    
    user_data = evaluation_data["users"][user_id]
    return {
        "style": user_data.get("style", "neutral"),
        "trust": user_data.get("trust", 5),
        "interactions": user_data.get("interactions", 0),
        "avg_score": user_data.get("avg_score", 0),
        "recent_scores": user_data.get("scores_history", [])[-10:],
    }

def get_global_evaluation_stats():
    return {
        "total_evaluations": evaluation_data["stats"]["total_evaluations"],
        "avg_score": evaluation_data["stats"]["avg_score"],
        "high_scores": evaluation_data["stats"]["high_scores"],
        "low_scores": evaluation_data["stats"]["low_scores"],
        "users_tracked": len(evaluation_data["users"]),
    }

def format_evaluation_stats():
    stats = get_global_evaluation_stats()
    lines = [
        "📊 СТАТИСТИКА ОЦЕНОК:",
        f"📝 Всего оценок: {stats['total_evaluations']}",
        f"⭐ Средний балл: {stats['avg_score']:.1f}/10",
        f"✅ Высоких оценок (>7): {stats['high_scores']}",
        f"❌ Низких оценок (<3): {stats['low_scores']}",
        f"👤 Отслеживается пользователей: {stats['users_tracked']}",
    ]
    return "\n".join(lines)

print("📊 Модуль оценки ответов загружен")
print(f"📝 Всего оценок: {evaluation_data['stats']['total_evaluations']}")
print(f"👤 Пользователей в системе: {len(evaluation_data['users'])}")