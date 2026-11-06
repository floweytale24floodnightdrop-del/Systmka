"""Загрузчик импортов — проверка и принудительная загрузка модулей"""

import os
import sys
import importlib
import time

# ============================================================
# 1. СПИСКИ МОДУЛЕЙ
# ============================================================

# Критические модули (без них бот не работает)
CRITICAL_MODULES = [
    "config",
    "config_network",
    "database",
    "system_prompt",
    "auto_import",
    "ai_key_rotator",
    "ai_model_manager",
    "ai_router",
    "ai_request_handler",
    "ai_gemini",
    "ai_huggingface",
    "ai_selector",
    "ai_stats",
    "ai_models",
]

# Основные модули (важные, но не критические)
MAIN_MODULES = [
    # Обработчики
    "handlers_start",
    "handlers_main",
    "handlers_commands",
    "handlers_owner",
    "handlers_economy",
    "handlers_media",
    "handlers_rp_osint",
    
    # Функциональные
    "generation",
    "music",
    "music_download",
    "music_lyrics",
    "battle",
    "osint_engine",
    "osint_operations",
    "osint_phone_email",
    "osint_username_fio",
    "moderation",
    "security",
    "trojan_game",
    "premium",
    "history",
    "top",
    
    # Личность
    "behavior",
    "personality",
    "personality_builder",
    "personality_analyzer",
    "impression_generator",
    "impression_manager",
    "emotions",
    "consciousness",
    "desires",
    "dreams",
    "attachments",
    "creativity",
    "self_reflection",
    "opinions",
    
    # Голос
    "voice",
    "voice_cloner",
    
    # Игры
    "games",
    "game_engine",
    "game_creator",
    "game_manager",
    
    # Утилиты
    "message_filter",
    "self_learning",
    "learning_core",
    "learning_manager",
    "file_manager",
    "file_organizer",
    "system_monitor",
    "system_control",
    "app_controller",
    "debug_changes",
    "log_manager",
    "terminal_chat",
    "progress",
    "commands",
    "messages",
    "profile",
    "memes",
    "dox_database",
    "file_analyzer",
    "auto_improve",
    "auto_install",
    "utils_media",
    "utils_text",
    "utils_osint_extended",
    "stickers_custom",
    "sleep",
    "fatigue",
    "morning_greetings",
    "reactions",
    "weather",
    "holidays",
    
    # ИИ
    "autonomy",
    "frozen_requests",
    "roleplay",
    "rp_commands",
    "message_analyzer",
    "prompt_notes_manager",
    "response_cache",
    "error_analyzer_advanced",
    
    # Бот
    "bot_startup",
    "bot_handlers",
    "bot_loops",
    "bot_monitor",
]

# ============================================================
# 2. ПРОВЕРКА ИМПОРТОВ
# ============================================================

def is_module_loaded(module_name):
    """
    Проверить, загружен ли модуль в sys.modules.
    
    Args:
        module_name: имя модуля
    
    Returns:
        bool
    """
    return module_name in sys.modules

def check_imports():
    """
    Проверить загрузку критических модулей.
    
    Проверяет через sys.modules, а не через globals().
    
    Returns:
        dict: {loaded: [...], missing: [...]}
    """
    loaded = []
    missing = []
    
    for module_name in CRITICAL_MODULES:
        if is_module_loaded(module_name):
            loaded.append(module_name)
        else:
            missing.append(module_name)
    
    return {
        "loaded": loaded,
        "missing": missing,
        "all_ok": len(missing) == 0,
    }

def verify_all_imports():
    """
    Полная проверка (с принтом).
    
    Returns:
        bool: True если все критические загружены
    """
    result = check_imports()
    
    if result["all_ok"]:
        print(f"✅ Все критические модули загружены ({len(result['loaded'])})")
        return True
    else:
        print(f"❌ Отсутствуют критически важные модули:")
        for m in result["missing"]:
            print(f"   • {m}")
        return False

# ============================================================
# 3. ЗАГРУЗКА МОДУЛЕЙ
# ============================================================

def load_module(module_name):
    """
    Загрузить один модуль.
    
    Returns:
        tuple: (success, error)
    """
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, f"ImportError: {str(e)[:100]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"

def load_critical_modules():
    """
    Загрузить только критические модули.
    
    Returns:
        tuple: (loaded, failed)
    """
    loaded = []
    failed = []
    
    for module_name in CRITICAL_MODULES:
        if is_module_loaded(module_name):
            loaded.append(module_name)
            continue
        
        success, error = load_module(module_name)
        if success:
            loaded.append(module_name)
            print(f"✅ {module_name}")
        else:
            failed.append({"name": module_name, "error": error})
            print(f"❌ {module_name} — {error}")
    
    return loaded, failed

def force_load_imports():
    """
    Принудительно загрузить все модули (критические + основные).
    
    Returns:
        tuple: (loaded, failed)
    """
    all_modules = CRITICAL_MODULES + MAIN_MODULES
    loaded = []
    failed = []
    total = len(all_modules)
    
    print(f"📦 Загрузка модулей ({total} шт.)...")
    
    for i, module_name in enumerate(all_modules, 1):
        # Пропускаем уже загруженные
        if is_module_loaded(module_name):
            loaded.append(module_name)
            continue
        
        success, error = load_module(module_name)
        if success:
            loaded.append(module_name)
            print(f"   ✅ [{i}/{total}] {module_name}")
        else:
            failed.append({"name": module_name, "error": error})
            print(f"   ❌ [{i}/{total}] {module_name} — {error}")
    
    print(f"\n📊 Загружено: {len(loaded)}/{total}")
    if failed:
        print(f"❌ Не загружено: {len(failed)}")
    
    return loaded, failed

def force_load_all_with_report():
    """
    Полная загрузка с подробным отчётом.
    
    Returns:
        dict: {loaded, failed, total}
    """
    loaded, failed = force_load_imports()
    
    report = {
        "loaded": loaded,
        "failed": failed,
        "total": len(loaded) + len(failed),
    }
    
    print("\n" + "=" * 60)
    print(f"📦 ИТОГОВЫЙ ОТЧЁТ:")
    print(f"   ✅ Загружено: {len(loaded)}")
    print(f"   ❌ Провалено: {len(failed)}")
    print("=" * 60)
    
    if failed:
        print("\n❌ Не загруженные модули:")
        for f in failed:
            print(f"   • {f['name']}: {f['error']}")
    
    return report

# ============================================================
# 4. ПЕРЕЗАГРУЗКА МОДУЛЯ
# ============================================================

def reload_module(module_name):
    """
    Перезагрузить модуль.
    
    Returns:
        bool: успех
    """
    try:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка перезагрузки {module_name}: {e}")
        return False

def unload_module(module_name):
    """
    Выгрузить модуль из sys.modules.
    
    Returns:
        bool: был ли модуль загружен
    """
    if module_name in sys.modules:
        del sys.modules[module_name]
        return True
    return False

# ============================================================
# 5. ИНФОРМАЦИЯ О МОДУЛЯХ
# ============================================================

def get_loaded_modules_count():
    """Получить количество загруженных модулей проекта"""
    project_modules = CRITICAL_MODULES + MAIN_MODULES
    loaded_count = sum(1 for m in project_modules if is_module_loaded(m))
    return {
        "loaded": loaded_count,
        "total": len(project_modules),
    }

def format_modules_status():
    """Форматировать статус модулей"""
    stats = get_loaded_modules_count()
    result = check_imports()
    
    lines = [
        "📦 СТАТУС МОДУЛЕЙ:",
        f"  Всего в списке: {stats['total']}",
        f"  Загружено: {stats['loaded']}/{stats['total']}",
        "",
    ]
    
    if result["all_ok"]:
        lines.append("✅ Все критические модули загружены")
    else:
        lines.append(f"❌ Отсутствуют критические: {len(result['missing'])}")
        for m in result["missing"]:
            lines.append(f"  • {m}")
    
    return "\n".join(lines)

def format_failed_modules(failed):
    """Форматировать список проваленных модулей"""
    if not failed:
        return "✅ Все модули загружены"
    
    lines = [f"❌ Не загружено модулей: {len(failed)}"]
    for f in failed:
        lines.append(f"  • {f['name']}: {f['error']}")
    
    return "\n".join(lines)

# ============================================================
# 6. БЕЗОПАСНЫЙ ИМПОРТ
# ============================================================

def safe_import(module_name, attr=None):
    """
    Безопасно импортировать модуль или атрибут.
    
    Args:
        module_name: имя модуля
        attr: имя атрибута (если None — возвращает модуль)
    
    Returns:
        модуль/атрибут или None
    """
    try:
        module = importlib.import_module(module_name)
        if attr is None:
            return module
        return getattr(module, attr, None)
    except ImportError:
        return None
    except Exception:
        return None

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📦 import_loader загружен")
print(f"📋 Критических модулей: {len(CRITICAL_MODULES)}")
print(f"📋 Основных модулей: {len(MAIN_MODULES)}")
print(f"💡 Используй force_load_all_with_report() для полной загрузки")