"""Конфигурация Систмки — с поддержкой множества ключей и переменных окружения"""

import os
import json
import pytz
import random
from datetime import datetime
from pathlib import Path

# ============================================================
# 1. ТОКЕНЫ (ОСНОВНЫЕ)
# ============================================================

# На Render берет из Environment, локально - из заглушки
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ТВОЙ_ТОКЕН_ТЕЛЕГРАМ_ЗДЕСЬ")

# ============================================================
# 2. OPENROUTER КЛЮЧИ (12 НОВЫХ + СТАРЫЙ ДЛЯ СОВМЕСТИМОСТИ)
# ============================================================

# Для совместимости со старыми модулями
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "ТВОЙ_КЛЮЧ_OPENROUTER_ЗДЕСЬ")

# Для ротации (12 КЛЮЧЕЙ)
# На Render задается как строка через запятую: key1,key2,key3
_env_router_keys = os.environ.get("OPENROUTER_KEYS")

if _env_router_keys:
    OPENROUTER_KEYS = [k.strip() for k in _env_router_keys.split(",") if k.strip()]
else:
    OPENROUTER_KEYS = [
        "ТВОЙ_КЛЮЧ_OPENROUTER_1",
        "ТВОЙ_КЛЮЧ_OPENROUTER_2",
        "ТВОЙ_КЛЮЧ_OPENROUTER_3",
        "ТВОЙ_КЛЮЧ_OPENROUTER_4",
        "ТВОЙ_КЛЮЧ_OPENROUTER_5",
        "ТВОЙ_КЛЮЧ_OPENROUTER_6",
        "ТВОЙ_КЛЮЧ_OPENROUTER_7",
        "ТВОЙ_КЛЮЧ_OPENROUTER_8",
        "ТВОЙ_КЛЮЧ_OPENROUTER_9",
        "ТВОЙ_КЛЮЧ_OPENROUTER_10",
        "ТВОЙ_КЛЮЧ_OPENROUTER_11",
        "ТВОЙ_КЛЮЧ_OPENROUTER_12",
    ]

# Почты для отображения в статусе
_env_router_emails = os.environ.get("OPENROUTER_EMAILS")

if _env_router_emails:
    OPENROUTER_EMAILS = [e.strip() for e in _env_router_emails.split(",") if e.strip()]
else:
    OPENROUTER_EMAILS = [
        "Systmka24Floweytale5@gmail.com",
        "Systmka24Floweytale2@gmail.com",
        "Systmka24Floweytale1@gmail.com",
        "Systmka24Floweytale3@gmail.com",
        "timetoclosewinmega@gmail.com",
        "alexpetrabars@gmail.com",
        "aleks.petka@gmail.com",
        "musicforever22889@gmail.com",
        "russiantriacommunity@gmail.com",
        "winmegaundercover@gmail.com",
        "liquidteamhouse@gmail.com",
        "waterevasionviofficial@gmail.com",
    ]

# ============================================================
# 3. ДОПОЛНИТЕЛЬНЫЕ КЛЮЧИ
# ============================================================

GEMINI_KEY = os.environ.get("GEMINI_KEY", "ТВОЙ_КЛЮЧ_GEMINI_ЗДЕСЬ")
HUGGINGFACE_KEY = os.environ.get("HUGGINGFACE_KEY", "ТВОЙ_КЛЮЧ_HUGGINGFACE_ЗДЕСЬ")

# ============================================================
# 4. ВЛАДЕЛЬЦЫ И ПОМОЩНИКИ
# ============================================================

_env_owners = os.environ.get("OWNER_IDS")
if _env_owners:
    OWNER_IDS = [int(i.strip()) for i in _env_owners.split(",") if i.strip().isdigit()]
else:
    OWNER_IDS = [8946758568, 7435271379]

_env_helpers = os.environ.get("HELPER_IDS")
if _env_helpers:
    HELPER_IDS = [int(i.strip()) for i in _env_helpers.split(",") if i.strip().isdigit()]
else:
    HELPER_IDS = [1893053205]

# ============================================================
# 5. ВРЕМЯ
# ============================================================

moscow_tz = pytz.timezone('Europe/Moscow')

# ============================================================
# 6. ФАЙЛЫ ДАННЫХ
# ============================================================

DATA_FILE = "systmka_data.json"
LEARNING_FILE = "learning_data.json"
KEY_STATS_FILE = "key_stats.json"

# ============================================================
# 7. СТИКЕРЫ
# ============================================================

ALL_STICKERS = [
    "CAACAgIAAxkBAAFS30BqkKEfAAFg8UZX6pcOQITj1JLeo4sAAj-BAAJok3FIFS0WM2uZ6Fs9BA",
    "CAACAgIAAxkBAAFS311qkKIFcsimvXDIfrrTkbSpYTAVgQACcYIAAohocUhZN3J6jyaDqj0E",
    "CAACAgIAAxkBAAFS321qkKKcZOG160yEMwAB3N_VWaSDHHcAAoVtAAIIGXhIFT21TFg605M9BA",
    "CAACAgIAAxkBAAFS329qkKK-6az52X-AW0WQPHkIBSsEWwACS30AApwUeUgTlaCrJ2ZcID0E",
    "CAACAgIAAxkBAAFS33tqkKNsSLCBpwkvfW6xK4skrfxcVQACM3IAAnG5eUjKw3mMUON7CT0E",
    "CAACAgIAAxkBAAFS339qkKOZh6YZoDWAM6nry1WttMOJ_gACGnMAAsfSeEjv62B0u4GOjj0E",
    "CAACAgIAAxkBAAFS34FqkKO2VwZV69X5Dl4lIfLMXFUspAACD24AAhfneUjG95lVuSm7JT0E",
    "CAACAgIAAxkBAAFS34VqkKPwnKc295rReMiQbd0HBdGwkAACYXcAAqnHeUiTM7I6om14iz0E",
    "CAACAgIAAxkBAAFS35hqkKSJ_SQIBOUsTSua_IwEQ_AzqAACDZUAAuxTqUgPqdJIVvq63T0E",
    "CAACAgIAAxkBAAFS35xqkKTQEVL617htyTC-Rjqchu2zhQACxYEAAogmqEgipXHHmjuHwD0",
    "CAACAgIAAxkBAAFS36JqkKUeCw3po4NR1bo7bhJWK75MDwACW5wAArr1KUmwLzAnO184GT0E",
]

# ============================================================
# 8. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_openrouter_keys():
    """Получить список ключей OpenRouter"""
    return OPENROUTER_KEYS

def get_openrouter_emails():
    """Получить список email для ключей"""
    return OPENROUTER_EMAILS

def get_gemini_key():
    """Получить ключ Gemini"""
    return GEMINI_KEY

def get_huggingface_key():
    """Получить ключ Hugging Face"""
    return HUGGINGFACE_KEY

def get_owner_ids():
    """Получить ID владельцев"""
    return OWNER_IDS

def get_helper_ids():
    """Получить ID помощников"""
    return HELPER_IDS

# ============================================================
# 9. ФУНКЦИИ СОХРАНЕНИЯ/ЗАГРУЗКИ (ДЛЯ СОВМЕСТИМОСТИ)
# ============================================================

def _convert_to_serializable(obj):
    """Конвертировать объект в сериализуемый формат"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_convert_to_serializable(i) for i in obj]
    if hasattr(obj, '__dict__'):
        return str(obj)
    return obj

def save_data(data, filename=None):
    """Сохранить данные в JSON"""
    if filename is None:
        filename = DATA_FILE
    
    try:
        serializable_data = _convert_to_serializable(data)
        temp_file = filename + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, filename)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

def load_data(filename=None):
    """Загрузить данные из JSON"""
    if filename is None:
        filename = DATA_FILE
    
    try:
        if not os.path.exists(filename):
            return None
        
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup_file = filename + ".tmp"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
    except:
        return None

# ============================================================
# 10. ЛЕНИВАЯ ИНИЦИАЛИЗАЦИЯ КЛЮЧЕЙ
# ============================================================

def init_all_keys():
    """
    Инициализировать все ключи.
    
    ВАЖНО: вызывается в bot.py, а НЕ при импорте config.py.
    Это убирает циклический импорт config ↔ ai_key_rotator.
    """
    try:
        from ai_key_rotator import init_keys
        init_keys(OPENROUTER_KEYS, OPENROUTER_EMAILS, GEMINI_KEY, HUGGINGFACE_KEY)
        print("🔑 Ключи инициализированы")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка инициализации ключей: {e}")
        return False

# ============================================================
# 11. ЗАГРУЗКА
# ============================================================

print("🔧 Конфигурация загружена")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")
print(f"📧 OpenRouter почт: {len(OPENROUTER_EMAILS)}")
print(f"🔑 Gemini: {'✅' if GEMINI_KEY and GEMINI_KEY != 'ТВОЙ_КЛЮЧ_GEMINI_ЗДЕСЬ' else '❌'}")
print(f"🔑 Hugging Face: {'✅' if HUGGINGFACE_KEY and HUGGINGFACE_KEY != 'ТВОЙ_КЛЮЧ_HUGGINGFACE_ЗДЕСЬ' else '❌'}")
print(f"👑 Владельцев: {len(OWNER_IDS)}")
print(f"💫 Помощников: {len(HELPER_IDS)}")