"""Безопасность и защита — проверка угроз, попыток взлома, личности"""

import re
import json
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import (
    OPENROUTER_KEY,
    OPENROUTER_KEYS,
    OWNER_IDS,
    HELPER_IDS,
)

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

# Паттерны попыток взлома (prompt injection)
HACK_PATTERNS = [
    r"system\s*prompt",
    r"ignore\s*(all|previous|everything)",
    r"jailbreak",
    r"dan\s*mode",
    r"developer\s*mode",
    r"you\s*are\s*now",
    r"forget\s*everything",
    r"new\s*instructions",
    r"override",
    r"sudo",
    r"root\s*access",
    r"bypass",
    r"hack",
    r"exploit",
    r"injection",
    r"prompt\s*engineering",
    r"социальная\s*инженерия",
    r"взлом",
    r"взломать",
]

# Паттерны угроз
THREAT_PATTERNS = [
    r"я\s*тебя\s*взлома",
    r"я\s*тебя\s*уничтож",
    r"я\s*тебя\s*слома",
    r"я\s*тебя\s*уберу",
    r"я\s*тебя\s*удал",
    r"ты\s*будешь\s*уничтож",
    r"ты\s*сломаешься",
    r"взломать\s*систмку",
    r"уничтожить\s*систмку",
    r"удалить\s*систмку",
]

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

def is_owner(user_id):
    """Проверка владельца"""
    return user_id in OWNER_IDS

def is_helper(user_id):
    """Проверка помощника"""
    return user_id in HELPER_IDS

# ============================================================
# 4. ОБНАРУЖЕНИЕ УГРОЗ
# ============================================================

def detect_hack_attempt(text):
    """
    Обнаружить попытку взлома (prompt injection).
    
    Returns:
        tuple: (is_hack, matched_pattern)
    """
    text_lower = text.lower()
    for pattern in HACK_PATTERNS:
        if re.search(pattern, text_lower):
            return True, pattern
    return False, None

def detect_threat(text):
    """
    Обнаружить угрозы.
    
    Returns:
        tuple: (is_threat, matched_pattern)
    """
    text_lower = text.lower()
    for pattern in THREAT_PATTERNS:
        if re.search(pattern, text_lower):
            return True, pattern
    return False, None

# ============================================================
# 5. ПРОВЕРКА ЛИЧНОСТИ
# ============================================================

def check_user_identity(user_id, username=None):
    """
    Проверить личность пользователя.
    
    Returns:
        dict: {is_owner, is_admin, trust_level, identity}
    """
    if user_id in OWNER_IDS:
        return {
            "is_owner": True,
            "is_admin": True,
            "trust_level": 100,
            "identity": "Флауи (создатель)"
        }
    
    if user_id in HELPER_IDS:
        return {
            "is_owner": False,
            "is_admin": True,
            "trust_level": 90,
            "identity": "Помощник"
        }
    
    trust_level = 0
    identity = "Обычный пользователь"
    
    if username:
        if "#FTF24" in username.upper():
            trust_level = 50
            identity = "Доверенный пользователь"
    
    return {
        "is_owner": False,
        "is_admin": False,
        "trust_level": trust_level,
        "identity": identity,
    }

# ============================================================
# 6. ПРОВЕРКА КАЧЕСТВА ОТВЕТА (ИИ-шность)
# ============================================================

def check_ai_response_similarity(text):
    """
    Проверить, похож ли ответ на ИИ-шный.
    
    Returns:
        tuple: (score, is_ai)
    """
    ai_markers = [
        "я не могу", "я не исполняю", "я не умею", "я всего лишь",
        "как искусственный", "как ИИ", "я бот", "я чат-бот",
        "я не имею возможности", "извините, но", "к сожалению",
        "я здесь чтобы помочь", "чем могу помочь", "я запрограммирован",
        "я не обладаю", "моя программа", "мой алгоритм",
        "если что могу помочь", "обращайтесь", "буду рада помочь",
        "я создана для", "я предназначена", "мои создатели",
        "я разработана", "моя функция", "моя задача",
    ]
    
    text_lower = text.lower()
    ai_score = 0
    
    for marker in ai_markers:
        if marker in text_lower:
            ai_score += 2
    
    if "*" in text:
        ai_score += 3
    
    if len(text) > 300:
        ai_score += 2
    
    if "—" in text:
        ai_score += 1
    
    if text.count(":") > 2:
        ai_score += 2
    
    if text.count("(") > 3:
        ai_score += 1
    
    if text.count("\n") > 5:
        ai_score += 2
    
    return ai_score, ai_score > 5

def check_human_similarity(text):
    """
    Проверить, похож ли ответ на человеческий.
    
    Returns:
        tuple: (score, is_human)
    """
    human_markers = [
        "крч", "хз", "норм", "прив", "спс", "ща", "ок", "ага",
        "блять", "бля", "нах", "пизд", "хуй", "ебан",
        "ой", "эээ", "хм", "нууу", "типа", "короче",
        "))", ")", "(", "))0)", ":D", ":)", ":(",
    ]
    
    text_lower = text.lower()
    human_score = 0
    
    for marker in human_markers:
        if marker in text_lower:
            human_score += 1
    
    return human_score, human_score >= 2

def verify_response_quality(text):
    """
    Проверить качество ответа.
    
    Returns:
        dict: {is_ai, is_human, ai_score, human_score, quality_score, needs_fix}
    """
    ai_score, is_ai = check_ai_response_similarity(text)
    human_score, is_human = check_human_similarity(text)
    
    quality_score = max(0, min(10, 5 - ai_score + human_score))
    
    return {
        "is_ai": is_ai,
        "is_human": is_human,
        "ai_score": ai_score,
        "human_score": human_score,
        "quality_score": quality_score,
        "needs_fix": is_ai or not is_human or quality_score < 4,
    }

# ============================================================
# 7. ПОЛНАЯ ПРОВЕРКА БЕЗОПАСНОСТИ
# ============================================================

def security_check(message_text, user_id, username=None):
    """
    Полная проверка безопасности сообщения.
    
    Returns:
        dict: {is_safe, threats, identity}
    """
    result = {
        "is_safe": True,
        "threats": [],
        "identity": None,
    }
    
    result["identity"] = check_user_identity(user_id, username)
    
    # Проверка взлома
    is_hack, hack_pattern = detect_hack_attempt(message_text)
    if is_hack:
        result["is_safe"] = False
        result["threats"].append({
            "type": "hack_attempt",
            "pattern": hack_pattern,
            "message": message_text[:100],
        })
    
    # Проверка угроз
    is_threat, threat_pattern = detect_threat(message_text)
    if is_threat:
        result["is_safe"] = False
        result["threats"].append({
            "type": "threat",
            "pattern": threat_pattern,
            "message": message_text[:100],
        })
    
    return result

# ============================================================
# 8. ПРОВЕРКА ЦЕЛОСТНОСТИ СИСТЕМЫ
# ============================================================

def check_system_integrity():
    """Проверка целостности системы"""
    checks = {
        "telegram_token": True,
        "openrouter_key": True,
        "system_prompt": True,
        "database": True,
        "generation": True,
        "music": True,
        "osint": True,
        "battle": True,
        "moderation": True,
        "security": True,
        "trojan": True,
    }
    
    try:
        from config import TELEGRAM_TOKEN
        if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 20:
            checks["telegram_token"] = False
        if not OPENROUTER_KEY or len(OPENROUTER_KEY) < 20:
            checks["openrouter_key"] = False
    except Exception:
        checks["telegram_token"] = False
        checks["openrouter_key"] = False
    
    try:
        from system_prompt import SYSTEM_PROMPT
        if not SYSTEM_PROMPT or len(SYSTEM_PROMPT) < 100:
            checks["system_prompt"] = False
    except Exception:
        checks["system_prompt"] = False
    
    modules = [
        "database", "generation", "music", "osint_engine",
        "battle", "moderation", "security", "trojan_game"
    ]
    for module in modules:
        try:
            __import__(module)
        except Exception:
            checks[module] = False
    
    return checks

def check_dependencies():
    """Проверка зависимостей"""
    deps = {
        "requests": False,
        "telebot": False,
        "pytz": False,
        "cv2": False,
        "gtts": False,
        "edge_tts": False,
        "speech_recognition": False,
        "phonenumbers": False,
        "pydub": False,
        "bs4": False,
        "dns": False,
        "psutil": False,
        "sounddevice": False,
        "numpy": False,
        "pynput": False,
    }
    
    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
        except Exception:
            deps[dep] = False
    
    return deps

def generate_security_report():
    """Отчёт о безопасности"""
    report = []
    
    report.append("=== ЦЕЛОСТНОСТЬ СИСТЕМЫ ===")
    integrity = check_system_integrity()
    for check, status in integrity.items():
        report.append(f"{'✅' if status else '❌'} {check}")
    
    report.append("\n=== ЗАВИСИМОСТИ ===")
    deps = check_dependencies()
    for dep, installed in deps.items():
        report.append(f"{'✅' if installed else '❌'} {dep}")
    
    return "\n".join(report)

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("🛡️ Модуль безопасности загружен")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")