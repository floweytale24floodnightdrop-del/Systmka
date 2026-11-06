"""Менеджер файлов Систмки — управляет всеми файлами (гибридная версия)"""

import os
import json
import re
from datetime import datetime

# ============================================================
# 1. КРИТИЧЕСКИЕ ФАЙЛЫ (ВРУЧНУЮ)
# ============================================================

CRITICAL_FILES = {
    "bot.py": {
        "id": 1,
        "purpose": "Главный файл запуска бота",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "config.py": {
        "id": 2,
        "purpose": "Настройки и токены",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "config_network.py": {
        "id": 3,
        "purpose": "Интернет, кэш, безопасные запросы",
        "importance": "high",
        "can_modify": True,
        "can_self_modify": True,
        "can_delete": False,
    },
    "database.py": {
        "id": 4,
        "purpose": "Хранилище данных",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "system_prompt.py": {
        "id": 5,
        "purpose": "Характер и личность Систмки",
        "importance": "critical",
        "can_modify": True,
        "can_self_modify": True,
        "can_delete": False,
    },
    "auto_import.py": {
        "id": 6,
        "purpose": "Регулятор импортов",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "import_core.py": {
        "id": 7,
        "purpose": "Ядро импортов",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "import_modules.py": {
        "id": 8,
        "purpose": "Загрузка всех модулей",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "import_loader.py": {
        "id": 9,
        "purpose": "Загрузчик импортов",
        "importance": "high",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "error_guardian.py": {
        "id": 10,
        "purpose": "Главный перехватчик импорта и ошибок",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "module_fixer.py": {
        "id": 11,
        "purpose": "Менеджер модулей (без перехвата)",
        "importance": "high",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "error_fixer.py": {
        "id": 12,
        "purpose": "Автоисправление ошибок",
        "importance": "high",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "trash.py": {
        "id": 13,
        "purpose": "Корзина с бэкапами",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "bot_handlers.py": {
        "id": 14,
        "purpose": "Регистрация обработчиков",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "bot_loops.py": {
        "id": 15,
        "purpose": "Фоновые потоки",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "bot_startup.py": {
        "id": 16,
        "purpose": "Загрузка данных при старте",
        "importance": "critical",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
    "auto_start.py": {
        "id": 17,
        "purpose": "Автозапуск",
        "importance": "medium",
        "can_modify": False,
        "can_self_modify": False,
        "can_delete": False,
    },
}

# ============================================================
# 2. ЭВРИСТИКА (ДЛЯ ОСТАЛЬНЫХ ФАЙЛОВ)
# ============================================================

IMPORTANCE_RULES = {
    # Критичные группы
    "critical": [
        "bot", "config", "database", "system_prompt",
        "import", "error_guardian", "module_fixer", "trash",
    ],
    "high": [
        "handlers_", "ai_", "osint", "voice", "security",
        "error_", "premium",
    ],
    "medium": [
        "game", "music", "battle", "moderation",
        "personality", "consciousness", "emotions",
    ],
    "low": [
        "progress", "commands", "messages", "profile",
        "response_cache", "log_manager",
    ],
}

MODIFY_RULES = {
    # Нельзя менять
    "forbidden": [
        "bot.py", "config.py", "config_network.py", "database.py",
        "system_prompt.py", "auto_import.py", "import_core.py",
        "import_modules.py", "import_loader.py", "error_guardian.py",
        "module_fixer.py", "error_fixer.py", "error_analyzer.py",
        "error_analyzer_advanced.py", "error_reporter.py",
        "trash.py", "auto_start.py", "log_manager.py",
        "bot_handlers.py", "bot_loops.py", "bot_startup.py",
        "ai_key_rotator.py", "ai_model_manager.py",
        "prompt_notes_manager.py", "auto_improve.py", "auto_install.py",
    ],
    # Нельзя удалять
    "no_delete": [
        "bot.py", "config.py", "config_network.py", "database.py",
        "system_prompt.py", "auto_import.py", "import_core.py",
        "import_modules.py", "import_loader.py", "error_guardian.py",
        "module_fixer.py", "trash.py", "bot_handlers.py",
        "bot_loops.py", "bot_startup.py",
    ],
}

def _get_importance(filename):
    """Определить важность файла по эвристике"""
    name = filename.lower()
    
    for level in ["critical", "high", "medium"]:
        for pattern in IMPORTANCE_RULES[level]:
            if pattern in name:
                return level
    
    return "low"

def _can_modify(filename):
    """Можно ли изменять файл"""
    if filename in MODIFY_RULES["forbidden"]:
        return False
    if filename.startswith("_"):
        return False
    return True

def _can_delete(filename):
    """Можно ли удалять файл"""
    if filename in MODIFY_RULES["no_delete"]:
        return False
    if filename.startswith("_"):
        return False
    return True

def _get_purpose(filename):
    """Получить назначение файла по эвристике"""
    purposes = {
        "handlers_": "Обработчик команд",
        "ai_": "Модуль ИИ",
        "osint": "OSINT модуль",
        "game": "Игровой модуль",
        "music": "Музыкальный модуль",
        "voice": "Голосовой модуль",
        "personality": "Личность Систмки",
        "consciousness": "Сознание",
        "emotions": "Эмоции",
        "error_": "Обработка ошибок",
        "prompt": "Управление промтами",
        "self_": "Самообучение",
        "response_": "Кэш ответов",
    }
    
    name = filename.lower()
    for pattern, purpose in purposes.items():
        if pattern in name:
            return purpose
    
    return "Модуль проекта"

# ============================================================
# 3. ДИНАМИЧЕСКИЙ РЕЕСТР
# ============================================================

def scan_all_files(directory="."):
    """
    Просканировать все .py файлы в директории.
    
    Returns:
        dict: {filename: info}
    """
    registry = {}
    next_id = 100  # начинаем с 100, чтобы не пересекаться с критическими
    
    for filename in os.listdir(directory):
        if not filename.endswith(".py"):
            continue
        
        if filename.startswith("_"):
            continue  # служебные
        
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        
        # Если критический — берём из CRITICAL_FILES
        if filename in CRITICAL_FILES:
            registry[filename] = CRITICAL_FILES[filename].copy()
            continue
        
        # Иначе — генерируем
        registry[filename] = {
            "id": next_id,
            "purpose": _get_purpose(filename),
            "importance": _get_importance(filename),
            "can_modify": _can_modify(filename),
            "can_self_modify": _can_modify(filename),
            "can_delete": _can_delete(filename),
            "load_frequency": "on_demand",
            "used_when": ["any"],
            "depends_on": [],
            "modules": [],
            "max_size": 200,
        }
        next_id += 1
    
    return registry


def get_file_registry():
    """
    Получить актуальный реестр (сканирует при каждом вызове).
    
    Returns:
        dict
    """
    return scan_all_files()


# Кэш реестра (обновляется при первом вызове)
_FILE_REGISTRY_CACHE = None


def _get_cached_registry():
    """Получить кэшированный реестр"""
    global _FILE_REGISTRY_CACHE
    if _FILE_REGISTRY_CACHE is None:
        _FILE_REGISTRY_CACHE = scan_all_files()
    return _FILE_REGISTRY_CACHE


# ============================================================
# 4. ПУБЛИЧНЫЕ ФУНКЦИИ
# ============================================================

def get_file_info(filename):
    """Получить информацию о файле"""
    registry = _get_cached_registry()
    return registry.get(filename)


def list_all_registered_files():
    """Список всех файлов"""
    return list(_get_cached_registry().keys())


def check_file_exists(filename):
    """Проверить существует ли файл"""
    return os.path.exists(filename)


def check_all_files():
    """Проверить все файлы"""
    registry = _get_cached_registry()
    results = {}
    for filename in registry:
        results[filename] = check_file_exists(filename)
    return results


def get_missing_files():
    """Получить отсутствующие файлы"""
    registry = _get_cached_registry()
    missing = []
    for filename in registry:
        if not check_file_exists(filename):
            missing.append(filename)
    return missing


def can_modify_file(filename):
    """Можно ли изменять файл"""
    info = get_file_info(filename)
    if info:
        return info.get("can_modify", False)
    return False


def can_delete_file(filename):
    """Можно ли удалять файл"""
    info = get_file_info(filename)
    if info:
        return info.get("can_delete", False)
    return False


def get_file_importance(filename):
    """Важность файла"""
    info = get_file_info(filename)
    if info:
        return info.get("importance", "unknown")
    return "unknown"


def get_file_dependencies(filename):
    """Зависимости файла"""
    info = get_file_info(filename)
    if info:
        return info.get("depends_on", [])
    return []


def refresh_registry():
    """Принудительно обновить реестр"""
    global _FILE_REGISTRY_CACHE
    _FILE_REGISTRY_CACHE = scan_all_files()
    return _FILE_REGISTRY_CACHE


def get_registry_stats():
    """Статистика реестра"""
    registry = _get_cached_registry()
    
    by_importance = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    modify_count = 0
    delete_count = 0
    
    for filename, info in registry.items():
        importance = info.get("importance", "unknown")
        if importance in by_importance:
            by_importance[importance] += 1
        if info.get("can_modify", False):
            modify_count += 1
        if info.get("can_delete", False):
            delete_count += 1
    
    return {
        "total_files": len(registry),
        "by_importance": by_importance,
        "can_modify": modify_count,
        "can_delete": delete_count,
    }


def format_registry_stats():
    """Форматировать статистику"""
    stats = get_registry_stats()
    lines = [
        "📁 РЕЕСТР ФАЙЛОВ:",
        f"  📊 Всего: {stats['total_files']}",
        f"  🔴 Критичных: {stats['by_importance']['critical']}",
        f"  🟠 Важных: {stats['by_importance']['high']}",
        f"  🟡 Средних: {stats['by_importance']['medium']}",
        f"  🟢 Низких: {stats['by_importance']['low']}",
        f"  ✏️ Можно менять: {stats['can_modify']}",
        f"  🗑 Можно удалять: {stats['can_delete']}",
    ]
    return "\n".join(lines)


# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

_registry = _get_cached_registry()
print(f"📁 Реестр файлов: {len(_registry)} файлов")
print(f"   🔴 Критичных: {get_registry_stats()['by_importance']['critical']}")
print(f"   ✏️ Можно менять: {get_registry_stats()['can_modify']}")