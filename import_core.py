"""ЯДРО — критически важные модули для работы бота"""

import os
import sys
import importlib
import json
from datetime import datetime

# ============================================================
# 1. КРИТИЧЕСКИЕ МОДУЛИ
# ============================================================

print("📦 Загрузка ядра...")

# === КОНФИГ ===
try:
    import config
    print("   ✅ config")
except Exception as e:
    print(f"   ❌ config — {e}")
    raise SystemExit("Критическая ошибка: не удалось загрузить config")

# === CONFIG_NETWORK ===
try:
    import config_network
    print("   ✅ config_network")
except Exception as e:
    print(f"   ❌ config_network — {e}")

# === DATABASE ===
try:
    import database
    print("   ✅ database")
except Exception as e:
    print(f"   ❌ database — {e}")
    raise SystemExit("Критическая ошибка: не удалось загрузить database")

# === SYSTEM_PROMPT ===
try:
    import system_prompt
    print("   ✅ system_prompt")
except Exception as e:
    print(f"   ❌ system_prompt — {e}")

# === TRASH ===
try:
    import trash
    print("   ✅ trash")
except Exception as e:
    print(f"   ❌ trash — {e}")

# === ERROR FIXER ===
try:
    import error_fixer
    print("   ✅ error_fixer")
except Exception as e:
    print(f"   ❌ error_fixer — {e}")

# === ERROR ANALYZER ===
try:
    import error_analyzer
    print("   ✅ error_analyzer")
except Exception as e:
    print(f"   ❌ error_analyzer — {e}")

# === ERROR REPORTER ===
try:
    import error_reporter
    print("   ✅ error_reporter")
except Exception as e:
    print(f"   ❌ error_reporter — {e}")

# ============================================================
# 2. ЯВНЫЕ ПЕРЕМЕННЫЕ (НЕ через globals())
# ============================================================

# === КОНФИГ ===
try:
    TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
    OWNER_IDS = config.OWNER_IDS
    HELPER_IDS = config.HELPER_IDS
    OPENROUTER_KEY = config.OPENROUTER_KEY
    OPENROUTER_KEYS = config.OPENROUTER_KEYS
    OPENROUTER_EMAILS = config.OPENROUTER_EMAILS
    GEMINI_KEY = config.GEMINI_KEY
    HUGGINGFACE_KEY = config.HUGGINGFACE_KEY
    DATA_FILE = config.DATA_FILE
    LEARNING_FILE = config.LEARNING_FILE
    KEY_STATS_FILE = config.KEY_STATS_FILE
    ALL_STICKERS = config.ALL_STICKERS
    moscow_tz = config.moscow_tz
except AttributeError as e:
    print(f"⚠️ Отсутствует переменная в config: {e}")

# === SYSTEM_PROMPT (КРИТИЧЕСКИ ВАЖНО!) ===
try:
    SYSTEM_PROMPT = system_prompt.SYSTEM_PROMPT
    print("   ✅ SYSTEM_PROMPT передан")
except AttributeError as e:
    print(f"⚠️ SYSTEM_PROMPT не найден: {e}")
    SYSTEM_PROMPT = "Ты Систмка."

# === DATABASE ===
db = database

# === CONFIG_NETWORK ===
try:
    check_internet = config_network.check_internet
    is_online = config_network.is_online
    cache_get = config_network.cache_get
    cache_set = config_network.cache_set
    safe_request = config_network.safe_request
    safe_get = config_network.safe_get
    safe_post = config_network.safe_post
except AttributeError as e:
    print(f"⚠️ Отсутствует функция в config_network: {e}")

# === TRASH ===
try:
    init_trash = trash.init_trash
    clean_logs_now = trash.clean_logs_now
    backup_file = trash.backup_file
    backup_file_before_change = trash.backup_file_before_change
    get_trash_list = trash.get_trash_list
    get_trash_stats = trash.get_trash_stats
    format_trash_stats = trash.format_trash_stats
    clear_trash = trash.clear_trash
    safe_change_file = trash.safe_change_file
    validate_file = trash.validate_file
except AttributeError as e:
    print(f"⚠️ Отсутствует функция в trash: {e}")

# === ERROR FIXER ===
try:
    auto_fix_all = error_fixer.auto_fix_all
    load_error_history = error_fixer.load_error_history
    save_error_history = error_fixer.save_error_history
    watchdog_loop = error_fixer.watchdog_loop
    fix_error_in_file = error_fixer.fix_error_in_file
    find_all_errors = error_fixer.find_all_errors
    find_runtime_errors_from_logs = error_fixer.find_runtime_errors_from_logs
    get_fix_stats = error_fixer.get_fix_stats
    format_fix_stats = error_fixer.format_fix_stats
except AttributeError as e:
    print(f"⚠️ Отсутствует функция в error_fixer: {e}")

# === ERROR ANALYZER ===
try:
    analyze_error = error_analyzer.analyze_error
    suggest_fix = error_analyzer.suggest_fix
    find_error_location = error_analyzer.find_error_location
except AttributeError as e:
    print(f"⚠️ Отсутствует функция в error_analyzer: {e}")

# === ERROR REPORTER ===
try:
    notify_error = error_reporter.notify_error
    load_notifications = error_reporter.load_notifications
    save_notifications = error_reporter.save_notifications
    get_error_stats = error_reporter.get_error_stats
except AttributeError as e:
    print(f"⚠️ Отсутствует функция в error_reporter: {e}")

# ============================================================
# 3. ПРОВЕРКА КРИТИЧЕСКИХ ИМПОРТОВ
# ============================================================

print("📦 Проверка критических импортов...")

required = [
    "SYSTEM_PROMPT",
    "db",
    "OWNER_IDS",
    "TELEGRAM_TOKEN",
    "OPENROUTER_KEYS",
    "clean_logs_now",
    "init_trash",
    "backup_file",
    "analyze_error",
    "suggest_fix",
    "find_error_location",
    "notify_error",
    "auto_fix_all",
    "load_error_history",
    "get_fix_stats",
    "format_fix_stats",
]

missing = []
for name in required:
    if name not in globals():
        missing.append(name)

if missing:
    print(f"⚠️ Отсутствуют импорты: {missing}")
else:
    print("✅ Все критические импорты доступны")

# ============================================================
# 4. ЭКСПОРТ
# ============================================================

__all__ = [
    # Config
    "TELEGRAM_TOKEN", "OWNER_IDS", "HELPER_IDS",
    "OPENROUTER_KEY", "OPENROUTER_KEYS", "OPENROUTER_EMAILS",
    "GEMINI_KEY", "HUGGINGFACE_KEY",
    "DATA_FILE", "LEARNING_FILE", "KEY_STATS_FILE",
    "ALL_STICKERS", "moscow_tz",
    
    # System prompt
    "SYSTEM_PROMPT",
    
    # Database
    "db",
    
    # Network
    "check_internet", "is_online", "cache_get", "cache_set",
    "safe_request", "safe_get", "safe_post",
    
    # Trash
    "init_trash", "clean_logs_now", "backup_file", "backup_file_before_change",
    "get_trash_list", "get_trash_stats", "format_trash_stats",
    "clear_trash", "safe_change_file", "validate_file",
    
    # Error fixer
    "auto_fix_all", "load_error_history", "save_error_history",
    "watchdog_loop", "fix_error_in_file", "find_all_errors",
    "find_runtime_errors_from_logs", "get_fix_stats", "format_fix_stats",
    
    # Error analyzer
    "analyze_error", "suggest_fix", "find_error_location",
    
    # Error reporter
    "notify_error", "load_notifications", "save_notifications", "get_error_stats",
]

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("📦 Ядро загружено")