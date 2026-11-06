"""Управление аккаунтом Флауи — исправление сокращений, каваи-режим, автоответы"""

import re
import random
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ АККАУНТА
# ============================================================

ACCOUNT_SETTINGS = {
    "fix_abbreviations": True,   # Исправление сокращений
    "kawaii_mode": False,        # Каваи режим
    "remove_spam_chats": True,   # Удаление спам-чатов
    "forward_deleted": True,     # Пересыл удалённых
    "auto_reply_afk": True,      # Автоответ если АФК
    "auto_reply_online": False,  # Автоответ если в сети
    "voice_transcription": True, # Расшифровка голосовых
}

# Статус Флауи
flawey_status = {
    "is_online": False,
    "last_seen": None,
    "afk_message": "",
}

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 4. ИСПРАВЛЕНИЕ СОКРАЩЕНИЙ
# ============================================================

def fix_abbreviations(text):
    """
    Исправить сокращения и сленг.
    
    Returns:
        str: исправленный текст
    """
    replacements = {
        # Технологии
        "чат гпт": "ChatGPT",
        "чат жпт": "ChatGPT",
        "чатгпт": "ChatGPT",
        "гпт": "GPT",
        "жпт": "GPT",
        "андроид": "Android",
        "айфон": "iPhone",
        "айпад": "iPad",
        "макбук": "MacBook",
        "виндовс": "Windows",
        "линукс": "Linux",
        "телеграм": "Telegram",
        "телега": "Telegram",
        "тг": "TG",
        "инста": "Instagram",
        "инстаграм": "Instagram",
        "ютуб": "YouTube",
        "тикток": "TikTok",
        "вк": "VK",
        "ок": "OK",
        
        # Сленг
        "спс": "спасибо",
        "пж": "пожалуйста",
        "прив": "привет",
        "ща": "сейчас",
        "хз": "не знаю",
        "норм": "нормально",
        "крч": "короче",
        "короч": "короче",
        "типа": "типа",
        "чо": "что",
        "чё": "что",
        "че": "что",
        "нету": "нет",
        "тута": "тут",
        "тама": "там",
        "здеся": "здесь",
        "енто": "это",
        "етот": "этот",
        "ета": "эта",
        "ети": "эти",
        "ихний": "их",
        "евонный": "его",
        "ейный": "её",
    }
    
    fixed = text
    for old, new in replacements.items():
        fixed = re.sub(
            r'\b' + re.escape(old) + r'\b',
            new,
            fixed,
            flags=re.IGNORECASE
        )
    
    return fixed

# ============================================================
# 5. КАВАИ-РЕЖИМ
# ============================================================

def apply_kawaii_mode(text):
    """
    Применить каваи-режим — замена матов, добавление эмодзи.
    
    Returns:
        str: изменённый текст
    """
    # Замена матов
    replacements = {
        "блять": "блин",
        "бля": "блин",
        "сука": "бака",
        "пиздец": "пипец",
        "хуй": "хей",
        "нах": "ну",
        "ебан": "эх",
        "пизд": "пи",
        "хуев": "плох",
        "заебал": "заколебал",
        "охуел": "обалдел",
        "пизда": "попа",
    }
    
    fixed = text
    for old, new in replacements.items():
        fixed = re.sub(old, new, fixed, flags=re.IGNORECASE)
    
    # Смайлики
    kawaii_emojis = [
        "🩷", "💝", "💖", "💕", "💞", "💓", "💗", "💌", "💋",
        "✨", "🫰", "🫶", "🙏", "🛐", "❤️‍🩹", "🥺", "😇",
        "😘", "😊", "🌸", "🎀", "🍓", "🥰",
    ]
    
    if random.random() < 0.7:
        emoji = random.choice(kawaii_emojis)
        fixed += f" {emoji}"
    
    # Удлинение слов (повтор букв)
    fixed = re.sub(r'([а-яА-Я])(\1)', r'\1\1\1', fixed)
    
    # Добавление скобочек
    if random.random() < 0.5:
        fixed += " ^^"
    
    # РП действия
    rp_actions = [
        "*обнимает за ручку*",
        "*мурчит*",
        "*улыбается*",
        "*держит твою ручку*",
        "*промычал*",
        "*прижимается*",
    ]
    if random.random() < 0.3:
        fixed += f"\n{random.choice(rp_actions)} <3"
    
    return fixed

# ============================================================
# 6. ИСПРАВЛЕНИЕ КОМАНД
# ============================================================

def fix_commands(text):
    """
    Исправить текст команд (добавить эмодзи, если не хватает).
    
    Returns:
        str: исправленный текст
    """
    command_fixes = {
        "список": "💟Список",
        "селфи": "💟Селфи",
        "профиль": "💟Профиль",
        "музыка": "💟Музыка",
        "казино": "💟Казино",
        "кредит": "💟Кредит",
        "перевод": "💟Перевод",
        "троян": "💟Троян",
        "топ": "💟Топ",
        "подарочек": "💟Подарочек",
        "бой аков": "💟Бой Аков",
        "рп команды": "💟РП Команды",
        "поиск": "💟Поиск",
        "мут": "💟Мут",
        "бан": "💟Бан",
        "варн": "💟Варн",
        "цензура": "💟Цензура",
        "сбор всех": "💟Сбор всех",
        "сбор в сети": "💟Сбор в сети",
    }
    
    text_lower = text.lower().strip()
    for cmd, fixed_cmd in command_fixes.items():
        if text_lower == cmd:
            return fixed_cmd
        if text_lower.startswith(cmd + " "):
            return fixed_cmd + text[len(cmd):]
    
    return text

# ============================================================
# 7. ОБРАБОТКА СООБЩЕНИЯ ФЛАУИ
# ============================================================

def process_flawey_message(text):
    """
    Обработать сообщение Флауи.
    
    Returns:
        str: обработанный текст
    """
    processed = text
    
    if ACCOUNT_SETTINGS["fix_abbreviations"]:
        processed = fix_abbreviations(processed)
    
    if ACCOUNT_SETTINGS["kawaii_mode"]:
        processed = apply_kawaii_mode(processed)
    
    processed = fix_commands(processed)
    
    return processed

# ============================================================
# 8. АВТООТВЕТ
# ============================================================

def generate_auto_reply(message_text):
    """
    Сгенерировать автоответ через ИИ.
    
    Returns:
        str: ответ
    """
    try:
        key = _get_openrouter_key()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты Флауи (Flowey). Ты общаешься от лица Флауи.\n"
                            "Ты спокойный, дружелюбный, но не слишком разговорчивый.\n"
                            "Отвечай коротко. Если просят рест — скажи что занят и ответишь позже.\n"
                            "Если спрашивают что-то важное — скажи что посмотришь позже.\n"
                            "Не давай обещаний. Не флиртуй. Будь вежливым."
                        )
                    },
                    {"role": "user", "content": message_text}
                ],
                "max_tokens": 100
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка generate_auto_reply: {e}")
    
    return "Привет! Я сейчас занят, отвечу позже."

# ============================================================
# 9. РАСШИФРОВКА ГОЛОСОВЫХ
# ============================================================

def transcribe_voice_for_flawey(voice_data, bot, file_id):
    """
    Расшифровать голосовое сообщение для Флауи.
    
    Returns:
        str или None
    """
    try:
        from utils_media import transcribe_voice
        return transcribe_voice(voice_data, bot, file_id)
    except Exception as e:
        print(f"⚠️ Ошибка transcribe_voice_for_flawey: {e}")
        return None

# ============================================================
# 10. ФОРМАТИРОВАНИЕ УДАЛЁННЫХ / ИЗМЕНЁННЫХ
# ============================================================

def format_deleted_message(message_text, user_name):
    """Форматировать удалённое сообщение"""
    return f"🗑 Удалённое сообщение от {user_name}:\n\n{message_text}"

def format_edited_message(old_text, new_text, user_name):
    """Форматировать изменённое сообщение"""
    return (
        f"✏️ {user_name} изменил сообщение:\n\n"
        f"ДО:\n{old_text}\n\n"
        f"ПОСЛЕ:\n{new_text}"
    )

# ============================================================
# 11. УПРАВЛЕНИЕ НАСТРОЙКАМИ
# ============================================================

def toggle_setting(setting_name):
    """
    Переключить настройку (True ↔ False).
    
    Returns:
        tuple: (setting_name, new_value) или (None, None)
    """
    if setting_name in ACCOUNT_SETTINGS:
        ACCOUNT_SETTINGS[setting_name] = not ACCOUNT_SETTINGS[setting_name]
        return setting_name, ACCOUNT_SETTINGS[setting_name]
    return None, None

def set_setting(setting_name, value):
    """Установить настройку"""
    if setting_name in ACCOUNT_SETTINGS:
        ACCOUNT_SETTINGS[setting_name] = bool(value)
        return True
    return False

def format_settings():
    """Форматировать все настройки"""
    lines = ["⚙️ НАСТРОЙКИ АККАУНТА:"]
    for name, value in ACCOUNT_SETTINGS.items():
        icon = "✅" if value else "❌"
        lines.append(f"  {icon} {name}: {value}")
    return "\n".join(lines)

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("👤 Модуль управления аккаунтом загружен")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")
print(f"⚙️ Настроек: {len(ACCOUNT_SETTINGS)}")