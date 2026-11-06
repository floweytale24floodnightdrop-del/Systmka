"""Главный регулятор импортов — объединяет import_core и import_modules"""

import os
import sys
import importlib
import json
import shutil
from datetime import datetime

# ============================================================
# 0. ОБЁРТКА UTF-8 УБРАНА
# ============================================================
# ВАЖНО: обёртка sys.stdout должна быть ТОЛЬКО в auto_start.py
# (или в bot.py, если он запускается отдельно).
#
# Если обернуть sys.stdout второй раз — старая обёртка закрывается
# автоматически, вместе с buffer, и любой print() падает с
# ValueError: I/O operation on closed file.
#
# Поэтому здесь НЕТ обёртки. auto_start.py уже её сделал.

# ============================================================
# 1. АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ ПАПОК В PYTHONPATH
# ============================================================

FOLDERS = [
    "handlers",
    "configs",
    "games",
    "media",
    "network",
    "ai",
    "utils",
    "security",
    "consciousness",
    "osint",
    "voice",
    "system",
    "premium",
    "rp",
]

_added_folders = []

for folder in FOLDERS:
    if os.path.exists(folder) and os.path.isdir(folder):
        folder_path = os.path.abspath(folder)
        if folder_path not in sys.path:
            sys.path.insert(0, folder_path)
            _added_folders.append(folder)

if _added_folders:
    print(f"📁 Добавлено папок в PYTHONPATH: {len(_added_folders)}")
    print(f"   {', '.join(_added_folders)}")

# ============================================================
# 2. ЗАГРУЗКА ЯДРА И МОДУЛЕЙ
# ============================================================

print("📦 Загрузка auto_import...")

try:
    import import_core
    print("✅ import_core загружен")
except Exception as e:
    print(f"❌ Ошибка загрузки import_core: {e}")

try:
    import import_modules
    print("✅ import_modules загружен")
except Exception as e:
    print(f"❌ Ошибка загрузки import_modules: {e}")

# ============================================================
# 3. ПРОВЕРКА ЗАГРУЗКИ (ПО МОДУЛЯМ, А НЕ ПО ПЕРЕМЕННЫМ!)
# ============================================================

def verify_modules():
    """
    Проверить, что критические МОДУЛИ загружены.
    
    ВАЖНО: проверяем только МОДУЛИ (sys.modules),
    а не переменные внутри них.
    
    Returns:
        dict: {loaded: [...], missing: [...]}
    """
    critical_modules = [
        "config",
        "config_network",
        "database",
        "system_prompt",
        "import_core",
        "import_modules",
    ]
    
    loaded = []
    missing = []
    
    for module_name in critical_modules:
        if module_name in sys.modules:
            loaded.append(module_name)
        else:
            missing.append(module_name)
    
    return {
        "loaded": loaded,
        "missing": missing,
        "all_ok": len(missing) == 0,
    }

# ============================================================
# 4. УПРАВЛЕНИЕ ПАПКАМИ (БЕЗОПАСНАЯ ВЕРСИЯ)
# ============================================================

class FolderManager:
    """
    Управление структурой папок.
    
    ВАЖНО: перемещение файлов ТОЛЬКО после подтверждения.
    Автоматически НИЧЕГО не перемещает.
    """
    
    def __init__(self):
        self.folder_structure = {}
        self.pending_moves = []
        self.approved = False
        self.folder_suggestions = []
    
    def suggest_folders(self):
        """Предложить структуру папок (только для справки)"""
        suggestions = {
            "core": [
                "bot.py", "config.py", "config_network.py",
                "database.py", "auto_import.py", "system_prompt.py",
                "import_core.py", "import_modules.py",
            ],
            "handlers": ["handlers_*.py"],
            "ai": ["ai_*.py"],
            "games": ["games.py", "game_*.py", "battle.py", "trojan_game.py"],
            "consciousness": [
                "consciousness.py", "emotions.py", "desires.py",
                "personality*.py", "fatigue.py", "sleep.py", "dreams.py",
                "attachments.py", "opinions.py", "self_reflection.py",
                "impression_*.py",
            ],
            "osint": ["osint_*.py", "dox_database.py"],
            "voice": ["voice*.py", "utils_media.py"],
            "system": [
                "system_*.py", "app_controller.py",
                "bot_monitor.py", "terminal_chat.py",
            ],
            "utils": [
                "error_*.py", "trash.py", "log_manager.py",
                "debug_changes.py", "file_*.py",
                "self_learning.py", "learning_*.py",
                "message_*.py", "moderation.py", "security.py",
                "progress.py", "commands.py", "messages.py",
                "profile.py", "reactions.py", "stickers_custom.py",
                "memes.py", "response_cache.py",
            ],
            "premium": ["premium.py"],
            "rp": ["roleplay.py", "rp_commands.py"],
            "media": ["generation.py", "music*.py", "creativity.py", "holidays.py"],
            "data": [
                "*.json", "personality_notes/", "prompt_notes/",
                "trash/", "error_backups/", "debug_logs/",
            ],
        }
        return suggestions
    
    def ask_permission(self, suggestion):
        """
        Спросить разрешение на создание папок.
        
        Возвращает False, если stdin недоступен или ответ отрицательный.
        """
        print("\n" + "=" * 70)
        print("📁 СИСТМКА ПРЕДЛАГАЕТ ОРГАНИЗОВАТЬ ФАЙЛЫ ПО ПАПКАМ:")
        print("=" * 70)
        
        for folder, files in suggestion.items():
            print(f"\n📂 {folder}/")
            for f in files[:5]:
                print(f"   • {f}")
            if len(files) > 5:
                print(f"   ... и ещё {len(files) - 5} файлов")
        
        print("\n" + "=" * 70)
        print("⚠️ ВНИМАНИЕ: перемещение файлов может СЛОМАТЬ проект!")
        print("   Рекомендуется: НЕТ")
        print("=" * 70)
        print("🔄 Создать папки и переместить файлы? (да/нет)")
        
        try:
            response = input("> ").strip().lower()
            return response in ("да", "yes", "y", "д")
        except (EOFError, KeyboardInterrupt):
            return False
        except Exception:
            return False
    
    def organize(self, force=False):
        """
        Полный цикл организации.
        
        Args:
            force: если True — не спрашивать (для тестов)
        
        Returns:
            dict или None
        """
        # БЕЗОПАСНО: по умолчанию ничего не делаем
        if not force:
            print("⏭ Организация файлов отключена (безопасный режим)")
            print("   💡 Для ручной организации используй force=True")
            return None
        
        suggestion = self.suggest_folders()
        
        if not self.ask_permission(suggestion):
            print("❌ Организация отменена пользователем")
            return None
        
        # Здесь был бы код перемещения — но мы его НЕ запускаем автоматически
        print("⚠️ Автоматическая организация отключена даже с force=True")
        print("   💡 Перемещай файлы вручную — это безопаснее")
        return None
    
    def get_structure(self):
        """Получить текущую структуру папок"""
        structure = {}
        
        try:
            for item in os.listdir("."):
                if os.path.isdir(item) and item not in (
                    "__pycache__", ".git", ".venv", "venv", "env",
                    "trash", "personality_notes", "prompt_notes",
                    "error_backups", "error_guardian_backups", "debug_logs",
                    "auto_improve_backups", "temp_music", "voice_clones",
                ):
                    if os.path.exists(os.path.join(item, "__init__.py")):
                        py_files = [
                            f for f in os.listdir(item)
                            if f.endswith(".py")
                        ]
                        structure[item] = len(py_files)
        except Exception:
            pass
        
        return structure
    
    def format_structure(self):
        """Форматировать текущую структуру"""
        structure = self.get_structure()
        
        if not structure:
            return "📁 Папки не организованы (все файлы в корне)"
        
        lines = ["📁 ТЕКУЩАЯ СТРУКТУРА:"]
        for folder, count in sorted(structure.items()):
            lines.append(f"  📂 {folder}/ — {count} .py файлов")
        
        return "\n".join(lines)


# ============================================================
# 5. ЭКСПОРТ ЯДРА
# ============================================================

# Ре-экспорт критических переменных из import_core
try:
    from import_core import (
        TELEGRAM_TOKEN,
        OWNER_IDS,
        HELPER_IDS,
        OPENROUTER_KEY,
        OPENROUTER_KEYS,
        OPENROUTER_EMAILS,
        GEMINI_KEY,
        HUGGINGFACE_KEY,
        SYSTEM_PROMPT,
        db,
        check_internet,
        is_online,
        cache_get,
        cache_set,
        safe_request,
        safe_get,
        safe_post,
        init_trash,
        clean_logs_now,
        backup_file,
        backup_file_before_change,
        get_trash_list,
        get_trash_stats,
        format_trash_stats,
        clear_trash,
        safe_change_file,
        validate_file,
        auto_fix_all,
        load_error_history,
        save_error_history,
        watchdog_loop,
        fix_error_in_file,
        find_all_errors,
        find_runtime_errors_from_logs,
        get_fix_stats,
        format_fix_stats,
        analyze_error,
        suggest_fix,
        find_error_location,
        notify_error,
        load_notifications,
        save_notifications,
        get_error_stats,
        ALL_STICKERS,
        moscow_tz,
    )
    print("✅ Критические переменные импортированы из import_core")
except ImportError as e:
    print(f"⚠️ Не удалось импортировать из import_core: {e}")

# ============================================================
# 6. СОЗДАНИЕ FolderManager
# ============================================================

folder_manager = FolderManager()

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("📦 auto_import загружен")

result = verify_modules()
if result["all_ok"]:
    print(f"✅ Все критические модули загружены ({len(result['loaded'])})")
else:
    print(f"⚠️ Отсутствуют модули: {result['missing']}")

print(f"📁 Текущая структура: {folder_manager.format_structure()}")