"""Клонирование голосов для Систмки — PC-версия"""

import os
import io
import json
import time
import asyncio
import tempfile
import threading
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

VOICE_CLONES_DIR = os.path.join(tempfile.gettempdir(), "systmka_voice_clones")
MAX_CLONES = 50
MAX_CLONE_SIZE_MB = 20

os.makedirs(VOICE_CLONES_DIR, exist_ok=True)

# ============================================================
# 2. ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================================

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge_tts не установлен — синтез речи недоступен")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️ gTTS не установлен — резервный синтез недоступен")

# ============================================================
# 3. СОХРАНЕНИЕ КЛОНА
# ============================================================

def save_voice_clone(audio_data, name=None):
    """
    Сохранить клон голоса.
    
    Args:
        audio_data: bytes аудио
        name: имя клона
    
    Returns:
        str или None: ID клона
    """
    if not audio_data:
        print("⚠️ Нет аудиоданных для сохранения")
        return None
    
    # Проверяем размер
    size_mb = len(audio_data) / (1024 * 1024)
    if size_mb > MAX_CLONE_SIZE_MB:
        print(f"⚠️ Аудио слишком большое: {size_mb:.1f}MB")
        return None
    
    if len(audio_data) < 1000:
        print(f"⚠️ Аудио слишком маленькое: {len(audio_data)} байт")
        return None
    
    # Проверяем количество клонов
    clones = get_voice_clones()
    if len(clones) >= MAX_CLONES:
        # Удаляем самый старый
        oldest = min(clones, key=lambda x: x.get("created", ""))
        delete_voice_clone(oldest.get("id", ""))
    
    voice_id = f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000}"
    voice_file = os.path.join(VOICE_CLONES_DIR, f"{voice_id}.mp3")
    
    try:
        with open(voice_file, "wb") as f:
            f.write(audio_data)
        
        if not os.path.exists(voice_file):
            print(f"⚠️ Файл не создан: {voice_file}")
            return None
        
        actual_size = os.path.getsize(voice_file)
        if actual_size < 1000:
            print(f"⚠️ Файл слишком маленький: {actual_size} байт")
            try:
                os.remove(voice_file)
            except Exception:
                pass
            return None
    except Exception as e:
        print(f"❌ Ошибка сохранения аудио: {e}")
        return None
    
    profile = {
        "id": voice_id,
        "name": name or "Клон",
        "created": datetime.now().isoformat(),
        "file": voice_file,
        "size": actual_size,
        "settings": {
            "pitch": "+5%",
            "rate": "+5%",
            "volume": "+5%",
        },
    }
    
    profile_file = os.path.join(VOICE_CLONES_DIR, f"{voice_id}.json")
    try:
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения профиля: {e}")
        try:
            os.remove(voice_file)
        except Exception:
            pass
        return None
    
    return voice_id

# ============================================================
# 4. ПОЛУЧЕНИЕ СПИСКА КЛОНОВ
# ============================================================

def get_voice_clones():
    """
    Получить список клонов голосов.
    
    Returns:
        list: список профилей
    """
    clones = []
    
    if not os.path.exists(VOICE_CLONES_DIR):
        return clones
    
    for file in os.listdir(VOICE_CLONES_DIR):
        if not file.endswith(".json"):
            continue
        
        file_path = os.path.join(VOICE_CLONES_DIR, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            
            if not isinstance(profile, dict):
                continue
            
            # Проверяем существование аудио
            audio_file = profile.get("file")
            if audio_file and os.path.exists(audio_file):
                clones.append(profile)
            else:
                # Удаляем битый профиль
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        except json.JSONDecodeError:
            # Битый JSON — удаляем
            try:
                os.remove(file_path)
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ Ошибка загрузки профиля {file}: {e}")
    
    return sorted(clones, key=lambda x: x.get("created", ""), reverse=True)

# ============================================================
# 5. ПОЛУЧЕНИЕ КОНКРЕТНОГО КЛОНА
# ============================================================

def get_voice_clone(voice_id):
    """Получить конкретный клон по ID"""
    if not voice_id:
        return None
    
    profile_file = os.path.join(VOICE_CLONES_DIR, f"{voice_id}.json")
    
    if not os.path.exists(profile_file):
        return None
    
    try:
        with open(profile_file, "r", encoding="utf-8") as f:
            profile = json.load(f)
        
        if not isinstance(profile, dict):
            return None
        
        audio_file = profile.get("file")
        if audio_file and os.path.exists(audio_file):
            return profile
        
        # Битый профиль — удаляем
        try:
            os.remove(profile_file)
        except Exception:
            pass
    except json.JSONDecodeError:
        try:
            os.remove(profile_file)
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ Ошибка получения клона: {e}")
    
    return None

# ============================================================
# 6. УДАЛЕНИЕ КЛОНА
# ============================================================

def delete_voice_clone(voice_id):
    """Удалить клон голоса"""
    if not voice_id:
        return False
    
    profile_file = os.path.join(VOICE_CLONES_DIR, f"{voice_id}.json")
    voice_file = os.path.join(VOICE_CLONES_DIR, f"{voice_id}.mp3")
    
    deleted = 0
    
    for path in (profile_file, voice_file):
        try:
            if os.path.exists(path):
                os.remove(path)
                deleted += 1
        except Exception as e:
            print(f"⚠️ Ошибка удаления {path}: {e}")
    
    return deleted > 0

# ============================================================
# 7. КЛОНИРОВАНИЕ
# ============================================================

def clone_voice(audio_data, text=None, target_voice_name=None):
    """
    Скопировать голос из аудио.
    
    Returns:
        str или None: ID клона
    """
    return save_voice_clone(audio_data, target_voice_name)

# ============================================================
# 8. ГЕНЕРАЦИЯ ГОЛОСОМ КЛОНА
# ============================================================

def _run_async_safe(coro):
    """
    Безопасно запустить async-корутину.
    
    Работает и в главном потоке, и в потоке с активным event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Уже есть loop — запускаем в отдельном потоке
            result = [None]
            exception = [None]
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(coro)
                    result[0] = True
                except Exception as e:
                    exception[0] = e
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join(timeout=60)
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        else:
            loop.run_until_complete(coro)
            return True
    except RuntimeError:
        # Нет event loop в текущем потоке
        asyncio.run(coro)
        return True


def generate_with_cloned_voice(voice_id, text, output_file=None):
    """
    Сгенерировать речь скопированным голосом.
    
    Пока использует голос Систмки (edge_tts) с характером клона.
    
    Args:
        voice_id: ID клона
        text: текст для озвучки
        output_file: путь для сохранения (если None — временный)
    
    Returns:
        bytes или None: MP3-данные
    """
    if not voice_id or not text:
        return None
    
    profile = get_voice_clone(voice_id)
    if not profile:
        print(f"⚠️ Клон {voice_id} не найден")
        return None
    
    if output_file is None:
        output_file = os.path.join(
            tempfile.gettempdir(),
            f"systmka_clone_{int(time.time() * 1000)}.mp3"
        )
    
    # === Способ 1: edge_tts ===
    if EDGE_TTS_AVAILABLE:
        try:
            clone_name = profile.get("name", "Клон")
            settings = profile.get("settings", {})
            
            character_text = f"Говори как {clone_name}. {text}"
            
            async def generate():
                communicate = edge_tts.Communicate(
                    character_text,
                    "ru-RU-SvetlanaNeural",
                    rate=settings.get("rate", "+5%"),
                    pitch=settings.get("pitch", "+3%"),
                    volume=settings.get("volume", "+5%"),
                )
                await communicate.save(output_file)
            
            _run_async_safe(generate())
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                with open(output_file, "rb") as f:
                    data = f.read()
                
                try:
                    os.remove(output_file)
                except Exception:
                    pass
                
                return data
        except Exception as e:
            print(f"⚠️ Ошибка edge_tts: {e}")
    
    # === Способ 2: gTTS ===
    if GTTS_AVAILABLE:
        try:
            tts = gTTS(text=text, lang='ru', slow=False)
            
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.read()
        except Exception as e:
            print(f"⚠️ Ошибка gTTS: {e}")
    
    return None

# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_clones_stats():
    """Получить статистику клонов"""
    clones = get_voice_clones()
    
    total_size = 0
    for clone in clones:
        size = clone.get("size", 0)
        if not size:
            audio_file = clone.get("file")
            if audio_file and os.path.exists(audio_file):
                try:
                    size = os.path.getsize(audio_file)
                except Exception:
                    pass
        total_size += size
    
    return {
        "total": len(clones),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "max_clones": MAX_CLONES,
        "names": [c.get("name", "Без имени") for c in clones[:10]],
    }


def format_clones_stats():
    """Форматировать статистику клонов"""
    stats = get_clones_stats()
    
    lines = [
        "🎤 СТАТИСТИКА КЛОНОВ:",
        f"📁 Всего: {stats['total']} / {stats['max_clones']}",
        f"💾 Размер: {stats['total_size_mb']}MB",
    ]
    
    if stats['names']:
        lines.append("📋 Имена:")
        for name in stats['names']:
            lines.append(f"  • {name}")
    
    return "\n".join(lines)

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

clones = get_voice_clones()

print("🎤 Модуль клонирования голосов загружен (PC)")
print(f"📁 Папка: {VOICE_CLONES_DIR}")
print(f"📦 edge_tts: {'✅' if EDGE_TTS_AVAILABLE else '❌'}")
print(f"📦 gTTS: {'✅' if GTTS_AVAILABLE else '❌'}")
print(f"📂 Клонов: {len(clones)} / {MAX_CLONES}")

if clones:
    total_size = sum(c.get("size", 0) for c in clones)
    print(f"💾 Общий размер: {round(total_size / (1024 * 1024), 2)}MB")