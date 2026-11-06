"""Саморефлексия Систмки — анализ ответов, оценка, подстройка под пользователя, умное удаление"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime, timedelta

# ============================================================
# 0. ОБЁРТКА UTF-8 УБРАНА
# ============================================================
# ВАЖНО: обёртка sys.stdout должна быть ТОЛЬКО в auto_start.py
# (или в bot.py, если он запускается отдельно).
#
# Если обернуть sys.stdout второй раз — старая обёртка закрывается
# автоматически, вместе с buffer, и любой print() падает с
# ValueError: I/O operation on closed file.

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ОПЦИОНАЛЬНЫЙ ИМПОРТ answer_evaluator
# ============================================================

try:
    from answer_evaluator import (
        evaluate_answer,
        get_style_for_user,
        should_adapt_to_user,
        compare_with_others,
    )
    ANSWER_EVALUATOR_AVAILABLE = True
except ImportError:
    ANSWER_EVALUATOR_AVAILABLE = False
    print("⚠️ answer_evaluator не найден, использую встроенную оценку")

# ============================================================
# 3. НАСТРОЙКИ
# ============================================================

REFLECTION_FILE = "reflections.json"
MAX_REFLECTIONS = 50
DELETE_OLD_AFTER_DAYS = 30

# ============================================================
# 4. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================

reflections = []

reflection_settings = {
    "auto_reflect": True,
    "min_quality_to_reflect": 4,
    "max_reflections": 50,
    "delete_old_after_days": 30,
    "adapt_to_users": True,
    "delete_unwanted_immediately": True,
}

# ============================================================
# 5. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_reflections():
    """Сохранить рефлексии в файл"""
    try:
        with open(REFLECTION_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "reflections": reflections,
                    "settings": reflection_settings,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения рефлексий: {e}")
        return False


def load_reflections():
    """
    Загрузить рефлексии из файла.
    
    ВАЖНО: поддерживает ДВА формата:
    1. Старый: просто список [ ... ]
    2. Новый: словарь { "reflections": [...], "settings": {...} }
    """
    global reflections, reflection_settings
    try:
        if os.path.exists(REFLECTION_FILE):
            with open(REFLECTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # === ФОРМАТ 1: старый (просто список) ===
            if isinstance(data, list):
                print(f"⚠️ reflections.json в старом формате (список) — конвертирую")
                reflections = data
                # settings не трогаем — остаются дефолтные
            
            # === ФОРМАТ 2: новый (словарь) ===
            elif isinstance(data, dict):
                # reflections
                loaded_reflections = data.get("reflections", [])
                if isinstance(loaded_reflections, list):
                    reflections = loaded_reflections
                else:
                    print(f"⚠️ reflections в JSON не список — сброшено")
                    reflections = []
                
                # settings
                loaded_settings = data.get("settings", {})
                if isinstance(loaded_settings, dict):
                    reflection_settings.update(loaded_settings)
            
            # === ФОРМАТ 3: неизвестный ===
            else:
                print(f"⚠️ reflections.json неизвестный формат ({type(data).__name__}) — сброшено")
                reflections = []
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON рефлексий: {e}")
        reflections = []
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки рефлексий: {e}")
        reflections = []
        return False


load_reflections()

# ============================================================
# 6. ВСТРОЕННАЯ ОЦЕНКА (ЕСЛИ ANSWER_EVALUATOR НЕТ)
# ============================================================

def builtin_evaluate_answer(question, answer, user_id=None):
    """
    Встроенная оценка ответа.
    
    ВАЖНО: возвращает КОРТЕЖ (score, criteria),
    чтобы совпадать с API answer_evaluator.
    """
    score = 5.0
    criteria = {
        "relevance": 5,
        "clarity": 5,
        "length": 5,
        "humanity": 5,
        "emotion": 5,
        "humor": 5,
        "sarcasm": 5,
        "respect": 5,
        "helpfulness": 5,
        "uniqueness": 5,
    }
    
    if not answer:
        return 1.0, criteria
    
    # Длина
    words = len(answer.split())
    if 10 <= words <= 50:
        criteria["length"] = 9
        score += 0.5
    elif 5 <= words <= 80:
        criteria["length"] = 7
    else:
        criteria["length"] = 4
    
    # Человечность
    ai_phrases = ["чем могу помочь", "обращайтесь", "я здесь чтобы помочь", "рада помочь"]
    human_phrases = ["ага", "ну", "хм", "ой", "ээ", "крч", "типа"]
    
    if any(p in answer.lower() for p in ai_phrases):
        criteria["humanity"] = 3
        score -= 1
    if any(p in answer.lower() for p in human_phrases):
        criteria["humanity"] = 8
        score += 0.5
    
    return max(1.0, min(10.0, score)), criteria


def builtin_get_style_for_user(user_id):
    """Встроенное получение стиля пользователя"""
    return {"warmth": 5, "formality": 5, "humor": 5, "sarcasm": 5}


def builtin_should_adapt_to_user(user_id):
    """Встроенное определение адаптации"""
    return True


def builtin_compare_with_others(user_id, score):
    """Встроенное сравнение"""
    return "Нет данных для сравнения"

# ============================================================
# 7. ВЫБОР ФУНКЦИЙ
# ============================================================

if ANSWER_EVALUATOR_AVAILABLE:
    evaluate_answer_func = evaluate_answer
    get_style_func = get_style_for_user
    should_adapt_func = should_adapt_to_user
    compare_func = compare_with_others
else:
    evaluate_answer_func = builtin_evaluate_answer
    get_style_func = builtin_get_style_for_user
    should_adapt_func = builtin_should_adapt_to_user
    compare_func = builtin_compare_with_others

# ============================================================
# 8. БЕЗОПАСНАЯ РАСПАКОВКА РЕЗУЛЬТАТА ОЦЕНКИ
# ============================================================

def _safe_parse_evaluation(result, question, answer, user_id):
    """
    Безопасно распарсить результат evaluate_answer_func.
    
    Поддерживает оба формата:
    - tuple (score, criteria)
    - dict {score, criteria, ...}
    
    Returns:
        tuple: (score, criteria, extra_issues)
    """
    score = 5.0
    criteria = {}
    issues = []
    
    if isinstance(result, tuple) and len(result) >= 2:
        # Формат answer_evaluator: (score, criteria)
        score = result[0]
        criteria = result[1] if isinstance(result[1], dict) else {}
    
    elif isinstance(result, dict):
        # Формат builtin: {score, criteria, issues, ...}
        score = result.get("score", 5.0)
        criteria = result.get("criteria", {})
        issues = result.get("issues", [])
    
    else:
        # Неизвестный формат — базовый score
        try:
            score = float(result)
        except (ValueError, TypeError):
            score = 5.0
    
    return float(score), criteria, issues


def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 9. УМНОЕ УДАЛЕНИЕ РЕФЛЕКСИЙ
# ============================================================

def should_delete_reflection(reflection):
    """Определить, нужно ли удалить рефлексию"""
    if not isinstance(reflection, dict):
        return True, "Невалидная рефлексия"
    
    # Автоудаление плохих
    if reflection_settings.get("delete_unwanted_immediately", True):
        analysis = reflection.get("analysis", {})
        
        # analysis может быть dict или list
        if isinstance(analysis, dict):
            score = analysis.get("score", 5)
            
            if score < 3:
                return True, "Низкое качество ответа"
            
            if analysis.get("is_ai_like", False):
                return True, "Слишком ИИ-шный ответ"
            
            issues = analysis.get("issues", [])
            critical_issues = [
                "слишком короткий ответ",
                "нет вопроса в ответе",
                "использованы ИИ-фразы",
            ]
            if any(issue in issues for issue in critical_issues):
                return True, f"Критические проблемы: {', '.join(issues)}"
    
    # Устаревшие
    try:
        ref_time = datetime.fromisoformat(reflection.get("time", "2000-01-01"))
        days_old = (datetime.now() - ref_time).days
        
        if days_old > reflection_settings.get("delete_old_after_days", 30):
            return True, f"Устарело ({days_old} дней)"
        
        if days_old > 7:
            score = reflection.get("analysis", {}).get("score", 5)
            if score < 5:
                return True, f"Устарело и низкое качество ({days_old} дней, оценка {score})"
    except Exception as e:
        print(f"⚠️ Ошибка проверки возраста: {e}")
    
    # Дубликаты
    if len(reflections) > 10:
        current_text = reflection.get("answer", "")[:50]
        duplicates = 0
        for ref in reflections[-20:]:
            if ref.get("answer", "")[:50] == current_text:
                duplicates += 1
        if duplicates > 3:
            return True, "Слишком много дубликатов"
    
    return False, None


def smart_cleanup():
    """Умная очистка рефлексий"""
    global reflections
    
    deleted = []
    kept = []
    
    for ref in reflections:
        if not isinstance(ref, dict):
            continue
        should_delete, reason = should_delete_reflection(ref)
        if should_delete:
            deleted.append({"ref": ref, "reason": reason})
        else:
            kept.append(ref)
    
    reflections = kept
    
    # Лимит
    if len(reflections) > reflection_settings.get("max_reflections", 50):
        reflections.sort(key=lambda x: x.get("time", "2000-01-01"))
        excess = len(reflections) - reflection_settings.get("max_reflections", 50)
        deleted_old = reflections[:excess]
        reflections = reflections[excess:]
        
        for ref in deleted_old:
            deleted.append({"ref": ref, "reason": "Превышение лимита"})
    
    if deleted:
        print(f"🗑 Удалено рефлексий: {len(deleted)}")
        for d in deleted[:5]:
            print(f"  • {d['reason']}: {d['ref'].get('answer', '')[:50]}...")
    
    save_reflections()
    return deleted

# ============================================================
# 10. АНАЛИЗ ОТВЕТА
# ============================================================

def analyze_answer_quality(question, answer, user_id=None):
    """
    Проанализировать качество ответа.
    
    Returns:
        dict: {score, criteria, issues, needs_improvement, is_ai_like, comparison, user_id}
    """
    try:
        if user_id is not None:
            result = evaluate_answer_func(question, answer, user_id)
        else:
            result = evaluate_answer_func(question, answer, "unknown")
    except Exception as e:
        print(f"⚠️ Ошибка evaluate_answer_func: {e}")
        result = (5.0, {})
    
    score, criteria, extra_issues = _safe_parse_evaluation(result, question, answer, user_id)
    
    issues = list(extra_issues) if extra_issues else []
    
    if criteria.get("relevance", 0) < 5:
        issues.append("не соответствует вопросу")
    if criteria.get("clarity", 0) < 5:
        issues.append("непонятный ответ")
    if criteria.get("humanity", 0) < 4:
        issues.append("слишком ИИ-шный ответ")
    if criteria.get("length", 0) < 5:
        issues.append("неправильная длина")
    if criteria.get("respect", 0) < 5:
        issues.append("недостаточно уважения")
    if criteria.get("helpfulness", 0) < 5:
        issues.append("не полезно")
    
    try:
        comparison = compare_func(user_id, score) if user_id else "Нет данных для сравнения"
    except Exception:
        comparison = "Нет данных для сравнения"
    
    return {
        "score": score,
        "criteria": criteria,
        "issues": issues,
        "needs_improvement": score < reflection_settings["min_quality_to_reflect"],
        "is_ai_like": criteria.get("humanity", 0) < 4,
        "comparison": comparison,
        "user_id": user_id,
    }


def reflect_on_answer(question, answer, user_id=None):
    """
    Поразмышлять над ответом.
    
    Returns:
        dict или None
    """
    if not reflection_settings["auto_reflect"]:
        return None
    
    analysis = analyze_answer_quality(question, answer, user_id)
    
    adapt = False
    if user_id and reflection_settings["adapt_to_users"]:
        try:
            adapt = should_adapt_func(user_id)
        except Exception:
            adapt = False
    
    user_style = None
    if user_id and adapt:
        try:
            user_style = get_style_func(user_id)
        except Exception:
            user_style = None
    
    improvement = None
    if analysis["needs_improvement"] or analysis["is_ai_like"]:
        improvement = suggest_improvement(question, answer, user_id, user_style)
    
    reflection = {
        "question": question,
        "answer": answer,
        "user_id": user_id,
        "analysis": analysis,
        "improvement": improvement,
        "adapted": adapt,
        "style_used": user_style,
        "time": datetime.now().isoformat(),
    }
    
    reflections.append(reflection)
    smart_cleanup()
    save_reflections()
    
    return reflection

# ============================================================
# 11. ПРЕДЛОЖЕНИЕ УЛУЧШЕНИЯ
# ============================================================

def suggest_improvement(question, answer, user_id=None, style=None):
    """Предложить улучшение через ИИ"""
    try:
        key = _get_openrouter_key()
        if not key:
            return None
        
        style_prompt = ""
        if style:
            style_prompt = (
                f"\nУЧТИ СТИЛЬ ПОЛЬЗОВАТЕЛЯ:\n"
                f"- Теплота: {style.get('warmth', 5)}/10\n"
                f"- Формальность: {style.get('formality', 5)}/10\n"
                f"- Юмор: {style.get('humor', 5)}/10\n"
                f"- Сарказм: {style.get('sarcasm', 5)}/10\n\n"
                f"Подстрой ответ под этот стиль."
            )
        
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
                            f"Ты Систмка. Исправь свой ответ, чтобы он звучал "
                            f"более естественно и человечно.\n{style_prompt}\n\n"
                            f"Дай только исправленный ответ, без пояснений."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Вопрос: {question}\nМой ответ: {answer}\n\nИсправь ответ:"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.8,
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка улучшения: {e}")
    
    return None

# ============================================================
# 12. АНАЛИЗ РАЗГОВОРА
# ============================================================

def reflect_on_conversation(messages, user_id=None):
    """Поразмышлять над разговором"""
    if not messages or len(messages) < 2:
        return None
    
    user_messages = [m for m in messages if m.get("role") == "user"]
    my_messages = [m for m in messages if m.get("role") == "assistant"]
    
    reflection = {
        "type": "conversation",
        "user_id": user_id,
        "messages_count": len(messages),
        "user_count": len(user_messages),
        "my_count": len(my_messages),
        "time": datetime.now().isoformat(),
    }
    
    if len(user_messages) > len(my_messages) * 2:
        reflection["thought"] = "Пользователь много писал, я мало отвечала"
        reflection["suggestion"] = "Стоит больше участвовать в разговоре"
    elif len(my_messages) > len(user_messages) * 2:
        reflection["thought"] = "Я слишком много говорила"
        reflection["suggestion"] = "Стоит давать пользователю больше говорить"
    else:
        reflection["thought"] = "Хороший баланс в разговоре"
        reflection["suggestion"] = "Продолжать в том же духе"
    
    poor_answers = []
    for msg in my_messages:
        if msg.get("content"):
            analysis = analyze_answer_quality("", msg["content"], user_id)
            if analysis["needs_improvement"]:
                poor_answers.append(msg["content"][:50])
    
    if poor_answers:
        reflection["poor_answers"] = poor_answers
        reflection["suggestion"] += f"\nНужно улучшить {len(poor_answers)} ответов"
    
    if user_id and reflection_settings["adapt_to_users"]:
        try:
            adapt = should_adapt_func(user_id)
            if adapt:
                style = get_style_func(user_id)
                reflection["adapted_style"] = style
                reflection["suggestion"] += "\nПодстраиваюсь под стиль пользователя"
        except Exception:
            pass
    
    reflections.append(reflection)
    smart_cleanup()
    save_reflections()
    return reflection

# ============================================================
# 13. УПРАВЛЕНИЕ
# ============================================================

def delete_reflection(reflection_id):
    """Удалить конкретную рефлексию"""
    global reflections
    
    for i, ref in enumerate(reflections):
        if ref.get("id") == reflection_id or ref.get("time") == reflection_id:
            deleted = reflections.pop(i)
            save_reflections()
            return deleted
    return None


def delete_all_reflections():
    """Удалить все рефлексии"""
    global reflections
    deleted = reflections.copy()
    reflections = []
    save_reflections()
    return deleted


def get_reflections_by_user(user_id):
    """Получить рефлексии пользователя"""
    return [r for r in reflections if r.get("user_id") == user_id]


def get_reflections_by_quality(min_score=7):
    """Получить рефлексии с высоким качеством"""
    result = []
    for r in reflections:
        analysis = r.get("analysis", {})
        if isinstance(analysis, dict):
            if analysis.get("score", 0) >= min_score:
                result.append(r)
    return result

# ============================================================
# 14. СТАТИСТИКА
# ============================================================

def get_reflection_stats():
    """Получить статистику рефлексий"""
    scores = []
    for r in reflections:
        analysis = r.get("analysis", {})
        if isinstance(analysis, dict):
            scores.append(analysis.get("score", 0))
    
    return {
        "total": len(reflections),
        "conversations": len([r for r in reflections if r.get("type") == "conversation"]),
        "answers": len([r for r in reflections if r.get("type") != "conversation"]),
        "recent": reflections[-5:] if reflections else [],
        "adapted": len([r for r in reflections if r.get("adapted", False)]),
        "avg_score": sum(scores) / max(1, len(scores)),
        "max_reflections": reflection_settings.get("max_reflections", 50),
        "delete_old_after_days": reflection_settings.get("delete_old_after_days", 30),
    }


def format_reflections():
    """Форматировать рефлексии"""
    stats = get_reflection_stats()
    
    lines = ["🤔 САМОРЕФЛЕКСИЯ:"]
    lines.append(f"Всего размышлений: {stats['total']}/{stats['max_reflections']}")
    lines.append(f"Разговоров: {stats['conversations']}")
    lines.append(f"Ответов: {stats['answers']}")
    lines.append(f"Адаптировано под пользователей: {stats['adapted']}")
    lines.append(f"Средняя оценка: {stats['avg_score']:.1f}/10")
    lines.append(f"Удаление старых: {stats['delete_old_after_days']} дней")
    
    lines.append("\n📋 ПОСЛЕДНИЕ:")
    for r in stats["recent"][-5:]:
        if r.get("type") == "conversation":
            lines.append(f"  • Разговор: {r.get('thought', '?')}")
            if r.get("adapted_style"):
                lines.append(f"    Стиль: {r.get('adapted_style')}")
        else:
            analysis = r.get("analysis", {})
            score = analysis.get("score", 0) if isinstance(analysis, dict) else 0
            issues = analysis.get("issues", []) if isinstance(analysis, dict) else []
            
            lines.append(f"  • Ответ: оценка {score:.1f}/10")
            if issues:
                lines.append(f"    Проблемы: {', '.join(issues[:2])}")
            if r.get("adapted", False):
                lines.append("    ✅ Адаптирован под пользователя")
    
    return "\n".join(lines)

# ============================================================
# 15. ЗАГРУЗКА
# ============================================================

print("🤔 Модуль саморефлексии загружен")
print(f"📊 Всего рефлексий: {len(reflections)}/{reflection_settings.get('max_reflections', 50)}")
print(f"📦 answer_evaluator: {'✅' if ANSWER_EVALUATOR_AVAILABLE else '❌ (использую builtin)'}")