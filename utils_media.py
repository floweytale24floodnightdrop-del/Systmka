"""Обработка медиа — анализ изображений, OCR, голос, видео"""

import os
import io
import re
import json
import base64
import tempfile
import subprocess
import requests
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ (С ЗАЩИТОЙ)
# ============================================================

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ opencv/numpy не установлены — анализ изображений недоступен")

try:
    import pytesseract
    # На Windows указываем путь к tesseract.exe
    import platform
    if platform.system() == "Windows":
        # Типичные пути установки
        for path in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️ pytesseract не установлен — OCR недоступен")

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️ SpeechRecognition не установлен — распознавание речи недоступно")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub не установлен — конвертация аудио недоступна")

# ============================================================
# 3. НАСТРОЙКИ
# ============================================================

TEMP_DIR = os.path.join(tempfile.gettempdir(), "systmka_media")
os.makedirs(TEMP_DIR, exist_ok=True)

VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct"

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 5. АНАЛИЗ ИЗОБРАЖЕНИЙ ЧЕРЕЗ ИИ
# ============================================================

def analyze_image_with_ai(image_data, question="Подробно опиши что на этой картинке"):
    """
    Анализ изображения через ИИ (vision-модель).
    
    Args:
        image_data: bytes изображения
        question: вопрос к ИИ
    
    Returns:
        str: описание
    """
    if not image_data:
        return "❌ Пустое изображение"
    
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        key = _get_openrouter_key()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"⚠️ Ошибка analyze_image_with_ai: {e}")
    
    return "Не удалось проанализировать"

# ============================================================
# 6. OCR — ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ ИЗОБРАЖЕНИЙ
# ============================================================

def extract_text_from_image(image_data):
    """
    Извлечь текст из изображения через Tesseract OCR.
    
    Args:
        image_data: bytes изображения
    
    Returns:
        str или None
    """
    if not PYTESSERACT_AVAILABLE or not CV2_AVAILABLE:
        return None
    
    if not image_data:
        return None
    
    try:
        # Декодируем через opencv
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        # Конвертируем BGR → RGB для Tesseract
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # OCR
        text = pytesseract.image_to_string(img_rgb, lang='rus+eng')
        
        if text and text.strip():
            return text.strip()
    except Exception as e:
        print(f"⚠️ Ошибка OCR: {e}")
    
    return None

def extract_text_advanced(image_data):
    """
    Улучшенный OCR — с предобработкой изображения.
    
    Returns:
        str или None
    """
    if not PYTESSERACT_AVAILABLE or not CV2_AVAILABLE:
        return None
    
    if not image_data:
        return None
    
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        # Предобработка: grayscale + порог
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR
        text = pytesseract.image_to_string(thresh, lang='rus+eng')
        
        if text and text.strip():
            return text.strip()
    except Exception as e:
        print(f"⚠️ Ошибка advanced OCR: {e}")
    
    return None

# ============================================================
# 7. ОБРАБОТКА ГОЛОСОВЫХ СООБЩЕНИЙ
# ============================================================

def transcribe_voice(voice_data, bot=None, file_id=None):
    """
    Распознать голосовое сообщение через SpeechRecognition.
    
    Args:
        voice_data: bytes аудио (если None — скачиваем через bot.get_file(file_id))
        bot: telebot instance
        file_id: file_id голосового
    
    Returns:
        str или None
    """
    if not SR_AVAILABLE:
        return None
    
    try:
        # Получаем данные
        if voice_data is None and bot and file_id:
            file_info = bot.get_file(file_id)
            voice_data = bot.download_file(file_info.file_path)
        
        if not voice_data:
            return None
        
        # Сохраняем OGG
        ogg_file = os.path.join(TEMP_DIR, "voice_input.ogg")
        with open(ogg_file, "wb") as f:
            f.write(voice_data)
        
        # Конвертируем в WAV
        wav_file = os.path.join(TEMP_DIR, "voice_input.wav")
        
        # Способ 1 — через pydub
        if PYDUB_AVAILABLE:
            try:
                audio = AudioSegment.from_ogg(ogg_file)
                audio.export(wav_file, format="wav")
            except Exception as e:
                print(f"⚠️ pydub ошибка: {e}")
                # Fallback — через ffmpeg
                _convert_via_ffmpeg(ogg_file, wav_file)
        else:
            # Fallback — через ffmpeg
            _convert_via_ffmpeg(ogg_file, wav_file)
        
        if not os.path.exists(wav_file):
            return None
        
        # Распознаём
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            
            # Удаляем временные файлы
            try:
                os.remove(ogg_file)
                os.remove(wav_file)
            except Exception:
                pass
            
            return text
    except Exception as e:
        print(f"⚠️ Ошибка transcribe_voice: {e}")
    
    return None

def _convert_via_ffmpeg(input_file, output_file):
    """Конвертация через ffmpeg (fallback)"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", input_file, "-y", output_file],
            timeout=60,
            capture_output=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️ ffmpeg не установлен")
        return False
    except Exception:
        return False

# ============================================================
# 8. АНАЛИЗ ВИДЕО
# ============================================================

def analyze_video(video_data, bot=None, file_id=None):
    """
    Анализ видео — извлекаем кадр и анализируем через ИИ.
    
    Returns:
        str или None
    """
    try:
        # Получаем данные
        if video_data is None and bot and file_id:
            file_info = bot.get_file(file_id)
            video_data = bot.download_file(file_info.file_path)
        
        if not video_data:
            return None
        
        # Сохраняем
        video_file = os.path.join(TEMP_DIR, "video_input.mp4")
        with open(video_file, "wb") as f:
            f.write(video_data)
        
        # Извлекаем кадр
        frame_file = os.path.join(TEMP_DIR, "video_frame.jpg")
        success = _extract_frame_ffmpeg(video_file, frame_file)
        
        if not success or not os.path.exists(frame_file):
            return None
        
        # Читаем кадр
        with open(frame_file, "rb") as f:
            frame_data = f.read()
        
        # Анализируем через ИИ
        analysis = analyze_image_with_ai(frame_data, "Что происходит в этом видео?")
        
        # Удаляем временные файлы
        try:
            os.remove(video_file)
            os.remove(frame_file)
        except Exception:
            pass
        
        return analysis
    except Exception as e:
        print(f"⚠️ Ошибка analyze_video: {e}")
    
    return None

def _extract_frame_ffmpeg(video_file, output_file, time_pos="0"):
    """Извлечь кадр из видео через ffmpeg"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", video_file, "-ss", time_pos, "-vframes", "1", "-y", output_file],
            timeout=30,
            capture_output=True
        )
        return result.returncode == 0 and os.path.exists(output_file)
    except FileNotFoundError:
        print("⚠️ ffmpeg не установлен")
        return False
    except Exception:
        return False

def _extract_frame_opencv(video_file, output_file, time_pos=0):
    """Извлечь кадр через opencv (fallback)"""
    if not CV2_AVAILABLE:
        return False
    
    try:
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            return False
        
        # Переходим к нужной позиции
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(time_pos * fps))
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            cv2.imwrite(output_file, frame)
            return True
    except Exception:
        pass
    
    return False

# ============================================================
# 9. АНАЛИЗ СТИКЕРОВ
# ============================================================

def analyze_sticker(bot, sticker_file_id):
    """
    Анализ стикера — конвертация webp в png + анализ через ИИ.
    
    Returns:
        str или None
    """
    try:
        # Скачиваем
        file_info = bot.get_file(sticker_file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        if not downloaded:
            return None
        
        # Конвертируем webp → png (если opencv доступен)
        if CV2_AVAILABLE:
            try:
                nparr = np.frombuffer(downloaded, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                
                if img is not None:
                    # Если есть альфа-канал — убираем
                    if len(img.shape) == 3 and img.shape[2] == 4:
                        # Заменяем прозрачный фон на белый
                        alpha = img[:, :, 3] / 255.0
                        for c in range(3):
                            img[:, :, c] = img[:, :, c] * alpha + 255 * (1 - alpha)
                        img = img[:, :, :3].astype(np.uint8)
                    
                    # Кодируем в PNG
                    success, buffer = cv2.imencode(".png", img)
                    if success:
                        downloaded = buffer.tobytes()
            except Exception as e:
                print(f"⚠️ Ошибка конвертации стикера: {e}")
        
        # Анализируем
        analysis = analyze_image_with_ai(downloaded, "Что на этом стикере?")
        return analysis
    except Exception as e:
        print(f"⚠️ Ошибка analyze_sticker: {e}")
    
    return None

# ============================================================
# 10. АНАЛИЗ GIF
# ============================================================

def analyze_gif(bot, file_id):
    """
    Анализ GIF — извлекаем первый кадр + анализ через ИИ.
    
    Returns:
        str или None
    """
    try:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        if not downloaded:
            return None
        
        # Сохраняем GIF
        gif_file = os.path.join(TEMP_DIR, "input.gif")
        with open(gif_file, "wb") as f:
            f.write(downloaded)
        
        frame_data = None
        
        # Способ 1 — через opencv
        if CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(gif_file)
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    success, buffer = cv2.imencode(".png", frame)
                    if success:
                        frame_data = buffer.tobytes()
            except Exception:
                pass
        
        # Способ 2 — через ffmpeg
        if frame_data is None:
            frame_file = os.path.join(TEMP_DIR, "gif_frame.png")
            if _extract_frame_ffmpeg(gif_file, frame_file):
                with open(frame_file, "rb") as f:
                    frame_data = f.read()
                try:
                    os.remove(frame_file)
                except Exception:
                    pass
        
        # Удаляем GIF
        try:
            os.remove(gif_file)
        except Exception:
            pass
        
        if frame_data is None:
            return None
        
        analysis = analyze_image_with_ai(frame_data, "Что на этой гифке?")
        return analysis
    except Exception as e:
        print(f"⚠️ Ошибка analyze_gif: {e}")
    
    return None

# ============================================================
# 11. КОНВЕРТАЦИЯ АУДИО
# ============================================================

def convert_audio(input_file, output_file, output_format="mp3"):
    """
    Конвертировать аудио через ffmpeg.
    
    Returns:
        bool: успех
    """
    # Способ 1 — ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", input_file, "-y", output_file],
            timeout=60,
            capture_output=True
        )
        if result.returncode == 0 and os.path.exists(output_file):
            return True
    except FileNotFoundError:
        print("⚠️ ffmpeg не установлен")
    except Exception:
        pass
    
    # Способ 2 — pydub
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format=output_format)
            return os.path.exists(output_file)
        except Exception as e:
            print(f"⚠️ pydub ошибка: {e}")
    
    return False

def get_audio_duration(file_path):
    """
    Получить длительность аудио в секундах.
    
    Returns:
        int: длительность
    """
    # Способ 1 — pydub
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            return int(len(audio) / 1000)
        except Exception:
            pass
    
    # Способ 2 — ffprobe
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return int(float(result.stdout.strip()))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    
    return 0

# ============================================================
# 12. СОЗДАНИЕ ВИДЕО
# ============================================================

def create_video_from_image(image_path, audio_path, output_path="output.mp4"):
    """
    Создать видео из картинки и аудио.
    
    Returns:
        bool: успех
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-loop", "1",
                "-i", image_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-y",
                output_path
            ],
            timeout=120,
            capture_output=True
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except FileNotFoundError:
        print("⚠️ ffmpeg не установлен")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка create_video: {e}")
        return False

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🎬 Модуль обработки медиа загружен")
print(f"📦 opencv: {'✅' if CV2_AVAILABLE else '❌'}")
print(f"📦 pytesseract: {'✅' if PYTESSERACT_AVAILABLE else '❌'}")
print(f"📦 SpeechRecognition: {'✅' if SR_AVAILABLE else '❌'}")
print(f"📦 pydub: {'✅' if PYDUB_AVAILABLE else '❌'}")
print(f"🔑 OpenRouter ключей: {len(OPENROUTER_KEYS)}")