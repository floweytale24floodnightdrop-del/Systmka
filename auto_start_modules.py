"""Загрузка модулей для автозапуска Систмки"""

import importlib
from datetime import datetime

# ============================================================
# 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПЕЧАТИ
# ============================================================

def print_status(message, level="INFO"):
    """Печать статуса с иконкой"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️",
        "OK": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "BOLD": "🔹",
        "VPN": "🔌",
        "BOT": "🤖",
        "MODULE": "📦",
        "NETWORK": "🌐",
        "SYSTEM": "🖥️",
        "FILE": "📁",
        "LOG": "📋",
        "CONSOLE": "💬",
        "PING": "📊",
        "GUARDIAN": "🛡️"
    }.get(level, "ℹ️")
    
    try:
        print(f"[{timestamp}] {prefix} {message}", flush=True)
        return
    except (ValueError, UnicodeEncodeError, OSError):
        pass
    
    try:
        print(f"[{timestamp}] {message}", flush=True)
        return
    except Exception:
        pass


def print_separator(char="=", length=60):
    """Печать разделителя"""
    try:
        print(char * length, flush=True)
    except Exception:
        pass


def print_header(text, icon="🤖"):
    """Печать заголовка"""
    print_separator()
    try:
        print(f"{icon} {text}")
    except (UnicodeEncodeError, ValueError):
        try:
            print(text)
        except Exception:
            pass
    print_separator()

# ============================================================
# 2. ЗАГРУЗКА МОДУЛЕЙ
# ============================================================

def load_module(module_name):
    """Загрузить модуль с обработкой ошибок"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, f"ImportError: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# Список критических модулей
CRITICAL_MODULES = [
    # Ядро
    'trash', 'config', 'database', 'system_prompt',
    'auto_import', 'error_fixer', 'error_reporter', 'error_analyzer',
    
    # Обработчики
    'handlers_start', 'handlers_main', 'handlers_commands', 'handlers_owner',
    'handlers_economy', 'handlers_media',
    
    # Личность
    'personality', 'personality_builder',
    'impression_generator', 'consciousness', 'emotions', 'desires', 'dreams',
    'attachments', 'creativity', 'self_reflection', 'opinions',
    
    # Голос
    'voice', 'voice_cloner',
    
    # Игры
    'games', 'game_engine', 'game_creator', 'game_manager',
    
    # Сеть (PC)
    'system_monitor',
    
    # Бот
    'bot_monitor',
    
    # Генерация и музыка
    'generation', 'music', 'music_download', 'music_lyrics', 'memes',
    
    # OSINT
    'dox_database', 'osint_engine', 'osint_phone_email', 'osint_username_fio',
    'osint_operations',
    
    # Сообщения и обучение
    'message_filter', 'self_learning', 'learning_core',
    'file_manager', 'file_organizer',
    'debug_changes', 'log_manager', 'system_control', 'app_controller',
    
    # Терминал
    'terminal_chat', 'progress', 'commands', 'messages',
    'rp_commands', 'profile', 'file_analyzer',
    'auto_improve', 'auto_install',
    'utils_media', 'utils_text', 'utils_osint_extended', 'stickers_custom',
    
    # Сон и реакции
    'sleep', 'fatigue', 'morning_greetings', 'reactions', 'weather', 'holidays',
    
    # ИИ
    'autonomy', 'frozen_requests', 'ai_router',
    'ai_request_handler', 'roleplay', 'message_analyzer', 'premium',
    'ai_models', 'ai_stats', 'ai_selector', 'ai_mode',
    'ai_gemini', 'ai_huggingface', 'ai_key_rotator', 'ai_model_manager',
    'prompt_notes_manager', 'learning_manager',
    
    # Стартовые
    'bot_startup', 'bot_handlers', 'bot_loops',
    'history', 'top', 'moderation', 'security',
    'trojan_game', 'battle', 'response_cache',
    'error_analyzer_advanced', 'debug_command_handler',
]


def force_load_imports():
    """Принудительная загрузка всех модулей"""
    print_header("ЗАГРУЗКА МОДУЛЕЙ", "📦")
    
    loaded = []
    failed = []
    total = len(CRITICAL_MODULES)
    
    for i, module_name in enumerate(CRITICAL_MODULES):
        success, error = load_module(module_name)
        if success:
            loaded.append(module_name)
            print_status(f"[{i+1}/{total}] {module_name} — загружен", "OK")
        else:
            failed.append({"name": module_name, "error": error})
            print_status(f"[{i+1}/{total}] {module_name} — ОШИБКА: {error}", "ERROR")
    
    print_separator()
    print_status(f"📊 ЗАГРУЖЕНО: {len(loaded)}/{total}", "BOLD")
    
    if failed:
        print_status(f"❌ НЕ ЗАГРУЖЕНО: {len(failed)}", "ERROR")
        for f in failed[:10]:
            print_status(f"   • {f['name']}: {f['error'][:80]}", "ERROR")
        if len(failed) > 10:
            print_status(f"   ... и ещё {len(failed) - 10} модулей", "ERROR")
    
    print_separator()
    return loaded, failed