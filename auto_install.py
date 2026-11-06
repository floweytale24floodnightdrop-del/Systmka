"""Автоматическая установка недостающих пакетов — PC-версия"""

import os
import sys
import importlib
import subprocess
import platform
from datetime import datetime

# ============================================================
# 1. КАРТА ПАКЕТОВ (pip-имя → import-имя)
# ============================================================

# pip-имя : import-имя
PACKAGES_MAP = {
    # === Telegram ===
    "pyTelegramBotAPI": "telebot",
    
    # === Сеть ===
    "requests": "requests",
    "dnspython": "dns",
    
    # === Картинки и OCR ===
    "opencv-python": "cv2",
    "numpy": "numpy",
    "pytesseract": "pytesseract",
    
    # === Голос ===
    "edge-tts": "edge_tts",
    "gTTS": "gtts",
    "pydub": "pydub",
    "SpeechRecognition": "speech_recognition",
    "sounddevice": "sounddevice",
    
    # === Управление ПК ===
    "pynput": "pynput",
    "psutil": "psutil",
    
    # === OSINT ===
    "phonenumbers": "phonenumbers",
    "maigret": "maigret",
    
    # === Веб ===
    "trafilatura": "trafilatura",
    "duckduckgo-search": "duckduckgo_search",
    
    # === Скорость интернета ===
    "speedtest-cli": "speedtest",
    "internetspeedtest": "internetspeedtest",
    "pythonping": "pythonping",
    
    # === Погода ===
    "openmeteo-requests": "openmeteo_requests",
    
    # === ИИ / Стабильность ===
    "pydantic-ai": "pydantic_ai",
    "instructor": "instructor",
    "json-repair": "json_repair",
    "context-clipper": "context_clipper",
    
    # === Медиа ===
    "imageio[ffmpeg]": "imageio",
    "moviepy": "moviepy",
    
    # === Музыка ===
    "yt-dlp": "yt_dlp",
    
    # === Утилиты ===
    "pytz": "pytz",
    
    # === Память / LangChain ===
    "langmem": "langmem",
    "chromadb": "chromadb",
    "langchain": "langchain",
    "langchain-community": "langchain_community",
    
    # === Обучение с подкреплением (RL) ===
    "stable-baselines3": "stable_baselines3",
    "gymnasium": "gymnasium",
}

# ============================================================
# 2. АЛИАСЫ (старые названия → новые)
# ============================================================

# Если кто-то использует старое имя — переадресуем
PACKAGE_ALIASES = {
    "PIL": "opencv-python",
    "Pillow": "opencv-python",
    "dns": "dnspython",
    "speech_recognition": "SpeechRecognition",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
}

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _normalize_package_name(package_name):
    """Привести имя пакета к pip-имени"""
    if package_name in PACKAGE_ALIASES:
        return PACKAGE_ALIASES[package_name]
    return package_name

def _get_import_name(pip_name):
    """Получить import-имя для pip-пакета"""
    if pip_name in PACKAGES_MAP:
        return PACKAGES_MAP[pip_name]
    # Fallback: заменяем дефисы на подчёркивания
    return pip_name.replace("-", "_").split("[")[0]

# ============================================================
# 4. ПРОВЕРКА ПАКЕТА
# ============================================================

def check_package(package_name):
    """
    Проверить, установлен ли пакет.
    
    Args:
        package_name: имя пакета (pip или import)
    
    Returns:
        bool
    """
    import_name = _get_import_name(package_name)
    
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False
    except Exception:
        return False

def check_all_packages():
    """
    Проверить все пакеты.
    
    Returns:
        dict: {pip_name: installed}
    """
    results = {}
    for pip_name in PACKAGES_MAP:
        results[pip_name] = check_package(pip_name)
    return results

def get_missing_packages():
    """
    Получить список отсутствующих пакетов.
    
    Returns:
        list: список pip-имён
    """
    missing = []
    for pip_name, import_name in PACKAGES_MAP.items():
        if not check_package(pip_name):
            missing.append(pip_name)
    return missing

# ============================================================
# 5. УСТАНОВКА ПАКЕТА
# ============================================================

def install_package(package_name):
    """
    Установить пакет через pip.
    
    Args:
        package_name: pip-имя пакета
    
    Returns:
        bool: успех
    """
    pip_name = _normalize_package_name(package_name)
    
    try:
        print(f"📦 Устанавливаю: {pip_name}...")
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name],
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="ignore"
        )
        
        if result.returncode == 0:
            print(f"✅ {pip_name} установлен")
            return True
        else:
            print(f"❌ {pip_name} не установлен:")
            if result.stderr:
                print(f"   {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {pip_name} — таймаут установки")
        return False
    except Exception as e:
        print(f"❌ Ошибка установки {pip_name}: {e}")
        return False

def auto_install_all():
    """
    Установить все отсутствующие пакеты.
    
    Returns:
        dict: {installed, failed, skipped}
    """
    results = {
        "installed": [],
        "failed": [],
        "skipped": [],
    }
    
    missing = get_missing_packages()
    
    if not missing:
        print("✅ Все пакеты установлены")
        return results
    
    print(f"📦 Отсутствует пакетов: {len(missing)}")
    
    for pip_name in missing:
        if install_package(pip_name):
            results["installed"].append(pip_name)
        else:
            results["failed"].append(pip_name)
    
    return results

# ============================================================
# 6. ВЕРИФИКАЦИЯ
# ============================================================

def verify_installation():
    """
    Проверить, что все пакеты установлены.
    
    Returns:
        dict: {pip_name: installed}
    """
    results = {}
    for pip_name in PACKAGES_MAP:
        results[pip_name] = check_package(pip_name)
    return results

def format_verification():
    """Форматировать результаты проверки"""
    results = verify_installation()
    
    installed = [p for p, v in results.items() if v]
    missing = [p for p, v in results.items() if not v]
    
    lines = [
        "📦 ПРОВЕРКА ПАКЕТОВ:",
        f"  ✅ Установлено: {len(installed)}/{len(results)}",
    ]
    
    if missing:
        lines.append("")
        lines.append(f"❌ Отсутствуют ({len(missing)}):")
        for pkg in missing:
            lines.append(f"  • {pkg}")
    else:
        lines.append("")
        lines.append("✅ Все пакеты на месте")
    
    return "\n".join(lines)

def format_detailed_verification():
    """Подробный отчёт — по каждому пакету"""
    results = verify_installation()
    
    lines = ["📦 ДЕТАЛЬНАЯ ПРОВЕРКА:"]
    
    for pip_name, installed in sorted(results.items()):
        icon = "✅" if installed else "❌"
        import_name = _get_import_name(pip_name)
        lines.append(f"  {icon} {pip_name} (import: {import_name})")
    
    return "\n".join(lines)

# ============================================================
# 7. РЕКОМЕНДАЦИИ ПО УСТАНОВКЕ
# ============================================================

def get_install_command():
    """
    Получить команду для установки всех отсутствующих пакетов.
    
    Returns:
        str: команда pip install
    """
    missing = get_missing_packages()
    
    if not missing:
        return "✅ Все пакеты установлены"
    
    packages_str = " ".join(missing)
    return f"pip install --progress-bar raw {packages_str}"

def format_install_help():
    """Форматировать инструкцию по установке"""
    missing = get_missing_packages()
    
    lines = ["📋 ИНСТРУКЦИЯ ПО УСТАНОВКЕ:"]
    lines.append("")
    
    if not missing:
        lines.append("✅ Все пакеты установлены. Ничего делать не нужно.")
        return "\n".join(lines)
    
    lines.append(f"❌ Отсутствует {len(missing)} пакетов:")
    lines.append("")
    
    # Команда
    lines.append("🔧 Установи одной командой:")
    lines.append("")
    lines.append(f"  py -3.14 -m pip install --progress-bar raw {' '.join(missing)}")
    lines.append("")
    lines.append("💡 Или по одному:")
    for pkg in missing:
        lines.append(f"  pip install {pkg}")
    
    return "\n".join(lines)

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("📦 Модуль автоустановки загружен (PC)")
print(f"💻 Python: {platform.python_version()}")
print(f"📋 Пакетов в списке: {len(PACKAGES_MAP)}")

# Проверяем на старте (без установки — только отчёт)
_installed_count = sum(1 for pkg in PACKAGES_MAP if check_package(pkg))
_missing_count = len(PACKAGES_MAP) - _installed_count

if _missing_count == 0:
    print(f"✅ Все {len(PACKAGES_MAP)} пакетов установлены")
else:
    print(f"⚠️ Установлено: {_installed_count}/{len(PACKAGES_MAP)}")
    print(f"❌ Отсутствует: {_missing_count}")
    print(f"💡 Запусти: py -3.14 -c \"from auto_install import format_install_help; print(format_install_help())\"")