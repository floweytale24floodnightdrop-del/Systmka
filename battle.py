"""Битва аккаунтов — сравнение профилей по аватарке, нику, активности"""

import os
import re
import io
import base64
import random
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ
# ============================================================

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ opencv/numpy не установлены — анализ аватарок недоступен")

# ============================================================
# 3. НАСТРОЙКИ
# ============================================================

VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct"

# Смысловые слова для оценки ника
MEANINGFUL_WORDS = [
    "flowey", "sans", "frisk", "chara", "star", "moon", "sun",
    "fire", "ice", "dark", "light", "shadow", "ghost", "angel",
    "demon", "systmka", "flower", "soul", "heart", "wind",
]

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 5. АВАТАРКА
# ============================================================

def get_user_avatar(bot, user_id):
    """
    Получить аватарку пользователя через Telegram API.
    
    Returns:
        bytes или None
    """
    if not bot:
        return None
    
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            file_id = photos.photos[0][-1].file_id
            file_info = bot.get_file(file_id)
            return bot.download_file(file_info.file_path)
    except Exception as e:
        print(f"⚠️ Ошибка получения аватарки {user_id}: {e}")
    return None


def analyze_avatar_with_ai(avatar_data):
    """
    Анализ аватарки через ИИ (vision-модель).
    
    Returns:
        tuple: (score, short_description, full_analysis)
    """
    if not avatar_data:
        return 2.0, "Нет аватарки", "Без аватарки"
    
    key = _get_openrouter_key()
    if not key:
        return 5.0, "Обычная аватарка", "Ключ ИИ недоступен"
    
    try:
        image_base64 = base64.b64encode(avatar_data).decode('utf-8')
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Оцени эту аватарку от 1 до 10. "
                                    "Опиши что на ней изображено. "
                                    "Насколько она красивая и качественная?"
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 200,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                text = data['choices'][0]['message']['content']
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                score = float(match.group(1)) if match else 5.0
                description = text[:100]
                return min(10, max(1, score)), description, text
    except Exception as e:
        print(f"⚠️ Ошибка анализа аватарки: {e}")
    
    return 5.0, "Обычная аватарка", "Среднее качество"


def check_avatar_quality(avatar_data):
    """
    Локальная проверка качества аватарки (без ИИ).
    
    Returns:
        dict: {width, height, size_kb, is_high_res, has_face}
    """
    if not avatar_data or not CV2_AVAILABLE:
        return {}
    
    try:
        nparr = np.frombuffer(avatar_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {}
        
        height, width = img.shape[:2]
        size_kb = len(avatar_data) // 1024
        
        # Определяем высокое разрешение
        is_high_res = width >= 500 and height >= 500
        
        # Пробуем найти лицо
        has_face = False
        try:
            face_cascade_path = (
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            if not face_cascade.empty():
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                has_face = len(faces) > 0
        except Exception:
            pass
        
        return {
            "width": width,
            "height": height,
            "size_kb": size_kb,
            "is_high_res": is_high_res,
            "has_face": has_face,
        }
    except Exception as e:
        print(f"⚠️ Ошибка проверки аватарки: {e}")
        return {}

# ============================================================
# 6. ОЦЕНКА НИКА
# ============================================================

def evaluate_nickname_quality(username):
    """
    Оценка качества ника.
    
    Returns:
        float: 1.0 - 10.0
    """
    if not username:
        return 1.0
    
    username_clean = username.replace("@", "").strip()
    score = 5.0
    
    if not username_clean:
        return 1.0
    
    # Длина
    if len(username_clean) < 3:
        score -= 3
    elif len(username_clean) < 5:
        score -= 1
    elif len(username_clean) > 25:
        score -= 2
    elif 7 <= len(username_clean) <= 15:
        score += 1
    
    # Цифры
    digit_count = sum(c.isdigit() for c in username_clean)
    if digit_count > 3:
        score -= 2
    elif digit_count > 0:
        score -= 0.5
    
    # Спецсимволы
    special_count = sum(
        not c.isalnum() and c != "_" for c in username_clean
    )
    if special_count > 3:
        score -= 2
    elif special_count > 0:
        score -= 0.5
    
    # Читаемость
    if username_clean.isalnum():
        score += 0.5
    
    # Смысловые слова
    for word in MEANINGFUL_WORDS:
        if word in username_clean.lower():
            score += 1
            break
    
    return max(1, min(10, round(score, 1)))

# ============================================================
# 7. ОЦЕНКА ОПИСАНИЯ
# ============================================================

def evaluate_description_quality(description):
    """
    Оценка качества описания профиля.
    
    Returns:
        tuple: (score, short_text)
    """
    if not description:
        return 0, "Нет описания"
    
    score = 5.0
    
    if len(description) > 50:
        score += 1
    if len(description) < 5:
        score -= 3
    
    desc_lower = description.lower()
    personal_words = ["я", "люблю", "хочу", "мой", "моя", "не", "да", "нет"]
    if any(w in desc_lower for w in personal_words):
        score += 0.5
    
    emojis = ["💜", "✨", "🌟", "💀", "🔥", "❤️", "😊"]
    if any(e in description for e in emojis):
        score += 0.5
    
    return max(1, min(10, round(score, 1))), description[:50]

# ============================================================
# 8. ВОЗРАСТ АККАУНТА
# ============================================================

def get_real_account_age(profile):
    """Получить возраст аккаунта в днях (по first_seen)"""
    if not profile:
        return 0
    
    first_seen = profile.get("first_seen")
    if not first_seen:
        return 0
    
    if isinstance(first_seen, str):
        try:
            first_seen = datetime.fromisoformat(first_seen)
        except (ValueError, TypeError):
            return 0
    
    if not isinstance(first_seen, datetime):
        return 0
    
    try:
        return (datetime.now() - first_seen).days
    except Exception:
        return 0

# ============================================================
# 9. ПОЛНАЯ ОЦЕНКА АККАУНТА
# ============================================================

def evaluate_account(user_id, opponent_id, user_profiles, user_glitches,
                     user_combo, get_user_glitches_func, owner_ids, bot=None):
    """
    Расширенная оценка аккаунта.
    
    Returns:
        tuple: (score, criteria, status_points)
    """
    score = 5.0
    criteria = {}
    status_points = {}
    
    profile = user_profiles.get(user_id, {})
    
    # НИК
    username = profile.get("username", "")
    nick_score = evaluate_nickname_quality(username)
    criteria["Ник"] = f"{nick_score}/10"
    score += (nick_score - 5) * 0.3
    
    # АВАТАРКА
    avatar_data = get_user_avatar(bot, user_id) if bot else None
    avatar_score, avatar_desc, avatar_full = analyze_avatar_with_ai(avatar_data)
    criteria["Аватар"] = f"{avatar_score}/10 - {avatar_desc[:30]}"
    score += (avatar_score - 5) * 0.4
    
    # Локальный анализ аватарки
    if avatar_data:
        quality = check_avatar_quality(avatar_data)
        if quality.get("is_high_res"):
            score += 0.3
            criteria["Аватар (HD)"] = "✅"
        if quality.get("has_face"):
            score += 0.2
            criteria["Лицо на аватаре"] = "✅"
    
    # ОПИСАНИЕ
    description = profile.get("description", "")
    desc_score, desc_text = evaluate_description_quality(description)
    criteria["Описание"] = f"{desc_score}/10" if description else "Нет"
    score += (desc_score - 5) * 0.2 if description else -0.5
    
    # АКТИВНОСТЬ
    messages = profile.get("messages", 0)
    if messages > 1000:
        criteria["Активность"] = "10/10"
        score += 2
    elif messages > 500:
        criteria["Активность"] = "9/10"
        score += 1.5
    elif messages > 100:
        criteria["Активность"] = "7/10"
        score += 0.8
    elif messages > 10:
        criteria["Активность"] = "5/10"
        score += 0.2
    else:
        criteria["Активность"] = "2/10"
        score -= 0.5
    
    # ВОЗРАСТ АККАУНТА
    account_age = get_real_account_age(profile)
    if account_age > 365:
        criteria["Возраст ака"] = f"{account_age} дней"
        score += 1
    elif account_age > 30:
        criteria["Возраст ака"] = f"{account_age} дней"
        score += 0.5
    else:
        criteria["Возраст ака"] = f"{account_age} дней (новый)"
        score -= 0.5
    
    # ПОВЕДЕНИЕ
    behavior = profile.get("behavior_score", 50)
    if behavior > 70:
        criteria["Поведение"] = "8/10"
        score += 1
    elif behavior < 30:
        criteria["Поведение"] = "3/10"
        score -= 1
    else:
        criteria["Поведение"] = "5/10"
    
    # ГЛИТЧИ
    try:
        glitches = get_user_glitches_func(user_id, owner_ids)
    except Exception:
        glitches = 0
    
    if glitches == float('inf'):
        criteria["Очки"] = "∞"
        score += 2
    elif glitches > 500:
        criteria["Очки"] = "10/10"
        score += 2
    elif glitches > 200:
        criteria["Очки"] = "8/10"
        score += 1.5
    elif glitches > 50:
        criteria["Очки"] = "6/10"
        score += 0.8
    else:
        criteria["Очки"] = "3/10"
        score -= 0.3
    
    # КОМБО
    combo = user_combo.get(user_id, 0)
    if combo > 50:
        criteria["Комбо"] = f"{combo}💜"
        score += 1.5
    elif combo > 20:
        criteria["Комбо"] = f"{combo}💜"
        score += 1
    elif combo > 10:
        criteria["Комбо"] = f"{combo}💜"
        score += 0.5
    elif combo > 0:
        criteria["Комбо"] = f"{combo}💜"
        score += 0.2
    else:
        criteria["Комбо"] = "0"
    
    # СТАТУС (заглушки на PC)
    status_points["TG Premium"] = 0
    criteria["Premium"] = "❌"
    status_points["NFT"] = 0
    criteria["NFT"] = "❌"
    status_points["Подарки"] = 0
    criteria["Подарки"] = "❌"
    
    # СРАВНЕНИЕ С ОППОНЕНТОМ
    try:
        opp_glitches = get_user_glitches_func(opponent_id, owner_ids)
    except Exception:
        opp_glitches = 0
    
    if glitches != float('inf') and opp_glitches != float('inf'):
        if glitches > opp_glitches * 2:
            criteria["Сравнение"] = "9/10"
            score += 1.5
        elif glitches > opp_glitches:
            criteria["Сравнение"] = "7/10"
            score += 0.8
        elif glitches < opp_glitches:
            criteria["Сравнение"] = "3/10"
            score -= 1
        else:
            criteria["Сравнение"] = "5/10"
    else:
        criteria["Сравнение"] = "5/10"
    
    return max(1, min(10, round(score, 2))), criteria, status_points

# ============================================================
# 10. БОЙ АКОВ
# ============================================================

def battle_accounts(challenger_id, opponent_id, user_profiles, user_glitches,
                    user_combo, get_user_glitches_func, add_glitches_func,
                    get_combo_multiplier_func, owner_ids, bet=0, bot=None):
    """
    Бой аков с полной оценкой.
    
    Returns:
        tuple: (result_text, challenger_avatar, opponent_avatar,
                challenger_username, opponent_username)
    """
    challenger_score, challenger_criteria, challenger_status = evaluate_account(
        challenger_id, opponent_id, user_profiles, user_glitches, user_combo,
        get_user_glitches_func, owner_ids, bot
    )
    opponent_score, opponent_criteria, opponent_status = evaluate_account(
        opponent_id, challenger_id, user_profiles, user_glitches, user_combo,
        get_user_glitches_func, owner_ids, bot
    )
    
    challenger_info = user_profiles.get(challenger_id, {})
    opponent_info = user_profiles.get(opponent_id, {})
    
    challenger_name = challenger_info.get("first_name", "Игрок 1")
    opponent_name = opponent_info.get("first_name", "Игрок 2")
    challenger_username = challenger_info.get("username", "")
    opponent_username = opponent_info.get("username", "")
    
    # Формируем результат
    result = "⚔️ БОЙ АКОВ\n\n"
    result += f"🟦 {challenger_name} {challenger_username}\n"
    result += f"Итоговая оценка: {challenger_score}/10\n\n"
    result += "Критерии:\n"
    for crit, val in challenger_criteria.items():
        result += f"  • {crit}: {val}\n"
    
    result += f"\n\n🟥 {opponent_name} {opponent_username}\n"
    result += f"Итоговая оценка: {opponent_score}/10\n\n"
    result += "Критерии:\n"
    for crit, val in opponent_criteria.items():
        result += f"  • {crit}: {val}\n"
    
    result += "\n\n"
    
    # Описание от ИИ
    description = generate_battle_description(
        challenger_info, opponent_info, challenger_score, opponent_score
    )
    result += f"📝 {description}\n\n"
    
    # Определяем победителя
    if challenger_score > opponent_score:
        winner = challenger_id
        loser = opponent_id
        diff = round(challenger_score - opponent_score, 2)
        result += f"🏆 Победитель: {challenger_name}!\nРазница: +{diff} балла"
    elif opponent_score > challenger_score:
        winner = opponent_id
        loser = challenger_id
        diff = round(opponent_score - challenger_score, 2)
        result += f"🏆 Победитель: {opponent_name}!\nРазница: +{diff} балла"
    else:
        result += "🤝 Ничья!"
        return result, None, None, None, None
    
    # Комбо
    if winner not in user_combo:
        user_combo[winner] = 0
    user_combo[winner] += 1
    if loser in user_combo:
        user_combo[loser] = 0
    
    combo = user_combo.get(winner, 0)
    
    try:
        multiplier = get_combo_multiplier_func(combo)
    except Exception:
        multiplier = 0
    
    base_points = 1 + (combo * 0.1 if combo >= 10 else 0)
    points = int(base_points + base_points * multiplier)
    
    try:
        add_glitches_func(winner, points, owner_ids)
    except Exception as e:
        print(f"⚠️ Ошибка начисления глитчей: {e}")
    
    if bet > 0:
        try:
            add_glitches_func(winner, bet, owner_ids)
            result += f"\n\nВыигрыш ставки: +{bet}👾"
        except Exception:
            pass
    
    result += f"\n\n💜 Комбо: {combo}\n👾 Очки: +{points}"
    
    # Аватарки
    challenger_avatar = get_user_avatar(bot, challenger_id) if bot else None
    opponent_avatar = get_user_avatar(bot, opponent_id) if bot else None
    
    return result, challenger_avatar, opponent_avatar, challenger_username, opponent_username

# ============================================================
# 11. ОПИСАНИЕ БИТВЫ ЧЕРЕЗ ИИ
# ============================================================

def generate_battle_description(challenger_info, opponent_info,
                                 challenger_score, opponent_score):
    """Генерация описания битвы через ИИ"""
    key = _get_openrouter_key()
    if not key:
        return _fallback_description(
            challenger_info, opponent_info, challenger_score, opponent_score
        )
    
    try:
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
                            "Ты комментатор битвы аккаунтов. "
                            "Опиши в 2-3 предложениях разницу между аккаунтами. "
                            "Будь смешным и саркастичным. "
                            "Не используй звёздочки. Пиши по-русски."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Игрок 1: {challenger_info.get('first_name', '?')} "
                            f"(@{challenger_info.get('username', '')}) - "
                            f"{challenger_score}/10\n"
                            f"Игрок 2: {opponent_info.get('first_name', '?')} "
                            f"(@{opponent_info.get('username', '')}) - "
                            f"{opponent_score}/10"
                        ),
                    },
                ],
                "temperature": 0.9,
                "max_tokens": 150,
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка генерации описания: {e}")
    
    return _fallback_description(
        challenger_info, opponent_info, challenger_score, opponent_score
    )


def _fallback_description(challenger_info, opponent_info,
                          challenger_score, opponent_score):
    """Fallback описание"""
    challenger_name = challenger_info.get("first_name", "Игрок 1")
    opponent_name = opponent_info.get("first_name", "Игрок 2")
    
    if challenger_score > opponent_score:
        return f"{challenger_name} явно лучше выглядит, а {opponent_name} надо подтянуться."
    elif opponent_score > challenger_score:
        return f"{opponent_name} круче, а {challenger_name} проигрывает."
    else:
        return f"{challenger_name} и {opponent_name} идут на равных."

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("⚔️ Модуль битвы аккаунтов загружен")
print(f"📦 opencv: {'✅' if CV2_AVAILABLE else '❌'}")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")