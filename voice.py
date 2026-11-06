"""Голос Систмки — уникальный, с характером, с проверкой зависимостей"""

import os
import re
import io
import json
import time
import asyncio
import random
import tempfile
import platform
import threading
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================================

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge_tts не установлен")

# gTTS через отдельное окружение venv_gtts
try:
    from gtts_bridge import (
        generate_gtts_voice as _gtts_generate,
        is_gtts_available as _gtts_available,
    )
    GTTS_AVAILABLE = _gtts_available()
    if not GTTS_AVAILABLE:
        print("⚠️ gTTS через venv_gtts недоступен")
except ImportError:
    GTTS_AVAILABLE = False
    _gtts_generate = None
    print("⚠️ gtts_bridge не найден")

try:
    from pydub import AudioSegment
    from pydub.effects import speedup, normalize
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub не установлен")

# ============================================================
# 3. ПУТИ
# ============================================================

TEMP_DIR = os.path.join(tempfile.gettempdir(), "systmka_voice")
os.makedirs(TEMP_DIR, exist_ok=True)

VOICE_FILE = os.path.join(TEMP_DIR, "systmka_voice.mp3")
VOICE_CLONES_DIR = os.path.join(TEMP_DIR, "systmka_voice_clones")
VOICE_SETTINGS_FILE = "voice_settings.json"

os.makedirs(VOICE_CLONES_DIR, exist_ok=True)

# ============================================================
# 4. ХАРАКТЕР ГОЛОСА
# ============================================================

DEFAULT_VOICE_PROFILE = {
    "pitch": "+12%",
    "rate": "+10%",
    "volume": "+5%",
    "voice": "ru-RU-SvetlanaNeural",
    "style": "conversational",
    "voice_character": "Дерзкий, игривый, уверенный, с хитринкой",
    "personality_traits": {
        "sass": 8,
        "playful": 9,
        "warmth": 6,
        "sarcasm": 7,
        "confidence": 9,
    },
}

SYSTMKA_VOICE_PROFILE = DEFAULT_VOICE_PROFILE.copy()

_voice_lock = threading.Lock()

# ============================================================
# 5. СОХРАНЕНИЕ/ЗАГРУЗКА НАСТРОЕК
# ============================================================

def save_voice_settings():
    """Сохранить настройки голоса"""
    try:
        with open(VOICE_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(SYSTMKA_VOICE_PROFILE, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения настроек голоса: {e}")
        return False


def load_voice_settings():
    """Загрузить настройки голоса"""
    global SYSTMKA_VOICE_PROFILE
    try:
        if os.path.exists(VOICE_SETTINGS_FILE):
            with open(VOICE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                for key in ("pitch", "rate", "volume", "voice", "style", "voice_character"):
                    if loaded.get(key):
                        SYSTMKA_VOICE_PROFILE[key] = loaded[key]
                
                if isinstance(loaded.get("personality_traits"), dict):
                    SYSTMKA_VOICE_PROFILE["personality_traits"].update(
                        loaded["personality_traits"]
                    )
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON настроек голоса: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки настроек голоса: {e}")
        return False


load_voice_settings()

# ============================================================
# 6. ОПРЕДЕЛЕНИЕ ЭМОЦИИ
# ============================================================

def detect_emotion(text):
    """Определить эмоцию из текста"""
    if not text:
        return "neutral"
    
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["ну и", "ага", "ясно", "конечно", "ахаха", "ха-ха"]):
        if any(w in text_lower for w in ["ну и", "ага", "конечно"]):
            return "sarcastic"
        return "sassy"
    
    if any(w in text_lower for w in ["😏", ";)", "хихи", "кавай", "мило", "игриво"]):
        return "playful"
    
    if any(w in text_lower for w in ["ура", "круто", "класс", "😊", "🔥", "супер"]):
        return "excited"
    
    if any(w in text_lower for w in ["блять", "сука", "злюсь", "бесит", "😡", "раздражает"]):
        return "angry"
    
    if any(w in text_lower for w in ["грустно", "жаль", "😭", "печаль", "💔", "обидно"]):
        return "sad"
    
    if any(w in text_lower for w in ["люблю", "обожаю", "💜", "душевно", "тепло", "спасибо"]):
        return "warm"
    
    return "neutral"

# ============================================================
# 7. ОЧИСТКА ТЕКСТА
# ============================================================

_EMOJI_PATTERN = re.compile(
    "["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F700-\U0001F77F"
    u"\U0001F780-\U0001F7FF"
    u"\U0001F800-\U0001F8FF"
    u"\U0001F900-\U0001F9FF"
    u"\U0001FA00-\U0001FA6F"
    u"\U0001FA70-\U0001FAFF"
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def clean_text_for_voice(text):
    """Очистить текст для озвучки"""
    if not text:
        return ""
    
    text = re.sub(r'\*[^*]+\*', '', text)
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = re.sub(r'\([^)]+\)', '', text)
    text = _EMOJI_PATTERN.sub('', text)
    
    replacements = {
        '💜': 'сердечко',
        '✨': 'звёздочка',
        '🔥': 'огонь',
        '🥺': 'умоляю',
        '🫶': 'люблю',
        '😊': 'улыбка',
        '💔': 'сердце разбито',
        '😭': 'плачу',
        '🥰': 'мило',
        '😏': 'хитро',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = ' '.join(text.split())
    return text.strip()

# ============================================================
# 8. НАСТРОЙКИ ЭМОЦИЙ
# ============================================================

EMOTION_SETTINGS = {
    "neutral": {"pitch": "+5%", "rate": "+8%", "volume": "+5%"},
    "sassy": {"pitch": "+15%", "rate": "+18%", "volume": "+8%"},
    "playful": {"pitch": "+20%", "rate": "+12%", "volume": "+6%"},
    "sarcastic": {"pitch": "+10%", "rate": "+5%", "volume": "+5%"},
    "warm": {"pitch": "+3%", "rate": "+5%", "volume": "+8%"},
    "angry": {"pitch": "-5%", "rate": "+25%", "volume": "+10%"},
    "sad": {"pitch": "-10%", "rate": "-15%", "volume": "+3%"},
    "excited": {"pitch": "+25%", "rate": "+30%", "volume": "+10%"},
}

# ============================================================
# 9. ГЕНЕРАЦИЯ ЧЕРЕЗ EDGE-TTS
# ============================================================

def _generate_edge_tts(text, settings, output_file=None):
    """Генерация через edge-tts"""
    if not EDGE_TTS_AVAILABLE:
        return None
    
    if output_file is None:
        output_file = os.path.join(TEMP_DIR, f"edge_{int(time.time() * 1000)}.mp3")
    
    try:
        voice = SYSTMKA_VOICE_PROFILE["voice"]
        
        async def generate():
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=settings["rate"],
                pitch=settings["pitch"],
                volume=settings["volume"],
            )
            await communicate.save(output_file)
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = [None]
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_loop.run_until_complete(generate())
                        result[0] = True
                    except Exception as e:
                        print(f"⚠️ Ошибка в потоке edge-tts: {e}")
                        result[0] = False
                    finally:
                        new_loop.close()
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join(timeout=60)
                
                if not result[0]:
                    return None
            else:
                loop.run_until_complete(generate())
        except RuntimeError:
            asyncio.run(generate())
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
            if PYDUB_AVAILABLE:
                try:
                    audio = AudioSegment.from_mp3(output_file)
                    audio = normalize(audio)
                    echo = audio - 10
                    audio = audio.overlay(echo, position=50)
                    audio.export(output_file, format="mp3")
                except Exception:
                    pass
            
            with open(output_file, "rb") as f:
                data = f.read()
            
            try:
                os.remove(output_file)
            except Exception:
                pass
            
            return data
    except Exception as e:
        print(f"⚠️ Ошибка edge-tts: {e}")
    
    return None

# ============================================================
# 10. ГЕНЕРАЦИЯ ЧЕРЕЗ GTTS (ЧЕРЕЗ VENV_GTTSS)
# ============================================================

def _generate_gtts(text, settings):
    """
    Генерация через gTTS (в отдельном venv_gtts).
    
    ИСПРАВЛЕНО: вместо прямого import gtts — используется gtts_bridge,
    который вызывает venv_gtts\Scripts\python.exe через subprocess.
    """
    if not GTTS_AVAILABLE or _gtts_generate is None:
        return None
    
    try:
        # Генерация через venv_gtts
        audio_data = _gtts_generate(text, lang='ru', slow=False)
        if not audio_data:
            return None
        
        # Обработка через pydub (если нужно)
        if PYDUB_AVAILABLE:
            try:
                audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
                
                # Ускорение
                try:
                    rate_str = settings.get("rate", "+0%").replace("%", "").replace("+", "")
                    speed_factor = 1.0 + (float(rate_str) / 100) / 2
                except ValueError:
                    speed_factor = 1.0
                
                modified = audio._spawn(
                    audio.raw_data,
                    overrides={"frame_rate": int(audio.frame_rate * speed_factor)},
                ).set_frame_rate(audio.frame_rate)
                
                # Пич
                try:
                    pitch_str = settings.get("pitch", "+0%").replace("%", "").replace("+", "")
                    pitch_factor = 1.0 + (float(pitch_str) / 100)
                except ValueError:
                    pitch_factor = 1.0
                
                pitched = modified._spawn(
                    modified.raw_data,
                    overrides={"frame_rate": int(modified.frame_rate * pitch_factor)},
                ).set_frame_rate(modified.frame_rate)
                
                pitched = normalize(pitched)
                
                # Эхо
                echo = pitched - 8
                final = pitched.overlay(echo, position=40)
                
                output_buffer = io.BytesIO()
                final.export(output_buffer, format="mp3")
                output_buffer.seek(0)
                return output_buffer.read()
            except Exception as e:
                print(f"⚠️ Ошибка pydub: {e}")
                return audio_data
        
        return audio_data
    except Exception as e:
        print(f"⚠️ Ошибка gTTS: {e}")
    
    return None

# ============================================================
# 11. ОСНОВНАЯ ГЕНЕРАЦИЯ
# ============================================================

def generate_systmka_voice(text, emotion=None):
    """Генерация голоса Систмки"""
    if not text:
        return None
    
    if not emotion:
        emotion = detect_emotion(text)
    
    settings = EMOTION_SETTINGS.get(emotion, EMOTION_SETTINGS["neutral"])
    
    clean_text = clean_text_for_voice(text)
    if not clean_text:
        return None
    
    character_prefix = "Говори с таким характером: дерзко, игриво, уверенно, с хитринкой. "
    full_text = character_prefix + clean_text
    
    # 1. Пробуем edge-tts
    if EDGE_TTS_AVAILABLE:
        result = _generate_edge_tts(full_text, settings)
        if result:
            return result
    
    # 2. Пробуем gTTS (через venv_gtts)
    if GTTS_AVAILABLE:
        result = _generate_gtts(clean_text, settings)
        if result:
            return result
    
    print("❌ Не удалось сгенерировать голос (нет доступных библиотек)")
    return None

# ============================================================
# 12. КЛОНИРОВАНИЕ ГОЛОСА
# ============================================================

def clone_voice_from_audio(audio_data, name=None):
    """Клонировать голос из аудио"""
    if not audio_data:
        return None
    
    clone_id = f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    clone_file = os.path.join(VOICE_CLONES_DIR, f"{clone_id}.mp3")
    clone_json = os.path.join(VOICE_CLONES_DIR, f"{clone_id}.json")
    
    try:
        with open(clone_file, 'wb') as f:
            f.write(audio_data)
        
        profile = {
            "id": clone_id,
            "name": name or "Клон",
            "created": datetime.now().isoformat(),
            "file": clone_file,
            "size": os.path.getsize(clone_file),
            "settings": {
                "pitch": "+5%",
                "rate": "+5%",
                "volume": "+5%",
            },
        }
        
        with open(clone_json, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        
        return clone_id
    except Exception as e:
        print(f"❌ Ошибка клонирования голоса: {e}")
        return None


def generate_with_cloned_voice(clone_id, text):
    """Сгенерировать речь клонированным голосом"""
    clone_json = os.path.join(VOICE_CLONES_DIR, f"{clone_id}.json")
    
    if not os.path.exists(clone_json):
        return None
    
    try:
        with open(clone_json, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        settings = profile.get("settings", {})
        
        with _voice_lock:
            original_pitch = SYSTMKA_VOICE_PROFILE.get("pitch", "+5%")
            original_rate = SYSTMKA_VOICE_PROFILE.get("rate", "+8%")
            
            try:
                SYSTMKA_VOICE_PROFILE["pitch"] = settings.get("pitch", original_pitch)
                SYSTMKA_VOICE_PROFILE["rate"] = settings.get("rate", original_rate)
                
                voice_data = generate_systmka_voice(text, "neutral")
            finally:
                SYSTMKA_VOICE_PROFILE["pitch"] = original_pitch
                SYSTMKA_VOICE_PROFILE["rate"] = original_rate
        
        return voice_data
    except Exception as e:
        print(f"❌ Ошибка генерации клонированным голосом: {e}")
        return None


def get_voice_clones():
    """Получить все клоны"""
    clones = []
    if not os.path.exists(VOICE_CLONES_DIR):
        return clones
    
    for f in os.listdir(VOICE_CLONES_DIR):
        if f.endswith('.json'):
            try:
                with open(os.path.join(VOICE_CLONES_DIR, f), 'r', encoding='utf-8') as file:
                    clones.append(json.load(file))
            except Exception:
                pass
    
    return sorted(clones, key=lambda x: x.get("created", ""), reverse=True)

# ============================================================
# 13. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def generate_voice(text, emotion=None, voice_type="systmka", clone_id=None):
    """Генерация голоса"""
    if not text:
        return None
    
    text = clean_text_for_voice(text)
    if not text:
        return None
    
    if voice_type == "systmka":
        return generate_systmka_voice(text, emotion)
    
    if voice_type == "clone" and clone_id:
        return generate_with_cloned_voice(clone_id, text)
    
    return generate_systmka_voice(text, emotion)

# ============================================================
# 14. КОМАНДЫ ДЛЯ БОТА
# ============================================================

def handle_voice_command(bot, message, text, emotion=None):
    """Обработка команды голоса"""
    voice_data = generate_voice(text, emotion)
    if voice_data:
        bot.send_voice(message.chat.id, voice_data)
        return True
    bot.reply_to(message, "❌ Не удалось сгенерировать голос (нет доступных библиотек)")
    return False


def handle_voice_clone_command(bot, message, audio_data, name=None):
    """Обработка команды клонирования"""
    clone_id = clone_voice_from_audio(audio_data, name)
    if clone_id:
        bot.reply_to(message, f"✅ Голос скопирован! ID: {clone_id}")
        return True
    bot.reply_to(message, "❌ Не удалось скопировать голос")
    return False

# ============================================================
# 15. ИНФОРМАЦИЯ
# ============================================================

def get_voice_info():
    """Получить информацию о голосе"""
    clones = get_voice_clones()
    
    return {
        "systmka_voice": "Активен" if (EDGE_TTS_AVAILABLE or GTTS_AVAILABLE) else "Недоступен",
        "voice_character": SYSTMKA_VOICE_PROFILE.get("voice_character", "разговорный"),
        "clones_count": len(clones),
        "clones": clones,
        "emotions": list(EMOTION_SETTINGS.keys()),
        "available": EDGE_TTS_AVAILABLE or GTTS_AVAILABLE,
        "settings": SYSTMKA_VOICE_PROFILE.copy(),
    }


def format_voice_info():
    """Форматировать информацию о голосе"""
    info = get_voice_info()
    
    lines = [
        "🎤 ИНФОРМАЦИЯ О ГОЛОСЕ:",
        f"Голос Систмки: {info['systmka_voice']}",
        f"Характер: {info['voice_character']}",
        f"Клонов голосов: {info['clones_count']}",
        "",
        "🎭 НАСТРОЙКИ ГОЛОСА:",
        f"  Высота: {info['settings'].get('pitch', '+5%')}",
        f"  Скорость: {info['settings'].get('rate', '+8%')}",
        f"  Громкость: {info['settings'].get('volume', '+5%')}",
        "",
        "😊 ЭМОЦИИ:",
    ]
    for emotion in info['emotions']:
        lines.append(f"  • {emotion}")
    
    if info['clones']:
        lines.append("\n📂 КЛОНЫ ГОЛОСОВ:")
        for clone in info['clones'][:5]:
            name = clone.get('name', 'Без имени')
            clone_id = clone.get('id', '?')
            lines.append(f"  • {name} (ID: {clone_id})")
    
    lines.append("")
    lines.append("📦 ДОСТУПНЫЕ БИБЛИОТЕКИ:")
    lines.append(f"  • edge_tts: {'✅' if EDGE_TTS_AVAILABLE else '❌'}")
    lines.append(f"  • gTTS (venv_gtts): {'✅' if GTTS_AVAILABLE else '❌'}")
    lines.append(f"  • pydub: {'✅' if PYDUB_AVAILABLE else '❌'}")
    
    if not info['available']:
        lines.append("\n⚠️ Голосовой модуль недоступен! Установи: pip install edge-tts pydub")
    
    return "\n".join(lines)

# ============================================================
# 16. ЗАГРУЗКА
# ============================================================

print("🎤 Голосовой модуль загружен (PC)")
print(f"🎭 Характер голоса: {SYSTMKA_VOICE_PROFILE.get('voice_character', 'разговорный')}")
print(f"📂 Клонов голосов: {len(get_voice_clones())}")
print(f"📦 edge_tts: {'✅' if EDGE_TTS_AVAILABLE else '❌'}")
print(f"📦 gTTS (venv_gtts): {'✅' if GTTS_AVAILABLE else '❌'}")
print(f"📦 pydub: {'✅' if PYDUB_AVAILABLE else '❌'}")
print(f"📁 Temp: {TEMP_DIR}")