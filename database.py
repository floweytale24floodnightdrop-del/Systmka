"""База данных Систмки — единый источник правды"""

import os
import json
import time
import re
import threading
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import (
    save_data,
    load_data,
    DATA_FILE,
    OWNER_IDS,
    HELPER_IDS,
)

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

RP_COMMANDS_FILE = "rp_commands.json"
PENDING_BATTLES_FILE = "pending_battles.json"
RP_REQUESTS_FILE = "rp_requests.json"

# Дебаунс автосохранения (секунды)
AUTO_SAVE_DEBOUNCE = 30

# ============================================================
# 3. ОСНОВНЫЕ ДАННЫЕ
# ============================================================

history = {}
user_profiles = {}
all_chats = {}
user_chat_activity = {}
ls_users = set()
user_last_seen = {}
user_behavior = {}
muted_users = {}
banned_users = {}
warned_users = {}
spam_counter = {}
user_glitches = {}
user_combo = {}
user_credits = {}
user_penalties = {}
censorship_levels = {}
chat_owner_present = {}
bot_start_time = datetime.now()
last_messages_log = []
safe_mode_chats = {}
profile_nicknames = {}
profile_descriptions = {}
profile_music = {}
user_gender = {}
user_roles = {}
premium_users = {}
user_levels = {}
pending_battles = {}
user_gender_history = {}

# ============================================================
# 4. РП-КОМАНДЫ
# ============================================================

DEFAULT_RP_COMMANDS = {
    "кусь": "<Ты> кусьнул(а) <Пользователь>",
    "чмок": "<Ты> чмокнул(а) <Пользователь>",
    "обнять": "<Ты> обнял(а) <Пользователь>",
    "поцеловать": "<Ты> поцеловал(а) <Пользователь>",
    "ударить": "<Ты> ударил(а) <Пользователь>",
    "погладить": "<Ты> погладил(а) <Пользователь>",
    "укусить": "<Ты> укусил(а) <Пользователь>",
    "засосать": "<Ты> засосал(а) <Пользователь>",
    "выебать": "<Ты> выебал(а) <Пользователь>",
    "трахнуть": "<Ты> трахнул(а) <Пользователь>",
    "отшлепать": "<Ты> отшлепал(а) <Пользователь>",
    "прижать": "<Ты> прижал(а) <Пользователь> к стене",
    "лизнуть": "<Ты> лизнул(а) <Пользователь>",
    "убить": "<Ты> убил(а) <Пользователь>",
    "воскресить": "<Ты> воскресил(а) <Пользователь>",
    "вылечить": "<Ты> вылечил(а) <Пользователь>",
    "обнять крепко": "<Ты> крепко обнял(а) <Пользователь>",
    "поцеловать в шею": "<Ты> поцеловал(а) <Пользователь> в шею",
    "поцеловать в губы": "<Ты> поцеловал(а) <Пользователь> в губы",
    "взять за руку": "<Ты> взял(а) <Пользователь> за руку",
    "прижать к себе": "<Ты> прижал(а) <Пользователь> к себе",
    "повалить": "<Ты> повалил(а) <Пользователь>",
    "защекотать": "<Ты> защекотал(а) <Пользователь>",
}

rp_commands = DEFAULT_RP_COMMANDS.copy()
custom_rp_commands = {}
rp_requests = {}

# ============================================================
# 5. ДЕБАУНС СОХРАНЕНИЯ
# ============================================================

_save_lock = threading.Lock()
_last_save_time = 0
_pending_save = False


def _schedule_save():
    """
    Запланировать сохранение с дебаунсом.
    
    Если сохранение было меньше AUTO_SAVE_DEBOUNCE секунд назад —
    откладываем до следующего вызова.
    """
    global _pending_save
    _pending_save = True


def _flush_save_if_needed():
    """Сохранить, если прошло достаточно времени"""
    global _last_save_time, _pending_save
    
    if not _pending_save:
        return
    
    now = time.time()
    if now - _last_save_time < AUTO_SAVE_DEBOUNCE:
        return
    
    with _save_lock:
        _pending_save = False
        _last_save_time = now
        _do_save_all_data()


def _do_save_all_data():
    """Реальное сохранение всех данных"""
    try:
        data = {
            "user_profiles": _convert_keys(user_profiles),
            "user_glitches": _convert_keys(user_glitches),
            "user_combo": _convert_keys(user_combo),
            "user_credits": _convert_keys(user_credits),
            "censorship_levels": _convert_keys(censorship_levels),
            "user_gender": _convert_keys(user_gender),
            "user_gender_history": _convert_keys(user_gender_history),
            "muted_users": _convert_keys(muted_users),
            "banned_users": _convert_keys(banned_users),
            "warned_users": _convert_keys(warned_users),
            "premium_users": _convert_keys(premium_users),
            "user_levels": _convert_keys(user_levels),
            "chat_owner_present": _convert_keys(chat_owner_present),
        }
        save_data(data)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения данных: {e}")
        return False


def _convert_keys(d):
    """Привести ключи словаря к строкам (для JSON)"""
    if not isinstance(d, dict):
        return d
    return {str(k): v for k, v in d.items()}


def _convert_keys_back(d):
    """Привести ключи обратно к int где возможно"""
    if not isinstance(d, dict):
        return d
    result = {}
    for k, v in d.items():
        try:
            result[int(k)] = v
        except (ValueError, TypeError):
            result[k] = v
    return result

# ============================================================
# 6. СОХРАНЕНИЕ/ЗАГРУЗКА РП-КОМАНД
# ============================================================

def save_rp_commands():
    """Сохранить РП-команды"""
    try:
        data = {
            "default": DEFAULT_RP_COMMANDS,
            "custom": custom_rp_commands,
            "saved_at": datetime.now().isoformat(),
        }
        with open(RP_COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения РП-команд: {e}")
        return False


def load_rp_commands():
    """Загрузить РП-команды"""
    global custom_rp_commands, rp_commands
    try:
        if os.path.exists(RP_COMMANDS_FILE):
            with open(RP_COMMANDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data.get("custom"), dict):
                custom_rp_commands = data["custom"]
            
            rp_commands = DEFAULT_RP_COMMANDS.copy()
            rp_commands.update(custom_rp_commands)
            return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки РП-команд: {e}")
    return False

# ============================================================
# 7. СОХРАНЕНИЕ/ЗАГРУЗКА РП-ЗАПРОСОВ
# ============================================================

def save_rp_requests():
    """Сохранить РП-запросы"""
    try:
        data = {}
        for req_id, req in rp_requests.items():
            data[str(req_id)] = {
                "from_user": req["from_user"],
                "to_user": req["to_user"],
                "action": req["action"],
                "status": req["status"],
                "created_at": (
                    req["created_at"].isoformat()
                    if isinstance(req.get("created_at"), datetime)
                    else req.get("created_at")
                ),
            }
        with open(RP_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения РП-запросов: {e}")
        return False


def load_rp_requests():
    """Загрузить РП-запросы"""
    global rp_requests
    try:
        if os.path.exists(RP_REQUESTS_FILE):
            with open(RP_REQUESTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for req_id, req in data.items():
                rp_requests[req_id] = {
                    "from_user": req["from_user"],
                    "to_user": req["to_user"],
                    "action": req["action"],
                    "status": req["status"],
                    "created_at": (
                        datetime.fromisoformat(req["created_at"])
                        if isinstance(req.get("created_at"), str)
                        else datetime.now()
                    ),
                }
            return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки РП-запросов: {e}")
    return False

# ============================================================
# 8. СОХРАНЕНИЕ/ЗАГРУЗКА БИТВ
# ============================================================

def save_pending_battles():
    """Сохранить ожидающие битвы"""
    try:
        data = {}
        for user_id, battle in pending_battles.items():
            data[str(user_id)] = {
                "challenger_id": battle["challenger_id"],
                "bet": battle.get("bet", 0),
                "timestamp": battle.get("timestamp", datetime.now().isoformat()),
            }
        with open(PENDING_BATTLES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения битв: {e}")
        return False


def load_pending_battles():
    """Загрузить ожидающие битвы"""
    global pending_battles
    try:
        if os.path.exists(PENDING_BATTLES_FILE):
            with open(PENDING_BATTLES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for user_id, battle in data.items():
                try:
                    pending_battles[int(user_id)] = {
                        "challenger_id": battle["challenger_id"],
                        "bet": battle.get("bet", 0),
                        "timestamp": battle.get("timestamp", datetime.now().isoformat()),
                    }
                except (ValueError, KeyError):
                    continue
            return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки битв: {e}")
    return False

# ============================================================
# 9. РП-КОМАНДЫ ФУНКЦИИ
# ============================================================

def get_all_rp_commands():
    """Получить все РП-команды"""
    all_commands = DEFAULT_RP_COMMANDS.copy()
    for trigger, data in custom_rp_commands.items():
        all_commands[trigger] = data["action"]
    return all_commands


def get_rp_command(trigger, user_id=None):
    """Получить РП-команду по триггеру"""
    trigger_lower = trigger.lower()
    if trigger_lower in custom_rp_commands:
        if user_id is None or custom_rp_commands[trigger_lower].get("creator_id") == user_id:
            return custom_rp_commands[trigger_lower]["action"]
    if trigger_lower in DEFAULT_RP_COMMANDS:
        return DEFAULT_RP_COMMANDS[trigger_lower]
    return None


def add_custom_rp_command(trigger, action, creator_id, creator_name):
    """Добавить кастомную РП-команду"""
    trigger_lower = trigger.lower()
    custom_rp_commands[trigger_lower] = {
        "action": action,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "created_at": datetime.now().isoformat(),
    }
    rp_commands[trigger_lower] = action
    save_rp_commands()
    return True


def remove_custom_rp_command(trigger, user_id):
    """Удалить кастомную РП-команду"""
    trigger_lower = trigger.lower()
    if trigger_lower in custom_rp_commands:
        if custom_rp_commands[trigger_lower]["creator_id"] == user_id:
            del custom_rp_commands[trigger_lower]
            if trigger_lower in rp_commands:
                del rp_commands[trigger_lower]
            save_rp_commands()
            return True
    return False


def get_user_rp_commands(user_id):
    """Получить РП-команды пользователя"""
    user_commands = {}
    for trigger, data in custom_rp_commands.items():
        if data["creator_id"] == user_id:
            user_commands[trigger] = data["action"]
    return user_commands

# ============================================================
# 10. ЗАПРОСЫ В ЛС
# ============================================================

def create_rp_request(from_user_id, to_user_id, action):
    """Создать РП-запрос"""
    request_id = str(len(rp_requests) + 1)
    for req_id, req in rp_requests.items():
        if (req["from_user"] == from_user_id
                and req["to_user"] == to_user_id
                and req["status"] == "pending"):
            return None, "У вас уже есть активный запрос"
    
    rp_requests[request_id] = {
        "from_user": from_user_id,
        "to_user": to_user_id,
        "action": action,
        "status": "pending",
        "created_at": datetime.now(),
    }
    save_rp_requests()
    return request_id, None


def accept_rp_request(request_id, user_id):
    """Принять РП-запрос"""
    req_id = str(request_id)
    if req_id not in rp_requests:
        return False, "Запрос не найден"
    
    req = rp_requests[req_id]
    if req["to_user"] != user_id:
        return False, "Вы не получатель"
    if req["status"] != "pending":
        return False, f"Запрос уже {req['status']}"
    
    req["status"] = "accepted"
    save_rp_requests()
    return True, None


def decline_rp_request(request_id, user_id):
    """Отклонить РП-запрос"""
    req_id = str(request_id)
    if req_id not in rp_requests:
        return False, "Запрос не найден"
    
    req = rp_requests[req_id]
    if req["to_user"] != user_id:
        return False, "Вы не получатель"
    if req["status"] != "pending":
        return False, f"Запрос уже {req['status']}"
    
    req["status"] = "declined"
    save_rp_requests()
    return True, None


def get_pending_requests(user_id):
    """Получить ожидающие РП-запросы"""
    pending = []
    for req_id, req in rp_requests.items():
        if req["to_user"] == user_id and req["status"] == "pending":
            pending.append({
                "id": req_id,
                "from_user": req["from_user"],
                "action": req["action"],
                "created_at": req["created_at"],
            })
    return pending

# ============================================================
# 11. ОПРЕДЕЛЕНИЕ ПОЛА
# ============================================================

def analyze_gender_by_speech(text):
    """Анализ пола по речи (счётчики)"""
    if not text:
        return {"male": 0, "female": 0, "unknown": 1}
    
    text_lower = text.lower()
    scores = {"male": 0, "female": 0, "unknown": 0}
    
    male_self = [
        "я парень", "я мужчина", "я мужик",
        "пошел", "сделал", "купил", "заходил", "гулял",
        "играл", "ходил", "ел", "пил", "спал", "читал", "писал",
    ]
    female_self = [
        "я девушка", "я женщина",
        "пошла", "сделала", "купила", "заходила", "гуляла",
        "играла", "ходила", "ела", "пила", "спала", "читала", "писала",
    ]
    
    for word in male_self:
        if word in text_lower:
            scores["male"] += 1.5
    for word in female_self:
        if word in text_lower:
            scores["female"] += 1.5
    
    emotional_female = [
        "❤️", "💜", "😍", "🥰", "😊", "🥺", "😢", "😭",
        "💔", "😘", "💕", "🫶", "🌸", "🌺", "💗", "💖",
    ]
    emotional_male = ["💀", "👾", "🔥", "😈", "🤘", "💪", "👊", "😎"]
    
    for emoji in emotional_female:
        if emoji in text:
            scores["female"] += 0.5
    for emoji in emotional_male:
        if emoji in text:
            scores["male"] += 0.5
    
    if len(text) > 80:
        scores["female"] += 0.3
    if len(text) > 150:
        scores["female"] += 0.3
    if len(text) < 20:
        scores["male"] += 0.2
    
    male_slang = [
        "бро", "брат", "кек", "лол", "харош", "норм",
        "крч", "хз", "реально", "чисто", "топ", "вай",
    ]
    female_slang = [
        "мило", "кавай", "ня", "мур", "приветик",
        "пока-пока", "споки", "вкусняшка",
    ]
    
    for word in male_slang:
        if word in text_lower:
            scores["male"] += 0.3
    for word in female_slang:
        if word in text_lower:
            scores["female"] += 0.3
    
    if text.count('!') > 3:
        scores["female"] += 0.4
    if text.count('?') > 3:
        scores["female"] += 0.2
    if text.count('...') > 2:
        scores["female"] += 0.3
    if text.count('!!!') > 0:
        scores["female"] += 0.5
    
    if text.isupper() and len(text) > 10:
        scores["male"] += 0.5
    
    fact_words = ["факт", "реально", "точно", "на самом деле", "в принципе", "по сути"]
    for word in fact_words:
        if word in text_lower:
            scores["male"] += 0.2
    
    empathy_words = [
        "грустно", "жаль", "рада", "счастлива", "люблю",
        "обожаю", "нравится", "приятно", "душевно",
    ]
    for word in empathy_words:
        if word in text_lower:
            scores["female"] += 0.3
    
    return scores


def detect_gender_by_speech(text, user_id=None):
    """Определить пол по речи"""
    scores = analyze_gender_by_speech(text)
    if user_id and user_id in user_gender_history:
        history = user_gender_history[user_id]
        scores["male"] += history.get("male", 0) * 0.5
        scores["female"] += history.get("female", 0) * 0.5
        scores["unknown"] += history.get("unknown", 0) * 0.3
    
    if scores["male"] > scores["female"] + 1.5:
        return "male"
    elif scores["female"] > scores["male"] + 1.5:
        return "female"
    else:
        return "unknown"


def update_user_gender(user_id, text):
    """
    Обновить пол пользователя.
    
    ИСПРАВЛЕНО: НЕ вызывает save_all_data() при каждом сообщении.
    Вместо этого — дебаунс через _schedule_save().
    """
    if not user_id or not text:
        return
    
    scores = analyze_gender_by_speech(text)
    if user_id not in user_gender_history:
        user_gender_history[user_id] = {
            "male": 0, "female": 0, "unknown": 0,
            "last_update": datetime.now().isoformat(),
        }
    
    history = user_gender_history[user_id]
    history["male"] += scores["male"]
    history["female"] += scores["female"]
    history["unknown"] += scores["unknown"]
    history["last_update"] = datetime.now().isoformat()
    
    if history["male"] > history["female"] + 5:
        detected = "male"
    elif history["female"] > history["male"] + 5:
        detected = "female"
    else:
        detected = "unknown"
    
    user_gender[user_id] = detected
    if user_id in user_profiles:
        user_profiles[user_id]["gender"] = detected
    
    total = history["male"] + history["female"] + history["unknown"]
    if total > 100:
        history["male"] *= 0.8
        history["female"] *= 0.8
        history["unknown"] *= 0.8
    
    # ДЕБАУНС: не сохраняем сразу, а планируем
    _schedule_save()

# ============================================================
# 12. СТАНДАРТНЫЕ ФУНКЦИИ
# ============================================================

def get_user_glitches(user_id, owner_ids):
    """Получить глитчи пользователя"""
    if user_id in owner_ids:
        return float('inf')
    if user_id not in user_glitches:
        user_glitches[user_id] = 0
    return user_glitches[user_id]


def add_glitches(user_id, amount, owner_ids):
    """Добавить/убавить глитчи"""
    if user_id in owner_ids:
        return
    if user_id not in user_glitches:
        user_glitches[user_id] = 0
    user_glitches[user_id] += amount
    _schedule_save()


def spend_glitches(user_id, amount, owner_ids):
    """Потратить глитчи"""
    if user_id in owner_ids:
        return True
    if get_user_glitches(user_id, owner_ids) >= amount:
        user_glitches[user_id] -= amount
        _schedule_save()
        return True
    return False


def get_glitch_badge(glitches):
    """Получить бейдж по глитчам"""
    if glitches >= 1000:
        return "☄️"
    elif glitches >= 500:
        return "💫"
    elif glitches >= 200:
        return "🌟"
    elif glitches >= 100:
        return "⭐"
    elif glitches >= 50:
        return "✨"
    return ""


def get_combo_multiplier(combo):
    """Множитель за комбо"""
    if combo >= 1000:
        return 0.3
    elif combo >= 500:
        return 0.25
    elif combo >= 250:
        return 0.2
    elif combo >= 100:
        return 0.15
    elif combo >= 20:
        return 0.1
    elif combo >= 10:
        return 0.1
    return 0


def parse_duration(text):
    """Парсинг длительности"""
    duration = timedelta(minutes=15)
    
    if not text:
        return duration
    
    text_lower = text.lower()
    
    try:
        if "час" in text_lower:
            parts = text_lower.split("час")[0].strip().split()
            if parts:
                duration = timedelta(hours=int(parts[-1]))
        elif "мин" in text_lower:
            parts = text_lower.split("мин")[0].strip().split()
            if parts:
                duration = timedelta(minutes=int(parts[-1]))
        elif "день" in text_lower or "дн" in text_lower:
            parts = text_lower.split("день")[0].strip().split()
            if parts:
                duration = timedelta(days=int(parts[-1]))
        elif "недел" in text_lower:
            parts = text_lower.split("недел")[0].strip().split()
            if parts:
                duration = timedelta(weeks=int(parts[-1]))
    except (ValueError, IndexError):
        pass
    
    return duration


def get_user_gender(user_id):
    """Получить пол пользователя"""
    return user_gender.get(user_id, "unknown")

# ============================================================
# 13. СОХРАНЕНИЕ ВСЕХ ДАННЫХ
# ============================================================

def save_all_data():
    """
    Сохранить все данные немедленно.
    
    Используется при остановке бота. В обычной работе
    используй `_schedule_save()` для дебаунса.
    """
    global _last_save_time, _pending_save
    
    with _save_lock:
        _pending_save = False
        _last_save_time = time.time()
        
        try:
            _do_save_all_data()
            
            # Дополнительные файлы
            try:
                save_rp_commands()
            except Exception:
                pass
            
            try:
                save_rp_requests()
            except Exception:
                pass
            
            try:
                save_pending_battles()
            except Exception:
                pass
            
            return True
        except Exception as e:
            print(f"⚠️ Ошибка save_all_data: {e}")
            return False


def _do_save_all_data():
    """Внутренняя функция реального сохранения"""
    try:
        data = {
            "user_profiles": _convert_keys(user_profiles),
            "user_glitches": _convert_keys(user_glitches),
            "user_combo": _convert_keys(user_combo),
            "user_credits": _convert_keys(user_credits),
            "censorship_levels": _convert_keys(censorship_levels),
            "user_gender": _convert_keys(user_gender),
            "user_gender_history": _convert_keys(user_gender_history),
            "muted_users": _convert_keys(muted_users),
            "banned_users": _convert_keys(banned_users),
            "warned_users": _convert_keys(warned_users),
            "premium_users": _convert_keys(premium_users),
            "user_levels": _convert_keys(user_levels),
            "chat_owner_present": _convert_keys(chat_owner_present),
        }
        return save_data(data)
    except Exception as e:
        print(f"⚠️ Ошибка _do_save_all_data: {e}")
        return False


def load_all_data():
    """Загрузить все данные"""
    global user_profiles, user_glitches, user_combo, user_credits
    global censorship_levels, user_gender, user_gender_history
    global muted_users, banned_users, warned_users
    global premium_users, user_levels, chat_owner_present
    
    try:
        data = load_data()
        if data and isinstance(data, dict):
            user_profiles = _convert_keys_back(data.get("user_profiles", {}))
            user_glitches = _convert_keys_back(data.get("user_glitches", {}))
            user_combo = _convert_keys_back(data.get("user_combo", {}))
            user_credits = _convert_keys_back(data.get("user_credits", {}))
            censorship_levels = _convert_keys_back(data.get("censorship_levels", {}))
            user_gender = _convert_keys_back(data.get("user_gender", {}))
            user_gender_history = _convert_keys_back(data.get("user_gender_history", {}))
            muted_users = _convert_keys_back(data.get("muted_users", {}))
            banned_users = _convert_keys_back(data.get("banned_users", {}))
            warned_users = _convert_keys_back(data.get("warned_users", {}))
            premium_users = _convert_keys_back(data.get("premium_users", {}))
            user_levels = _convert_keys_back(data.get("user_levels", {}))
            chat_owner_present = _convert_keys_back(data.get("chat_owner_present", {}))
        
        load_rp_commands()
        load_rp_requests()
        load_pending_battles()
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки данных: {e}")
        return False

# ============================================================
# 14. ФОНОВЫЙ ЦИКЛ СОХРАНЕНИЯ
# ============================================================

_saver_thread = None
_saver_stop = threading.Event()


def _saver_loop():
    """Фоновый цикл сохранения"""
    while not _saver_stop.is_set():
        if _saver_stop.wait(10):
            break
        try:
            _flush_save_if_needed()
        except Exception as e:
            print(f"⚠️ Ошибка в saver_loop: {e}")


def start_saver():
    """Запустить фоновый цикл сохранения"""
    global _saver_thread
    
    if _saver_thread and _saver_thread.is_alive():
        return _saver_thread
    
    _saver_stop.clear()
    _saver_thread = threading.Thread(target=_saver_loop, daemon=True)
    _saver_thread.start()
    print("💾 Фоновое сохранение запущено (дебаунс 30с)")
    return _saver_thread


def stop_saver():
    """Остановить фоновый цикл"""
    _saver_stop.set()
    if _saver_thread:
        _saver_thread.join(timeout=5)
    print("💾 Фоновое сохранение остановлено")

# ============================================================
# 15. ЗАГРУЗКА ПРИ СТАРТЕ
# ============================================================

load_all_data()
start_saver()

print(f"📊 Пользователей: {len(user_profiles)}")
print(f"📊 Определено полов: {len(user_gender)}")
print(f"📊 РП-команд: {len(rp_commands)}")
print(f"📊 Ожидающих битв: {len(pending_battles)}")
print(f"💾 Автосохранение: каждые {AUTO_SAVE_DEBOUNCE}с (дебаунс)")