"""Менеджер модулей — БОЛЬШЕ НЕ ПЕРЕХВАТЫВАЕТ ИМПОРТ

ГЛАВНЫЙ перехватчик теперь error_guardian.py.
Этот модуль оставлен для:
- чтения/записи frozen_modules.json
- ручной разморозки модулей
- статуса

ВАЖНО: activate() НЕ вызывается — перехват делает error_guardian.
"""

import os
import sys
import json
import importlib
import time
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

FROZEN_MODULES_FILE = "frozen_modules.json"

# Модули, которые НЕ НУЖНЫ (тихо игнорируются)
IGNORED_MODULES = [
    # Android-модули (не нужны на PC)
    '_elementtree',
    '_wmi',
    '_uuid',
    'defusedxml',
    'cryptography',
    'ujson',
    'redis',
    'hiredis',
    'opentelemetry',
    'xxhash',
    'aiosignal',
    'StringIO',
    'backports',
    'brotlicffi',
    'pycares',
    # Оптимизации C-расширений
    '_quoting_c',
    '_helpers_c',
    '_frozenlist',
    'yarl._quoting_c',
    'propcache._helpers_c',
    'frozenlist._frozenlist',
    'redis.utils',
    'redis.client',
    'redis.connection',
    'redis.commands',
    'redis.asyncio',
    'redis.cluster',
    'redis.sentinel',
    'redis.event',
    'redis.observability',
    # Прочие встроенные (не критичные)
    '_sqlite3',
    '_ssl',
    'org.python',
]

# ============================================================
# 2. ДАННЫЕ
# ============================================================

frozen_modules = {
    "modules": [],
    "last_update": None,
    "checked_at": None,
    "unfrozen_at_startup": False,
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_frozen_modules():
    """Сохранить список замороженных модулей"""
    try:
        with open(FROZEN_MODULES_FILE, "w", encoding="utf-8") as f:
            json.dump(frozen_modules, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения замороженных модулей: {e}")
        return False


def load_frozen_modules():
    """Загрузить список замороженных модулей"""
    global frozen_modules
    try:
        if os.path.exists(FROZEN_MODULES_FILE):
            with open(FROZEN_MODULES_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
                if isinstance(loaded, dict):
                    frozen_modules.update(loaded)
                elif isinstance(loaded, list):
                    # Старый формат
                    frozen_modules["modules"] = loaded
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON frozen_modules: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки frozen_modules: {e}")
        return False


def is_ignored_module(module_name):
    """Проверить, является ли модуль игнорируемым"""
    for ignored in IGNORED_MODULES:
        if ignored in module_name:
            return True
    return False


# ============================================================
# 4. КЛАСС ДЛЯ УПРАВЛЕНИЯ МОДУЛЯМИ (БЕЗ ПЕРЕХВАТА!)
# ============================================================

class ModuleManager:
    """
    Менеджер модулей.
    
    ВАЖНО: НЕ перехватывает __import__.
    Всю работу с импортом делает error_guardian.py.
    """
    
    def __init__(self):
        self.frozen = []
        self.import_errors = []
        self.activated = False
        self.first_run = True
    
    def activate(self):
        """
        ЗАГЛУШКА — НЕ активирует перехват импорта.
        
        Перехват делает error_guardian.py.
        Здесь только загружаем список замороженных.
        """
        if self.activated:
            return True
        
        self.activated = True
        
        # Загружаем список замороженных
        load_frozen_modules()
        self.frozen = frozen_modules.get("modules", [])
        
        print(f"🔧 Менеджер модулей: перехват импорта отключён")
        print(f"   🛡️ Импорт перехватывает error_guardian.py")
        print(f"   ❄️ Заморожено модулей: {len(self.frozen)}")
        return True
    
    def check_and_unfreeze(self):
        """
        Проверить, исправились ли ошибки, и разморозить.
        
        Returns:
            list: размороженные модули
        """
        unfrozen = []
        
        for module_name in list(frozen_modules.get("modules", [])):
            try:
                importlib.import_module(module_name)
                unfrozen.append(module_name)
                print(f"✅ Модуль '{module_name}' разморожен")
            except:
                pass
        
        if unfrozen:
            for module in unfrozen:
                if module in frozen_modules["modules"]:
                    frozen_modules["modules"].remove(module)
            frozen_modules["last_update"] = datetime.now().isoformat()
            save_frozen_modules()
        
        return unfrozen
    
    def force_unfreeze(self, module_name):
        """Принудительно разморозить модуль"""
        if module_name in frozen_modules.get("modules", []):
            frozen_modules["modules"].remove(module_name)
            frozen_modules["last_update"] = datetime.now().isoformat()
            save_frozen_modules()
            return True
        return False
    
    def force_freeze(self, module_name):
        """Принудительно заморозить модуль"""
        if module_name not in frozen_modules.get("modules", []):
            frozen_modules["modules"].append(module_name)
            frozen_modules["last_update"] = datetime.now().isoformat()
            save_frozen_modules()
            return True
        return False
    
    def get_status(self):
        """Получить статус менеджера"""
        return {
            "frozen_modules": frozen_modules.get("modules", []),
            "total_frozen": len(frozen_modules.get("modules", [])),
            "import_errors": len(self.import_errors),
            "last_update": frozen_modules.get("last_update"),
            "checked_at": frozen_modules.get("checked_at"),
            "unfrozen_at_startup": frozen_modules.get("unfrozen_at_startup", False),
        }
    
    def format_status(self):
        """Форматировать статус для вывода"""
        status = self.get_status()
        lines = [
            "🔧 СТАТУС МЕНЕДЖЕРА МОДУЛЕЙ:",
            f"❄️ Заморожено модулей: {status['total_frozen']}",
            f"⚠️ Ошибок импорта: {status['import_errors']}",
            f"🔄 Разморозка при старте: {'✅' if status['unfrozen_at_startup'] else '❌'}",
        ]
        if status['frozen_modules']:
            preview = status['frozen_modules'][:10]
            lines.append(f"📦 Список: {', '.join(preview)}")
            if len(status['frozen_modules']) > 10:
                lines.append(f"   ... и ещё {len(status['frozen_modules']) - 10}")
        if status['last_update']:
            lines.append(f"🕐 Обновлено: {status['last_update'][:16]}")
        if status['checked_at']:
            lines.append(f"🕐 Проверено: {status['checked_at'][:16]}")
        return "\n".join(lines)


# ============================================================
# 5. СОЗДАНИЕ ЭКЗЕМПЛЯРА (БЕЗ АКТИВАЦИИ ПЕРЕХВАТА!)
# ============================================================

module_manager = ModuleManager()

# ВАЖНО: activate() теперь НЕ вызывает перехват импорта.
# Перехват делает error_guardian.py, который загружается РАНЬШЕ.
module_manager.activate()

# ============================================================
# 6. ЗАГРУЗКА
# ============================================================

load_frozen_modules()

print("🔧 Менеджер модулей загружен (перехват импорта — НЕ здесь)")
print(f"❄️ Заморожено модулей: {len(frozen_modules.get('modules', []))}")
print(f"📋 Игнорируемых модулей: {len(IGNORED_MODULES)}")

if frozen_modules.get("modules"):
    preview = frozen_modules['modules'][:10]
    print(f"📦 Замороженные: {', '.join(preview)}")
    if len(frozen_modules['modules']) > 10:
        print(f"   ... и ещё {len(frozen_modules['modules']) - 10}")