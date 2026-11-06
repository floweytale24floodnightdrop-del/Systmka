"""Общие утилиты для системы обработки ошибок"""

import os
import sys

# ============================================================
# 1. БЕЗОПАСНЫЙ STDOUT
# ============================================================

def ensure_stdout():
    """Восстановить sys.stdout/sys.stderr, если они закрыты"""
    try:
        if sys.stdout is None or getattr(sys.stdout, "closed", False):
            try:
                sys.stdout = open(os.devnull, "w", encoding="utf-8")
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        if sys.stderr is None or getattr(sys.stderr, "closed", False):
            try:
                sys.stderr = open(os.devnull, "w", encoding="utf-8")
            except Exception:
                pass
    except Exception:
        pass


def safe_print(*args, **kwargs):
    """Безопасный print — не падает, если stdout закрыт"""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        ensure_stdout()
        try:
            print(*args, **kwargs)
        except Exception:
            pass

# ============================================================
# 2. ПРОВЕРКА STDIN
# ============================================================

def is_stdin_available():
    """Проверить, доступен ли stdin (терминал)"""
    try:
        if sys.stdin is None:
            return False
        if getattr(sys.stdin, "closed", False):
            return False
        return sys.stdin.isatty()
    except Exception:
        return False

# ============================================================
# 3. МОДУЛИ, КОТОРЫЕ НЕ РАЗМОРАЖИВАЕМ
# ============================================================

SKIP_UNFREEZE = {
    # Ядро
    "bot",
    "auto_start",
    "auto_import",
    "import_core",
    "import_modules",
    "import_loader",
    
    # Бот-обвязка
    "bot_handlers",
    "bot_loops",
    "bot_startup",
    "message_processor",
    
    # Обработчики
    "handlers_main",
    "handlers_start",
    "handlers_commands",
    "handlers_owner",
    "handlers_economy",
    "handlers_media",
    "handlers_rp_osint",
    
    # Регистраторы
    "impression_manager",
}

# ============================================================
# 4. ИГНОРИРУЕМЫЕ МОДУЛИ (НЕ ЗАМОРАЖИВАЕМ!)
# ============================================================

IGNORED_MODULES = [
    # Android-модули
    '_elementtree', '_wmi', '_uuid', 'defusedxml', 'cryptography',
    'ujson', 'redis', 'hiredis', 'opentelemetry', 'xxhash',
    'aiosignal', 'StringIO', 'cStringIO', 'backports',
    'brotlicffi', 'brotli', 'pycares',
    # C-расширения
    '_quoting_c', '_helpers_c', '_frozenlist',
    'yarl._quoting_c', 'propcache._helpers_c', 'frozenlist._frozenlist',
    'redis.utils', 'redis.client', 'redis.connection', 'redis.commands',
    'redis.asyncio', 'redis.cluster', 'redis.sentinel', 'redis.event',
    'redis.observability',
    # Прочие
    '_sqlite3', '_ssl', 'org.python',
    # Устаревшие
    'pwd', 'fcntl', 'gui', '__builtin__', 'urllib2',
    'Queue', 'std', 'downloads', 'uncalled_for', 'cython',
    # НОВОЕ: несовместимы с Python 3.14 (внутренние модули httpx)
    'http2',
    'httpcore2',
    'h2',
    'hpack',
    'hyperframe',
    # НОВОЕ: несовместимы с Python 3.14 (сторонние)
    'speedtest',
    'griffe',
    'toolsets._tool_search',
    'fastmcp',
]


def is_ignored_module(module_name):
    """Проверить, является ли модуль игнорируемым"""
    if not module_name:
        return False
    for ignored in IGNORED_MODULES:
        if ignored in module_name:
            return True
    return False

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

ensure_stdout()

print("🛡️ error_common загружен")
print(f"📋 SKIP_UNFREEZE: {len(SKIP_UNFREEZE)} модулей")
print(f"📋 IGNORED_MODULES: {len(IGNORED_MODULES)} модулей")