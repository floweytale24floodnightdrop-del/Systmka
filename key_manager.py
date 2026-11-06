"""
key_manager.py — Управление ключом шифрования Систмки.

Ключ берётся из переменной окружения SYSTMKA_KEY.
Если её нет — используется fallback (для локальной разработки).
"""

import os
import hashlib
import base64


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

ENV_KEY_NAME = "SYSTMKA_KEY"

# Fallback для локальной разработки (НЕ ИСПОЛЬЗУЙ НА СЕРВЕРЕ!)
FALLBACK_KEY = "Sуstееemkа404"


# ============================================================
# 2. ПОЛУЧЕНИЕ КЛЮЧА
# ============================================================

def get_master_key() -> str:
    """
    Получить мастер-ключ.
    
    Приоритет:
    1. Переменная окружения SYSTMKA_KEY
    2. Fallback (только для локальной разработки)
    """
    key = os.environ.get(ENV_KEY_NAME)
    
    if key:
        return key
    
    print(f"⚠️ {ENV_KEY_NAME} не установлена — используется fallback")
    print(f"⚠️ НЕ ИСПОЛЬЗУЙ ЭТО НА СЕРВЕРЕ!")
    return FALLBACK_KEY


def derive_key(password: str, salt: bytes = None) -> bytes:
    """
    Произвести 32-байтовый ключ из пароля через SHA-256.
    
    Args:
        password: пароль
        salt: соль (если None — без соли)
    
    Returns:
        bytes: 32 байта
    """
    if salt:
        data = password.encode("utf-8") + salt
    else:
        data = password.encode("utf-8")
    
    return hashlib.sha256(data).digest()


def derive_key_b64(password: str, salt: bytes = None) -> str:
    """Произвести ключ и вернуть в Base64."""
    key = derive_key(password, salt)
    return base64.b64encode(key).decode("ascii")


# ============================================================
# 3. ПРОВЕРКА
# ============================================================

def is_env_key_set() -> bool:
    """Проверить, установлена ли переменная окружения."""
    return bool(os.environ.get(ENV_KEY_NAME))


def get_key_info() -> dict:
    """Информация о ключе (без раскрытия)."""
    key = get_master_key()
    return {
        "source": "env" if is_env_key_set() else "fallback",
        "length": len(key),
        "preview": key[:2] + "***" + key[-2:] if len(key) > 4 else "***",
    }


# ============================================================
# 4. ЗАГРУЗКА
# ============================================================

print("🔑 key_manager загружен")
print(f"🔐 Источник ключа: {'env' if is_env_key_set() else 'fallback'}")