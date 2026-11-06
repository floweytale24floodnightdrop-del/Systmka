"""Полное определение пола пользователя — по аватарке, нику, речи, обращению других"""

import os
import re
import json
import base64
import requests
from datetime import datetime
from collections import defaultdict
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

GENDER_FILE = "gender_data.json"

gender_data = {
    "users": {},  # {user_id: {"gender": str, "confidence": float, "scores": {}, "history": []}}
    "stats": {
        "male": 0,
        "female": 0,
        "unknown": 0,
        "total": 0,
    }
}

# ============================================================
# 2. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_gender_data():
    try:
        with open(GENDER_FILE, "w", encoding="utf-8") as f:
            json.dump(gender_data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_gender_data():
    global gender_data
    try:
        if os.path.exists(GENDER_FILE):
            with open(GENDER_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                gender_data.update(loaded)
        return True
    except:
        return False

load_gender_data()

# ============================================================
# 3. АНАЛИЗ АВАТАРКИ
# ============================================================

def analyze_avatar_gender(avatar_data):
    """Определить пол по аватарке через ИИ"""
    if not avatar_data:
        return None, 0
    
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        image_base64 = base64.b64encode(avatar_data).decode('utf-8')
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-3.2-11b-vision-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Определи пол человека на аватарке. Ответь ТОЛЬКО: male, female или unknown. Никаких пояснений."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content'].strip().lower()
                if result in ["male", "female", "unknown"]:
                    return result, 0.8
    except:
        pass
    
    return None, 0

# ============================================================
# 4. АНАЛИЗ НИКА И USERNAME
# ============================================================

def analyze_nickname_gender(username, first_name, last_name=""):
    """Определить пол по нику и имени"""
    scores = {"male": 0, "female": 0}
    
    # 1. Анализ имени
    male_names = ["александр", "алексей", "андрей", "антон", "артем", "владимир", "дмитрий", "евгений", "иван", "игорь", "кирилл", "константин", "максим", "михаил", "николай", "олег", "павел", "петр", "рома", "роман", "сергей", "станислав", "юрий", "ярослав"]
    female_names = ["александра", "анастасия", "анна", "валентина", "валерия", "вероника", "виктория", "галина", "дарья", "екатерина", "елена", "елизавета", "ирина", "кристина", "ксения", "людмила", "мария", "марина", "наталья", "нинель", "ольга", "рита", "светлана", "софия", "татьяна", "юлия"]
    
    name_lower = (first_name or "").lower()
    last_lower = (last_name or "").lower()
    
    for name in male_names:
        if name in name_lower or name in last_lower:
            scores["male"] += 2
            break
    
    for name in female_names:
        if name in name_lower or name in last_lower:
            scores["female"] += 2
            break
    
    # 2. Анализ username
    username_lower = (username or "").lower()
    
    male_patterns = ["_boy", "_guy", "man", "bro", "dude", "king", "mr", "vlad", "alex"]
    female_patterns = ["_girl", "_lady", "queen", "ms", "miss", "kat", "anna", "mary"]
    
    for pattern in male_patterns:
        if pattern in username_lower:
            scores["male"] += 1
            break
    
    for pattern in female_patterns:
        if pattern in username_lower:
            scores["female"] += 1
            break
    
    # 3. Окончания ников
    if username_lower.endswith("_m") or username_lower.endswith("_man"):
        scores["male"] += 1
    if username_lower.endswith("_f") or username_lower.endswith("_woman"):
        scores["female"] += 1
    
    return scores

# ============================================================
# 5. АНАЛИЗ РЕЧИ
# ============================================================

def analyze_speech_gender(text):
    """Определить пол по речи"""
    if not text:
        return {"male": 0, "female": 0}
    
    text_lower = text.lower()
    scores = {"male": 0, "female": 0}
    
    # Самообращение (я пошёл/пошла)
    male_self = ["я пошел", "я пришел", "я сделал", "я купил", "я заходил", "я гулял", "я играл", "я ходил", "я ел", "я пил", "я спал", "я читал", "я писал", "я был"]
    female_self = ["я пошла", "я пришла", "я сделала", "я купила", "я заходила", "я гуляла", "я играла", "я ходила", "я ела", "я пила", "я спала", "я читала", "я писала", "я была"]
    
    for phrase in male_self:
        if phrase in text_lower:
            scores["male"] += 2
            break
    
    for phrase in female_self:
        if phrase in text_lower:
            scores["female"] += 2
            break
    
    # Обращение к другим
    male_to_other = ["ты пошел", "ты пришел", "ты сделал", "ты купил"]
    female_to_other = ["ты пошла", "ты пришла", "ты сделала", "ты купила"]
    
    for phrase in male_to_other:
        if phrase in text_lower:
            scores["male"] += 1
            break
    
    for phrase in female_to_other:
        if phrase in text_lower:
            scores["female"] += 1
            break
    
    # Эмодзи
    male_emojis = ["💀", "👾", "🔥", "😈", "🤘", "💪", "👊", "😎"]
    female_emojis = ["❤️", "💜", "😍", "🥰", "😊", "🥺", "😢", "😭", "💔", "😘", "💕", "🫶", "🌸", "🌺", "💗", "💖"]
    
    for emoji in male_emojis:
        if emoji in text:
            scores["male"] += 0.5
            break
    
    for emoji in female_emojis:
        if emoji in text:
            scores["female"] += 0.5
            break
    
    # Сленг
    male_slang = ["бро", "брат", "кек", "лол", "харош", "норм", "крч", "хз", "реально", "чисто", "топ", "вай"]
    female_slang = ["мило", "кавай", "ня", "мур", "приветик", "пока-пока", "споки", "вкусняшка"]
    
    for word in male_slang:
        if word in text_lower:
            scores["male"] += 0.3
            break
    
    for word in female_slang:
        if word in text_lower:
            scores["female"] += 0.3
            break
    
    # Длина сообщения
    if len(text) > 80:
        scores["female"] += 0.5
    if len(text) < 20:
        scores["male"] += 0.3
    
    return scores

# ============================================================
# 6. АНАЛИЗ ОБРАЩЕНИЙ ОТ ДРУГИХ
# ============================================================

def analyze_others_speech(user_id, messages):
    """Анализировать как к пользователю обращаются другие"""
    scores = {"male": 0, "female": 0}
    
    male_refs = ["он", "его", "ему", "парень", "мужик", "братан", "дружище"]
    female_refs = ["она", "ее", "ей", "девушка", "девчонка", "подруга", "милая"]
    
    for msg in messages:
        text = msg.get("text", "").lower()
        for ref in male_refs:
            if ref in text:
                scores["male"] += 1
        for ref in female_refs:
            if ref in text:
                scores["female"] += 1
    
    return scores

# ============================================================
# 7. ОСНОВНАЯ ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ПОЛА
# ============================================================

def detect_gender(user_id, username=None, first_name=None, last_name=None, 
                  avatar_data=None, text=None, messages=None):
    """Полное определение пола пользователя"""
    
    user_id_str = str(user_id)
    
    # Инициализация пользователя
    if user_id_str not in gender_data["users"]:
        gender_data["users"][user_id_str] = {
            "gender": "unknown",
            "confidence": 0.0,
            "scores": {"male": 0, "female": 0, "avatar": 0, "nick": 0, "speech": 0, "others": 0},
            "history": [],
            "last_update": None,
        }
    
    user = gender_data["users"][user_id_str]
    scores = {"male": 0, "female": 0}
    
    # 1. Анализ аватарки
    if avatar_data:
        avatar_gender, confidence = analyze_avatar_gender(avatar_data)
        if avatar_gender == "male":
            scores["male"] += 3
            user["scores"]["avatar"] = 3
        elif avatar_gender == "female":
            scores["female"] += 3
            user["scores"]["avatar"] = 3
    
    # 2. Анализ ника
    nick_scores = analyze_nickname_gender(username, first_name, last_name)
    scores["male"] += nick_scores["male"] * 0.5
    scores["female"] += nick_scores["female"] * 0.5
    user["scores"]["nick"] = max(nick_scores["male"], nick_scores["female"])
    
    # 3. Анализ речи
    if text:
        speech_scores = analyze_speech_gender(text)
        scores["male"] += speech_scores["male"] * 0.3
        scores["female"] += speech_scores["female"] * 0.3
        user["scores"]["speech"] = max(speech_scores["male"], speech_scores["female"])
    
    # 4. Анализ обращений от других
    if messages:
        others_scores = analyze_others_speech(user_id, messages)
        scores["male"] += others_scores["male"] * 0.2
        scores["female"] += others_scores["female"] * 0.2
        user["scores"]["others"] = max(others_scores["male"], others_scores["female"])
    
    # Итоговое определение
    total_male = scores["male"]
    total_female = scores["female"]
    
    # Накопление статистики
    user["history"].append({
        "time": datetime.now().isoformat(),
        "male_score": total_male,
        "female_score": total_female,
        "text": text[:50] if text else ""
    })
    
    if len(user["history"]) > 100:
        user["history"] = user["history"][-100:]
    
    # Определение пола
    if total_male > total_female + 2:
        user["gender"] = "male"
        user["confidence"] = min(1.0, total_male / (total_male + total_female))
    elif total_female > total_male + 2:
        user["gender"] = "female"
        user["confidence"] = min(1.0, total_female / (total_male + total_female))
    else:
        user["gender"] = "unknown"
        user["confidence"] = 0.5
    
    user["last_update"] = datetime.now().isoformat()
    
    # Обновление статистики
    gender_data["stats"]["total"] += 1
    if user["gender"] == "male":
        gender_data["stats"]["male"] += 1
    elif user["gender"] == "female":
        gender_data["stats"]["female"] += 1
    else:
        gender_data["stats"]["unknown"] += 1
    
    save_gender_data()
    
    return user["gender"], user["confidence"], scores

# ============================================================
# 8. ПОЛУЧЕНИЕ ИНФОРМАЦИИ
# ============================================================

def get_user_gender(user_id):
    user_id_str = str(user_id)
    if user_id_str in gender_data["users"]:
        return gender_data["users"][user_id_str].get("gender", "unknown")
    return "unknown"

def get_user_gender_stats(user_id):
    user_id_str = str(user_id)
    if user_id_str in gender_data["users"]:
        return gender_data["users"][user_id_str]
    return None

def format_gender_info(user_id):
    stats = get_user_gender_stats(user_id)
    if not stats:
        return "❌ Нет данных о поле"
    
    lines = [
        f"👤 Пол: {stats.get('gender', 'unknown')}",
        f"📊 Уверенность: {stats.get('confidence', 0):.0%}",
        f"📈 Мужской: {stats.get('scores', {}).get('male', 0):.1f}",
        f"📈 Женский: {stats.get('scores', {}).get('female', 0):.1f}",
        f"🔄 Обновлено: {stats.get('last_update', '?')[:16]}",
    ]
    return "\n".join(lines)

print("👤 Модуль определения пола загружен")
print(f"📊 Всего пользователей: {gender_data['stats']['total']}")