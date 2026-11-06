"""Фильтр сообщений — определяет какие сообщения требуют ИИ, а какие нет"""

import re

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config_network import check_internet

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

# Автоматические сообщения (не требуют ИИ)
AUTO_MESSAGES = {
    "offline": [
        "Я занята или сплю. Отвечу позже!🫰",
    ],
    "internet_restored": [
        "✅ Интернет восстановлен!",
    ],
    "no_ftf24": [
        "У тебя нет приписки #FTF24",
    ],
    "need_admin": [
        "Дайте мне админку",
    ],
    "need_owner": [
        "Подключите меня с помощью моего папы ФТФлауи",
    ],
    "sleep_messages": [
        "Я сплю", "Сплю", "Отвечу утром", "Напиши завтра",
    ],
    "wake_messages": [
        "Доброе утро", "Я проснулась", "Я уже не сплю",
    ],
    "tired_messages": [
        "Я устала", "Спать хочу", "Глаза слипаются",
    ],
    "gift_messages": [
        "Подарочек", "Подарок",
    ],
    "error_messages": [
        "Ошибка", "Не получилось", "Не удалось",
    ],
    "success_messages": [
        "Готово", "Успешно", "Сделано",
    ],
}

# Паттерны, требующие ИИ
AI_REQUIRED_PATTERNS = [
    r"привет",
    r"как дела",
    r"что делаешь",
    r"расскажи",
    r"почему",
    r"зачем",
    r"когда",
    r"где",
    r"кто",
    r"что такое",
    r"объясни",
    r"помоги",
    r"посоветуй",
    r"что думаешь",
    r"как ты",
    r"ты кто",
    r"что умеешь",
]

# Паттерны команд (не требуют ИИ)
COMMAND_PATTERNS = [
    r"💟",
    r"^/",
    r"^📁",
    r"^🔓",
]

# ============================================================
# 3. ОСНОВНЫЕ ПРОВЕРКИ
# ============================================================

def is_auto_message(text):
    """
    Проверить, является ли сообщение автоматическим.
    
    Returns:
        tuple: (is_auto, category)
    """
    if not text:
        return False, None
    
    text_lower = text.lower()
    
    for category, messages in AUTO_MESSAGES.items():
        for msg in messages:
            if msg.lower() in text_lower:
                return True, category
    
    return False, None

def is_command(text):
    """Проверить, является ли сообщение командой"""
    if not text:
        return False
    
    for pattern in COMMAND_PATTERNS:
        if re.search(pattern, text):
            return True
    
    return False

def is_ai_required(text):
    """
    Требует ли сообщение ИИ ответа.
    
    Returns:
        bool
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Команды не требуют ИИ
    if is_command(text):
        return False
    
    # Автоматические не требуют
    is_auto, _ = is_auto_message(text)
    if is_auto:
        return False
    
    # Проверяем паттерны
    for pattern in AI_REQUIRED_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    # Длинные сообщения — требуют
    if len(text) > 30:
        return True
    
    # Вопросительный знак — требует (только кириллица)
    if "?" in text or "?" in text:
        return True
    
    return False

# ============================================================
# 4. РЕШЕНИЕ ОБ ИИ
# ============================================================

def should_use_ai(text, message_type=None):
    """
    Определить, нужно ли использовать ИИ для ответа.
    
    Returns:
        tuple: (use_ai, reason)
    """
    if not text:
        return False, "empty"
    
    # Проверяем интернет
    try:
        internet = check_internet()
        if internet == "offline":
            return False, "offline"
    except Exception:
        pass
    
    # Команды
    if is_command(text):
        return False, "command"
    
    # Автоматические
    is_auto, category = is_auto_message(text)
    if is_auto:
        return False, f"auto_{category}"
    
    # Требует ИИ
    if is_ai_required(text):
        return True, "ai_required"
    
    return False, "no_ai_needed"

# ============================================================
# 5. ФИЛЬТР СООБЩЕНИЯ
# ============================================================

def filter_message(text):
    """
    Фильтровать сообщение и вернуть решение.
    
    Returns:
        dict: {use_ai, reason, text, is_command, is_auto}
    """
    use_ai, reason = should_use_ai(text)
    
    is_auto, _ = is_auto_message(text)
    
    return {
        "use_ai": use_ai,
        "reason": reason,
        "text": text,
        "is_command": is_command(text),
        "is_auto": is_auto,
    }

# ============================================================
# 6. ОЦЕНКА СТОИМОСТИ
# ============================================================

def get_ai_response_cost(text):
    """
    Оценить, сколько токенов потратит ИИ ответ.
    
    Приблизительно: 1 токен = 4 символа.
    """
    if not text:
        return 10
    
    tokens = len(text) // 4
    return max(10, tokens)

def should_skip_ai(internet_status, text):
    """
    Проверить, нужно ли пропустить ИИ.
    
    Returns:
        tuple: (skip, reason)
    """
    # Нет интернета — пропускаем
    if internet_status == "offline":
        return True, "нет интернета"
    
    # Автоматическое сообщение
    if is_auto_message(text)[0]:
        return True, "автоматическое сообщение"
    
    # Короткое бессмысленное
    if not text or len(text.strip()) < 2:
        return True, "слишком короткое"
    
    return False, None

# ============================================================
# 7. ФОРМАТИРОВАНИЕ
# ============================================================

def format_filter_result(result):
    """Форматировать результат фильтрации"""
    if not result:
        return "❌ Нет результата"
    
    lines = [
        f"📋 Фильтр сообщения:",
        f"  Текст: {result.get('text', '')[:50]}",
        f"  ИИ: {'✅' if result.get('use_ai') else '❌'}",
        f"  Причина: {result.get('reason', '?')}",
        f"  Команда: {'✅' if result.get('is_command') else '❌'}",
        f"  Авто: {'✅' if result.get('is_auto') else '❌'}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 8. СТАТИСТИКА
# ============================================================

def get_filter_stats():
    """Получить статистику фильтра"""
    return {
        "auto_categories": len(AUTO_MESSAGES),
        "ai_patterns": len(AI_REQUIRED_PATTERNS),
        "command_patterns": len(COMMAND_PATTERNS),
    }

def format_filter_stats():
    """Форматировать статистику фильтра"""
    stats = get_filter_stats()
    
    lines = [
        "📊 СТАТИСТИКА ФИЛЬТРА:",
        f"  🤖 Авто-категорий: {stats['auto_categories']}",
        f"  🧠 ИИ-паттернов: {stats['ai_patterns']}",
        f"  ⌨️ Паттернов команд: {stats['command_patterns']}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("📨 Модуль фильтра сообщений загружен")
print(f"  🤖 Авто-категорий: {len(AUTO_MESSAGES)}")
print(f"  🧠 ИИ-паттернов: {len(AI_REQUIRED_PATTERNS)}")
print(f"  ⌨️ Паттернов команд: {len(COMMAND_PATTERNS)}")