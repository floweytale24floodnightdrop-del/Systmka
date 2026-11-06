"""Обработка текста — токсичность, ссылки, упоминания, перевод, суммаризация"""

import re
import json
import requests

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 3. ТОКСИЧНОСТЬ
# ============================================================

def detect_toxicity(text):
    """
    Определение токсичности через ИИ.
    
    Returns:
        int: 1-10 (1 = не токсично, 10 = очень токсично)
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
                        "content": "Определи уровень токсичности текста от 1 до 10. Ответь только числом."
                    },
                    {"role": "user", "content": text}
                ],
                "max_tokens": 10
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content'].strip()
                match = re.search(r'\d+', result)
                if match:
                    return int(match.group())
    except Exception as e:
        print(f"⚠️ Ошибка detect_toxicity: {e}")
    
    # Fallback — простая проверка
    toxic_words = [
        "тупой", "дурак", "идиот", "дебил", "блять", "сука",
        "пизда", "хуй", "мудак", "тварь", "мразь",
    ]
    text_lower = text.lower()
    count = sum(1 for w in toxic_words if w in text_lower)
    return min(10, count * 2)

# ============================================================
# 4. ИЗВЛЕЧЕНИЕ ЭЛЕМЕНТОВ
# ============================================================

def extract_links(text):
    """Извлечь ссылки из текста"""
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
    return urls

def extract_mentions(text):
    """Извлечь упоминания @username"""
    mentions = re.findall(r'@(\w+)', text)
    return mentions

def extract_hashtags(text):
    """Извлечь хэштеги #tag"""
    hashtags = re.findall(r'#(\w+)', text)
    return hashtags

def extract_emails(text):
    """Извлечь email"""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return emails

def extract_phones(text):
    """Извлечь номера телефонов (простой паттерн)"""
    phones = re.findall(r'\+?\d[\d\s\-()]{8,15}\d', text)
    return phones

# ============================================================
# 5. ПЕРЕВОД
# ============================================================

def translate_text(text, target_lang="ru"):
    """
    Перевести текст через ИИ.
    
    Args:
        text: текст
        target_lang: целевой язык ("ru", "en", "de" и т.д.)
    
    Returns:
        str: перевод
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
                    {"role": "system", "content": f"Переведи на {target_lang}. Только перевод, без пояснений."},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 300
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка translate_text: {e}")
    
    return text

# ============================================================
# 6. СУММАРИЗАЦИЯ
# ============================================================

def summarize_text(text):
    """
    Суммаризировать текст через ИИ.
    
    Returns:
        str: краткое содержание
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
                    {"role": "system", "content": "Суммаризируй в 2-3 предложения."},
                    {"role": "user", "content": text}
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
        print(f"⚠️ Ошибка summarize_text: {e}")
    
    return text[:200]

# ============================================================
# 7. ОПРЕДЕЛЕНИЕ ЯЗЫКА
# ============================================================

def detect_language(text):
    """
    Определить язык текста.
    
    Returns:
        str: код языка ("ru", "en", ...) или "unknown"
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
                    {"role": "system", "content": "Определи язык текста. Ответь только кодом (ru, en, de и т.д.)."},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip().lower()
    except Exception as e:
        print(f"⚠️ Ошибка detect_language: {e}")
    
    # Простой fallback по кириллице/латинице
    if re.search(r'[а-яА-ЯёЁ]', text):
        return "ru"
    elif re.search(r'[a-zA-Z]', text):
        return "en"
    
    return "unknown"

# ============================================================
# 8. АНАЛИЗ НАСТРОЕНИЯ
# ============================================================

def analyze_sentiment(text):
    """
    Анализ настроения текста.
    
    Returns:
        str: "positive", "negative" или "neutral"
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
                        "content": "Определи настроение текста: positive, negative или neutral. Ответь одним словом."
                    },
                    {"role": "user", "content": text}
                ],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip().lower()
    except Exception as e:
        print(f"⚠️ Ошибка analyze_sentiment: {e}")
    
    # Простой fallback
    text_lower = text.lower()
    positive = ["хорошо", "круто", "спасибо", "люблю", "отлично", "супер", "класс"]
    negative = ["плохо", "ужасно", "ненавижу", "бесит", "тупо", "отстой"]
    
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    
    return "neutral"

# ============================================================
# 9. ОБРАБОТКА ТЕКСТА
# ============================================================

def clean_text(text):
    """
    Очистить текст от лишних пробелов и переносов.
    
    Returns:
        str: очищенный текст
    """
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    
    # Убираем пробелы в начале и конце
    text = text.strip()
    
    return text

def truncate_text(text, max_length=500, suffix="..."):
    """
    Обрезать текст до max_length.
    
    Returns:
        str: обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def count_words(text):
    """Посчитать слова"""
    return len(text.split())

def count_chars(text, with_spaces=True):
    """Посчитать символы"""
    if with_spaces:
        return len(text)
    return len(text.replace(" ", ""))

def detect_caps_lock(text):
    """Определить, написан ли текст капсом (больше 70% заглавных)"""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return caps_ratio > 0.7

def has_repeated_chars(text, threshold=5):
    """Проверить наличие повторяющихся символов (ааааа)"""
    for match in re.finditer(r'(.)\1{2,}', text):
        if len(match.group()) >= threshold:
            return True
    return False

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("📝 Модуль обработки текста загружен")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")