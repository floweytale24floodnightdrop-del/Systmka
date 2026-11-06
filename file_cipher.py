"""
file_cipher.py — Твой уникальный шифр (Цезарь + эмодзи).

Работает ТОЛЬКО с текстовыми данными (JSON, строки).
НЕ ИСПОЛЬЗУЕТСЯ для .py файлов (Python их не выполнит).
"""

import os
import json
import base64
from typing import Optional

from key_manager import get_master_key, derive_key


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

EN_LOWER = "abcdefghijklmnopqrstuvwxyz"
EN_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
RU_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
RU_UPPER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

# Замены
REPLACEMENTS = {
    "s": "💟",
    "S": "💜",
    "A": "🤍",
    "a": "🖤",
}

REVERSE_REPLACEMENTS = {v: k for k, v in REPLACEMENTS.items()}


# ============================================================
# 2. ЦЕЗАРЬ
# ============================================================

def caesar_shift(text: str, shift: int) -> str:
    """Сдвиг Цезаря для английских и русских букв."""
    result = []
    for ch in text:
        if ch in EN_LOWER:
            idx = EN_LOWER.index(ch)
            result.append(EN_LOWER[(idx + shift) % 26])
        elif ch in EN_UPPER:
            idx = EN_UPPER.index(ch)
            result.append(EN_UPPER[(idx + shift) % 26])
        elif ch in RU_LOWER:
            idx = RU_LOWER.index(ch)
            result.append(RU_LOWER[(idx + shift) % 33])
        elif ch in RU_UPPER:
            idx = RU_UPPER.index(ch)
            result.append(RU_UPPER[(idx + shift) % 33])
        else:
            result.append(ch)
    return "".join(result)


def caesar_encode(text: str) -> str:
    """
    Кодирование с разным сдвигом:
    - Маленькие английские: +3
    - Большие английские: +1
    - Русские: +2
    """
    result = []
    for ch in text:
        if ch in EN_LOWER:
            result.append(EN_LOWER[(EN_LOWER.index(ch) + 3) % 26])
        elif ch in EN_UPPER:
            result.append(EN_UPPER[(EN_UPPER.index(ch) + 1) % 26])
        elif ch in RU_LOWER:
            result.append(RU_LOWER[(RU_LOWER.index(ch) + 2) % 33])
        elif ch in RU_UPPER:
            result.append(RU_UPPER[(RU_UPPER.index(ch) + 2) % 33])
        else:
            result.append(ch)
    return "".join(result)


def caesar_decode(text: str) -> str:
    """Обратный Цезарь."""
    result = []
    for ch in text:
        if ch in EN_LOWER:
            result.append(EN_LOWER[(EN_LOWER.index(ch) - 3) % 26])
        elif ch in EN_UPPER:
            result.append(EN_UPPER[(EN_UPPER.index(ch) - 1) % 26])
        elif ch in RU_LOWER:
            result.append(RU_LOWER[(RU_LOWER.index(ch) - 2) % 33])
        elif ch in RU_UPPER:
            result.append(RU_UPPER[(RU_UPPER.index(ch) - 2) % 33])
        else:
            result.append(ch)
    return "".join(result)


# ============================================================
# 3. ЗАМЕНА
# ============================================================

def apply_replacements(text: str) -> str:
    """Заменить s/S/A/a на эмодзи."""
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def reverse_replacements(text: str) -> str:
    """Обратная замена эмодзи на буквы."""
    for emoji, letter in REVERSE_REPLACEMENTS.items():
        text = text.replace(emoji, letter)
    return text


# ============================================================
# 4. ПОЛНЫЙ ЦИКЛ
# ============================================================

def encrypt_text(text: str, key: Optional[str] = None) -> str:
    """Зашифровать текст твоим алгоритмом."""
    if key is None:
        key = get_master_key()
    
    # 1. Base64 (чтобы эмодзи не ломали кодировку)
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    
    # 2. Цезарь
    text_caesar = caesar_encode(text_b64)
    
    # 3. Замена
    text_replaced = apply_replacements(text_caesar)
    
    # 4. XOR с ключом (для уникальности)
    key_hash = derive_key(key)[:16]
    final = []
    for i, ch in enumerate(text_replaced):
        final.append(ch)
        # XOR на уровне символов — добавляет уникальности
        if i % 3 == 0:
            final.append(chr(ord(ch) ^ ord(key_hash[i % len(key_hash)])))
    
    return "".join(final)


def decrypt_text(text: str, key: Optional[str] = None) -> str:
    """Расшифровать текст."""
    if key is None:
        key = get_master_key()
    
    # 1. Убираем XOR-вставки
    key_hash = derive_key(key)[:16]
    cleaned = []
    i = 0
    while i < len(text):
        cleaned.append(text[i])
        if i % 3 == 0:
            i += 2  # пропускаем XOR-символ
        else:
            i += 1
    
    text_clean = "".join(cleaned)
    
    # 2. Обратная замена
    text_replaced = reverse_replacements(text_clean)
    
    # 3. Обратный Цезарь
    text_caesar = caesar_decode(text_replaced)
    
    # 4. Base64
    decoded = base64.b64decode(text_caesar.encode("ascii")).decode("utf-8")
    
    return decoded


# ============================================================
# 5. ФАЙЛЫ
# ============================================================

def encrypt_file(path: str, key: Optional[str] = None) -> bool:
    """Зашифровать файл."""
    try:
        if not os.path.exists(path):
            print(f"⚠️ Файл не найден: {path}")
            return False
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        encrypted = encrypt_text(content, key)
        
        encrypted_path = path + ".enc"
        with open(encrypted_path, "w", encoding="utf-8") as f:
            f.write(encrypted)
        
        print(f"🔐 Зашифрован: {path} → {encrypted_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка шифрования {path}: {e}")
        return False


def decrypt_file(path: str, key: Optional[str] = None) -> Optional[str]:
    """Расшифровать файл."""
    try:
        if not os.path.exists(path):
            print(f"⚠️ Файл не найден: {path}")
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return decrypt_text(content, key)
    except Exception as e:
        print(f"❌ Ошибка расшифровки {path}: {e}")
        return None


# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

print("🔐 file_cipher загружен")
print(f"📋 Замен: {len(REPLACEMENTS)}")
print(f"🔤 Цезарь: EN lower +3, EN upper +1, RU +2")