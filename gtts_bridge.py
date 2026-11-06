"""Мост между Систмкой и venv_gtts — генерация голоса через gTTS в отдельном окружении"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

# Путь к Python из venv_gtts
VENV_GTTSS_PYTHON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "venv_gtts",
    "Scripts",
    "python.exe",
)

# Fallback для Linux/Mac (если понадобится)
if not os.path.exists(VENV_GTTSS_PYTHON):
    VENV_GTTSS_PYTHON = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "venv_gtts",
        "bin",
        "python",
    )

# Таймаут генерации (секунды)
GENERATION_TIMEOUT = 30

# ============================================================
# 2. ПРОВЕРКА ДОСТУПНОСТИ
# ============================================================

def is_gtts_available():
    """
    Проверить, доступен ли gTTS через venv_gtts.
    
    Returns:
        bool
    """
    if not os.path.exists(VENV_GTTSS_PYTHON):
        return False
    
    try:
        result = subprocess.run(
            [VENV_GTTSS_PYTHON, "-c", "from gtts import gTTS; print('OK')"],
            capture_output=True,
            timeout=10,
            encoding="utf-8",
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False

# ============================================================
# 3. ГЕНЕРАЦИЯ ГОЛОСА
# ============================================================

def generate_gtts_voice(text, lang="ru", slow=False):
    """
    Сгенерировать голос через gTTS в venv_gtts.
    
    Args:
        text: текст для озвучки
        lang: язык (по умолчанию "ru")
        slow: медленная речь
    
    Returns:
        bytes (MP3) или None
    """
    if not text:
        return None
    
    if not os.path.exists(VENV_GTTSS_PYTHON):
        print(f"⚠️ venv_gtts не найден: {VENV_GTTSS_PYTHON}")
        return None
    
    # Временный файл для MP3
    temp_dir = tempfile.gettempdir()
    temp_mp3 = os.path.join(
        temp_dir,
        f"gtts_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.mp3"
    )
    
    # Скрипт для venv_gtts
    # ВАЖНО: используем repr() для безопасной передачи текста
    script = f"""
import sys
try:
    from gtts import gTTS
    tts = gTTS({repr(text)}, lang={repr(lang)}, slow={slow})
    tts.save({repr(temp_mp3)})
    print('OK')
except Exception as e:
    print(f'ERROR: {{e}}', file=sys.stderr)
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [VENV_GTTSS_PYTHON, "-c", script],
            capture_output=True,
            timeout=GENERATION_TIMEOUT,
            encoding="utf-8",
        )
        
        if result.returncode != 0:
            print(f"⚠️ gTTS ошибка: {result.stderr[:200]}")
            return None
        
        if not os.path.exists(temp_mp3):
            print(f"⚠️ gTTS не создал файл: {temp_mp3}")
            return None
        
        # Читаем MP3
        with open(temp_mp3, "rb") as f:
            audio_data = f.read()
        
        # Удаляем временный файл
        try:
            os.remove(temp_mp3)
        except Exception:
            pass
        
        if len(audio_data) < 1000:
            print(f"⚠️ gTTS вернул слишком маленький файл: {len(audio_data)} байт")
            return None
        
        return audio_data
    
    except subprocess.TimeoutExpired:
        print(f"⚠️ gTTS таймаут ({GENERATION_TIMEOUT}с)")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка gTTS: {e}")
        return None

# ============================================================
# 4. ТЕСТ
# ============================================================

def test_gtts_bridge():
    """Тест моста"""
    print("🧪 Тест gtts_bridge...")
    
    print(f"📁 venv_gtts Python: {VENV_GTTSS_PYTHON}")
    print(f"✅ Файл существует: {os.path.exists(VENV_GTTSS_PYTHON)}")
    
    available = is_gtts_available()
    print(f"✅ gTTS доступен: {available}")
    
    if not available:
        print("❌ gTTS недоступен — проверь venv_gtts")
        return False
    
    print("🎤 Генерирую 'привет мир'...")
    audio = generate_gtts_voice("привет мир")
    
    if audio:
        print(f"✅ Сгенерировано: {len(audio)} байт")
        return True
    else:
        print("❌ Не удалось сгенерировать")
        return False

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("🌉 gtts_bridge загружен")

if os.path.exists(VENV_GTTSS_PYTHON):
    if is_gtts_available():
        print("✅ gTTS через venv_gtts: доступен")
    else:
        print("⚠️ venv_gtts найден, но gTTS не работает")
else:
    print(f"⚠️ venv_gtts не найден: {VENV_GTTSS_PYTHON}")
    print("   💡 Создай: py -3.14 -m venv venv_gtts")
    print("   💡 Установи: venv_gtts\\Scripts\\pip.exe install gtts \"click<8.2\"")