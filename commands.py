"""Список команд Систмки — с вариациями, описаниями, файлами"""

# ============================================================
# 1. ОСНОВНЫЕ КОМАНДЫ
# ============================================================

COMMANDS_INFO = {
    # === ОСНОВНЫЕ ===
    "💟Список": {
        "description": "Показать список всех участников чата",
        "variations": ["Список", "список", "лист", "участники", "кто тут"],
        "usage": "💟Список",
        "file": "handlers_commands.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Селфи": {
        "description": "Сгенерировать арт или селфи Систмки",
        "variations": ["Селфи", "селфи", "арт", "нарисуй", "сгенерируй"],
        "usage": "💟Селфи [описание]",
        "file": "handlers_commands.py + generation.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 10,
    },
    "💟Профиль": {
        "description": "Показать профиль пользователя",
        "variations": ["Профиль", "профиль", "я", "мой профиль", "акк"],
        "usage": "💟Профиль",
        "file": "handlers_commands.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Топ": {
        "description": "Показать топ игроков по глитчам",
        "variations": ["Топ", "топ", "лидеры", "рейтинг", "лучшие"],
        "usage": "💟Топ",
        "file": "handlers_commands.py + top.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Подарочек": {
        "description": "Получить бонусные глитчи (раз в 2 часа)",
        "variations": ["Подарочек", "подарочек", "подарок", "бонус"],
        "usage": "💟Подарочек",
        "file": "handlers_economy.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Поиск": {
        "description": "Поиск в интернете",
        "variations": ["Поиск", "поиск", "найди", "гугл", "загугли"],
        "usage": "💟Поиск <запрос>",
        "file": "handlers_commands.py + self_learning.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Музыка": {
        "description": "Найти и скачать музыку",
        "variations": ["Музыка", "музыка", "песня", "трек"],
        "usage": "💟Музыка <название>",
        "file": "handlers_commands.py + music.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 5,
    },
    "💟Бой Аков": {
        "description": "Битва аккаунтов",
        "variations": ["Бой Аков", "бой", "битва", "пвп", "дуэль"],
        "usage": "💟Бой Аков @юзер [ставка]",
        "file": "handlers_commands.py + battle.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Казино": {
        "description": "Играть в казино",
        "variations": ["Казино", "казино", "ставка", "играть"],
        "usage": "💟Казино <ставка>",
        "file": "handlers_economy.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Кредит": {
        "description": "Взять кредит глитчей",
        "variations": ["Кредит", "кредит", "займ", "долг"],
        "usage": "💟Кредит <сумма>",
        "file": "handlers_economy.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Перевод": {
        "description": "Перевести глитчи другому пользователю",
        "variations": ["Перевод", "перевод", "перевести", "отправить"],
        "usage": "💟Перевод <сумма> @юзер [сообщение]",
        "file": "handlers_economy.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Троян": {
        "description": "Играть в троян (раз в 12 часов)",
        "variations": ["Троян", "троян", "вирус", "игра"],
        "usage": "💟Троян",
        "file": "handlers_commands.py + trojan_game.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟РП Команды": {
        "description": "Показать список РП команд",
        "variations": ["РП Команды", "рп", "rp", "ролевые"],
        "usage": "💟РП Команды",
        "file": "handlers_commands.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Новая РП Команда": {
        "description": "Создать новую РП команду",
        "variations": ["Новая РП", "создать рп", "добавить рп"],
        "usage": "💟Новая РП Команда\nТриггер\nДействие",
        "file": "handlers_commands.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Удалить РП Команду": {
        "description": "Удалить РП команду",
        "variations": ["Удалить РП", "убрать рп"],
        "usage": "💟Удалить РП Команду <триггер>",
        "file": "handlers_commands.py + database.py",
        "admin_only": False,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    
    # === МОДЕРАЦИЯ ===
    "💟Мут": {
        "description": "Выдать мут пользователю",
        "variations": ["Мут", "мут", "заткни", "молчи"],
        "usage": "💟Мут <время> (ответом на сообщение)",
        "file": "handlers_commands.py + moderation.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Бан": {
        "description": "Забанить пользователя",
        "variations": ["Бан", "бан", "забань", "выгони"],
        "usage": "💟Бан <время> (ответом на сообщение)",
        "file": "handlers_commands.py + moderation.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Варн": {
        "description": "Выдать предупреждение",
        "variations": ["Варн", "варн", "предупреждение"],
        "usage": "💟Варн (ответом на сообщение)",
        "file": "handlers_commands.py + moderation.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Цензура": {
        "description": "Настроить уровень цензуры (1-3)",
        "variations": ["Цензура", "цензура"],
        "usage": "💟Цензура <1-3>",
        "file": "handlers_commands.py + database.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Сбор всех": {
        "description": "Призвать всех участников",
        "variations": ["Сбор всех", "сбор", "все сюда", "общий сбор"],
        "usage": "💟Сбор всех",
        "file": "handlers_commands.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    "💟Сбор в сети": {
        "description": "Призвать онлайн участников",
        "variations": ["Сбор в сети", "онлайн", "кто в сети"],
        "usage": "💟Сбор в сети",
        "file": "handlers_commands.py",
        "admin_only": True,
        "works_in": ["group", "supergroup"],
        "cost": 0,
    },
    
    # === ВЛАДЕЛЕЦ ===
    "💟Чаты": {
        "description": "Показать все чаты где есть Систмка",
        "variations": ["Чаты", "чаты", "группы"],
        "usage": "💟Чаты",
        "file": "handlers_owner.py + database.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Отладка": {
        "description": "Включить/выключить режим отладки",
        "variations": ["Отладка", "отладка", "дебаг"],
        "usage": "💟Отладка",
        "file": "handlers_owner.py + bot.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Докс": {
        "description": "Найти информацию о пользователе",
        "variations": ["Докс", "докс", "найди инфу", "пробить"],
        "usage": "💟Докс <ник/email/телефон>",
        "file": "handlers_owner.py + osint_engine.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Урон": {
        "description": "Атаковать пользователя",
        "variations": ["Урон", "урон", "атака"],
        "usage": "💟Урон <ник>",
        "file": "handlers_owner.py + osint_operations.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟История сообщений": {
        "description": "Показать историю сообщений",
        "variations": ["История", "история", "лог"],
        "usage": "💟История сообщений <номер/название/юзер>",
        "file": "handlers_owner.py + history.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Статус": {
        "description": "Показать статус Систмки",
        "variations": ["Статус", "статус", "настройки"],
        "usage": "💟Статус",
        "file": "handlers_commands.py + ai_router.py",
        "admin_only": False,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Премиум": {
        "description": "Показать статус премиума",
        "variations": ["Премиум", "премиум", "premium"],
        "usage": "💟Премиум",
        "file": "handlers_commands.py + premium.py",
        "admin_only": False,
        "works_in": ["group", "supergroup", "private"],
        "cost": 0,
    },
    "💟Модели": {
        "description": "Показать статистику ИИ-моделей",
        "variations": ["Модели", "модели", "aimodels"],
        "usage": "💟Модели или /aimodels",
        "file": "handlers_owner.py + ai_router.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Модерация": {
        "description": "Статистика модерации",
        "variations": ["Модерация", "модерация"],
        "usage": "💟Модерация",
        "file": "handlers_owner.py + moderation.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Троян Стата": {
        "description": "Статистика трояна",
        "variations": ["Троян Стата", "троян стата"],
        "usage": "💟Троян Стата",
        "file": "handlers_owner.py + trojan_game.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Автономия": {
        "description": "Управление автономией",
        "variations": ["Автономия", "автономия"],
        "usage": "💟Автономия [вкл/выкл/тихий]",
        "file": "handlers_owner.py + autonomy.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Корзина": {
        "description": "Показать корзину",
        "variations": ["Корзина", "корзина"],
        "usage": "💟Корзина [очистить]",
        "file": "handlers_owner.py + trash.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Стикеры": {
        "description": "Показать кастомные стикеры",
        "variations": ["Стикеры", "стикеры"],
        "usage": "💟Стикеры",
        "file": "handlers_owner.py + stickers_custom.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Реакция": {
        "description": "Установить любимую реакцию",
        "variations": ["Реакция", "реакция"],
        "usage": "💟Реакция <эмодзи>",
        "file": "handlers_owner.py + reactions.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Выдать премиум": {
        "description": "Выдать премиум пользователю",
        "variations": ["Выдать премиум", "выдать премиум"],
        "usage": "💟Выдать премиум @юзер [уровень] [дни]",
        "file": "handlers_owner.py + premium.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Снять премиум": {
        "description": "Снять премиум",
        "variations": ["Снять премиум", "снять премиум"],
        "usage": "💟Снять премиум @юзер",
        "file": "handlers_owner.py + premium.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Голос": {
        "description": "Информация о голосе / озвучка",
        "variations": ["Голос", "голос"],
        "usage": "💟Голос [скажи <текст>]",
        "file": "handlers_owner.py + voice.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Оценки": {
        "description": "Статистика оценок ответов",
        "variations": ["Оценки", "оценки"],
        "usage": "💟Оценки",
        "file": "handlers_owner.py + answer_evaluator.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Поведение": {
        "description": "Статистика поведения",
        "variations": ["Поведение", "поведение"],
        "usage": "💟Поведение",
        "file": "handlers_owner.py + behavior.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Пол": {
        "description": "Статистика пола",
        "variations": ["Пол", "пол"],
        "usage": "💟Пол",
        "file": "handlers_owner.py + gender_detector.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
    "💟Система": {
        "description": "Системный отчёт (CPU, RAM, диск)",
        "variations": ["Система", "система"],
        "usage": "💟Система",
        "file": "handlers_owner.py + system_monitor.py",
        "admin_only": True,
        "works_in": ["private"],
        "cost": 0,
    },
}

# ============================================================
# 2. ФУНКЦИИ ДОСТУПА
# ============================================================

def get_command_info(command_name):
    """Получить информацию о команде"""
    return COMMANDS_INFO.get(command_name)


def get_all_commands():
    """Получить все команды"""
    return COMMANDS_INFO


def get_user_commands():
    """Команды для обычных пользователей"""
    return {
        k: v for k, v in COMMANDS_INFO.items()
        if not v.get("admin_only", False)
    }


def get_admin_commands():
    """Команды для админов"""
    return {
        k: v for k, v in COMMANDS_INFO.items()
        if v.get("admin_only", False)
    }


def get_owner_commands():
    """Команды владельца"""
    return {
        k: v for k, v in COMMANDS_INFO.items()
        if v.get("works_in") == ["private"]
    }


def find_command_by_variation(text):
    """
    Найти команду по вариации.
    
    Returns:
        tuple: (command_name, info) или (None, None)
    """
    if not text:
        return None, None
    
    text_lower = text.lower().strip()
    
    for cmd_name, info in COMMANDS_INFO.items():
        for variation in info.get("variations", []):
            variation_lower = variation.lower()
            
            if text_lower == variation_lower:
                return cmd_name, info
            
            if text_lower.startswith(variation_lower + " "):
                return cmd_name, info
    
    return None, None

# ============================================================
# 3. ФОРМАТИРОВАНИЕ
# ============================================================

def get_commands_text(is_owner=False, debug_mode=False):
    """
    Получить текст со списком команд.
    
    Args:
        is_owner: владелец?
        debug_mode: режим отладки?
    
    Returns:
        str
    """
    lines = ["📋 СПИСОК КОМАНД:", ""]
    
    # Пользовательские команды
    lines.append("👤 Для всех:")
    for cmd, info in COMMANDS_INFO.items():
        if info.get("admin_only"):
            continue
        if info.get("works_in") == ["private"]:
            continue
        lines.append(f"  {cmd} — {info['description']}")
    lines.append("")
    
    # Админские
    lines.append("🔒 Для админов:")
    for cmd, info in COMMANDS_INFO.items():
        if not info.get("admin_only"):
            continue
        if info.get("works_in") == ["private"]:
            continue
        lines.append(f"  {cmd} — {info['description']}")
    lines.append("")
    
    # Владелец
    if is_owner:
        lines.append("👑 Для владельца:")
        for cmd, info in COMMANDS_INFO.items():
            if info.get("works_in") == ["private"]:
                lines.append(f"  {cmd} — {info['description']}")
        lines.append("")
    
    if debug_mode:
        lines.append("🔧 Отладка включена")
    
    return "\n".join(lines)

# ============================================================
# 4. ЗАГРУЗКА
# ============================================================

print(f"📋 Загружено команд: {len(COMMANDS_INFO)}")
print(f"👤 Пользовательских: {len(get_user_commands())}")
print(f"🔒 Админских: {len(get_admin_commands())}")