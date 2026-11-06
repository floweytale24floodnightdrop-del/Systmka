"""Поиск музыки — PC-версия (yt-dlp + ffmpeg)"""

import os
import re
import json
import time
import random
import subprocess
import urllib.parse
import tempfile
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# 1. ИМПОРТЫ ИЗ CONFIG
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

MUSIC_CACHE_FILE = "music_cache.json"
TEMP_DIR = os.path.join(tempfile.gettempdir(), "systmka_music")
os.makedirs(TEMP_DIR, exist_ok=True)

# Время последнего запроса (для глитчей)
last_glitch_time = {}
GLITCH_INTERVAL = 30  # 30 секунд между начислением глитчей

music_cache = {}

# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

def _check_yt_dlp():
    """Проверить доступность yt-dlp"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False

def _check_ffmpeg():
    """Проверить доступность ffmpeg"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False

YT_DLP_AVAILABLE = _check_yt_dlp()
FFMPEG_AVAILABLE = _check_ffmpeg()

# ============================================================
# 4. КЭШИРОВАНИЕ
# ============================================================

def load_music_cache():
    """Загрузить кэш музыки"""
    global music_cache
    try:
        if os.path.exists(MUSIC_CACHE_FILE):
            with open(MUSIC_CACHE_FILE, "r", encoding="utf-8") as f:
                music_cache = json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки кэша музыки: {e}")
        music_cache = {}

def save_music_cache():
    """Сохранить кэш музыки"""
    try:
        with open(MUSIC_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(music_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения кэша музыки: {e}")

load_music_cache()

# ============================================================
# 5. ПОНИМАНИЕ ЗАПРОСА
# ============================================================

def understand_music_query(user_query):
    """
    Понимание запроса через ИИ.
    
    Returns:
        dict: {title, artist, version}
    """
    try:
        key = _get_openrouter_key()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты помогаешь найти музыку.\n"
                            "Пользователь написал запрос. Определи:\n"
                            "1. Название песни\n"
                            "2. Исполнителя (если указан)\n"
                            "3. Версию (русская/английская/инструментал/полная)\n\n"
                            "Формат ответа:\n"
                            "НАЗВАНИЕ: ...\n"
                            "ИСПОЛНИТЕЛЬ: ...\n"
                            "ВЕРСИЯ: ...\n\n"
                            "Если версия не указана — выбери самую популярную."
                        )
                    },
                    {"role": "user", "content": user_query}
                ],
                "max_tokens": 200,
                "temperature": 0.5
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content']
                
                name_match = re.search(r'НАЗВАНИЕ:\s*(.+?)(?=\n|$)', result, re.IGNORECASE)
                artist_match = re.search(r'ИСПОЛНИТЕЛЬ:\s*(.+?)(?=\n|$)', result, re.IGNORECASE)
                version_match = re.search(r'ВЕРСИЯ:\s*(.+?)(?=\n|$)', result, re.IGNORECASE)
                
                return {
                    "title": name_match.group(1).strip() if name_match else user_query,
                    "artist": artist_match.group(1).strip() if artist_match else None,
                    "version": version_match.group(1).strip() if version_match else "полная",
                }
    except Exception as e:
        print(f"⚠️ Ошибка понимания запроса: {e}")
    
    return {
        "title": user_query,
        "artist": None,
        "version": "полная",
    }

# ============================================================
# 6. ПОИСК МУЗЫКИ
# ============================================================

def search_music_global(query):
    """
    Поиск музыки через yt-dlp.
    
    Returns:
        dict или None: {source, title, artist, url, video_id, duration, album_art}
    """
    # Проверяем кэш
    cache_key = query.lower().strip()
    if cache_key in music_cache:
        cached = music_cache[cache_key]
        cached_time = cached.get("cached_at")
        if cached_time:
            try:
                if (datetime.now() - datetime.fromisoformat(cached_time)).total_seconds() < 86400:
                    return cached.get("result")
            except Exception:
                pass
    
    result = search_youtube(query)
    
    if not result:
        # Пробуем транслит
        translit_query = transliterate(query)
        if translit_query != query:
            result = search_youtube(translit_query)
    
    if result:
        # Добавляем обложку
        result = add_album_art(result)
        
        # Кэшируем
        music_cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now().isoformat(),
        }
        save_music_cache()
    
    return result

def transliterate(text):
    """Транслитерация русского в английский"""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    return ''.join(translit_map.get(c, c) for c in text.lower())

# ============================================================
# 7. ПОИСК НА YOUTUBE
# ============================================================

def search_youtube(query):
    """
    Поиск на YouTube через yt-dlp.
    
    Returns:
        dict или None
    """
    if not YT_DLP_AVAILABLE:
        print("⚠️ yt-dlp не установлен")
        return None
    
    try:
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--get-title",
            "--get-id",
            "--get-duration",
            "--get-thumbnail",
            f"ytsearch1:{query}"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="ignore"
        )
        
        if result.returncode != 0:
            print(f"⚠️ yt-dlp ошибка: {result.stderr[:100]}")
            return None
        
        lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        
        if len(lines) < 4:
            return None
        
        title = lines[0]
        video_id = lines[1]
        duration_str = lines[2]
        thumbnail = lines[3] if len(lines) > 3 else None
        
        return {
            "source": "YouTube",
            "title": title,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": parse_duration(duration_str),
            "album_art": thumbnail,
            "is_full": True,
            "quality": 9,
        }
    except subprocess.TimeoutExpired:
        print("⚠️ yt-dlp timeout")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка поиска YouTube: {e}")
        return None

def parse_duration(duration_str):
    """
    Парсинг длительности из строки.
    
    Returns:
        int: секунды
    """
    try:
        parts = duration_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0

# ============================================================
# 8. ОБЛОЖКА
# ============================================================

def add_album_art(music_data):
    """
    Добавить обложку к песне.
    
    Returns:
        dict: music_data с album_art
    """
    if not music_data:
        return music_data
    
    title = music_data.get("title", "")
    artist = music_data.get("artist", "")
    
    # Способ 1 — Deezer
    try:
        query = urllib.parse.quote(f"{title} {artist}".strip())
        url = f"https://api.deezer.com/search?q={query}&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                track = data["data"][0]
                album = track.get("album", {})
                if album.get("cover_medium"):
                    music_data["album_art"] = album["cover_medium"]
                    if not music_data.get("artist"):
                        music_data["artist"] = track.get("artist", {}).get("name", "")
                    return music_data
    except Exception:
        pass
    
    # Способ 2 — iTunes
    try:
        query = urllib.parse.quote(f"{title} {artist}".strip())
        url = f"https://itunes.apple.com/search?term={query}&media=music&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                track = data["results"][0]
                if track.get("artworkUrl100"):
                    music_data["album_art"] = track["artworkUrl100"].replace("100x100", "500x500")
                    return music_data
    except Exception:
        pass
    
    # Способ 3 — YouTube thumbnail
    if music_data.get("video_id"):
        music_data["album_art"] = f"https://img.youtube.com/vi/{music_data['video_id']}/hqdefault.jpg"
        return music_data
    
    # Fallback — ui-avatars
    if not music_data.get("album_art"):
        name = artist or title or "Music"
        music_data["album_art"] = (
            f"https://ui-avatars.com/api/?name={urllib.parse.quote(name)}"
            f"&size=200&background=8B5CF6&color=FFFFFF"
        )
    
    return music_data

# ============================================================
# 9. СКАЧИВАНИЕ АУДИО
# ============================================================

def get_music_audio(music_data):
    """
    Получить аудио музыки (mp3).
    
    Returns:
        bytes или None
    """
    if not music_data:
        return None
    
    url = music_data.get("url")
    if not url:
        return None
    
    if not YT_DLP_AVAILABLE or not FFMPEG_AVAILABLE:
        print("⚠️ yt-dlp или ffmpeg не установлены — скачивание невозможно")
        return None
    
    return download_youtube_full(url)

def download_youtube_full(video_url):
    """
    Скачать полную версию с YouTube.
    
    Returns:
        bytes или None
    """
    try:
        output_template = os.path.join(TEMP_DIR, f"music_{int(time.time())}.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_template,
            "--no-playlist",
            "--max-filesize", "50M",
            video_url
        ]
        
        result = subprocess.run(
            cmd,
            timeout=180,
            capture_output=True,
            encoding="utf-8",
            errors="ignore"
        )
        
        if result.returncode != 0:
            print(f"⚠️ yt-dlp ошибка: {result.stderr[:200]}")
            return None
        
        # Ищем скачанный файл
        base_name = os.path.basename(output_template).split(".")[0]
        for f in os.listdir(TEMP_DIR):
            if f.startswith(base_name) and f.endswith(".mp3"):
                file_path = os.path.join(TEMP_DIR, f)
                with open(file_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                
                return audio_data
    except subprocess.TimeoutExpired:
        print("⚠️ yt-dlp timeout при скачивании")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка скачивания: {e}")
        return None
    
    return None

# ============================================================
# 10. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def find_music(query, user_id=None):
    """
    Найти музыку по запросу.
    
    Returns:
        dict или None
    """
    # Проверка глитчей
    if user_id:
        now = time.time()
        last_glitch_time[user_id] = now
    
    parsed = understand_music_query(query)
    search_query = f"{parsed['title']} {parsed['artist'] or ''}".strip()
    
    result = search_music_global(search_query)
    
    if not result:
        return None
    
    result["request"] = {
        "original": query,
        "title": parsed["title"],
        "artist": parsed["artist"],
        "version": parsed["version"],
    }
    
    return result

# ============================================================
# 11. ТЕКСТ ПЕСНИ
# ============================================================

def get_music_lyrics(music_data):
    """
    Получить текст песни.
    
    Returns:
        str или None
    """
    try:
        from music_lyrics import get_lyrics
        if not music_data:
            return None
        
        title = music_data.get("title", "")
        artist = music_data.get("artist", "")
        
        return get_lyrics(title, artist)
    except Exception as e:
        print(f"⚠️ Ошибка получения текста: {e}")
        return None

# ============================================================
# 12. КОМАНДА ДЛЯ БОТА
# ============================================================

def handle_music_command(bot, message, query, user_id):
    """
    Обработка команды музыки.
    """
    music = find_music(query, user_id)
    
    if not music:
        bot.reply_to(message, "❌ Не нашёл музыку по этому запросу")
        return
    
    bot.send_chat_action(message.chat.id, "upload_audio")
    
    audio_data = get_music_audio(music)
    
    # Отправляем обложку
    art_data = None
    try:
        album_art = music.get("album_art")
        if album_art:
            art_response = requests.get(album_art, timeout=10)
            if art_response.status_code == 200:
                art_data = art_response.content
                bot.send_photo(
                    message.chat.id,
                    art_data,
                    caption=(
                        f"🎵 {music.get('title', 'Неизвестно')}\n"
                        f"🎤 {music.get('artist', 'Неизвестен')}"
                    )
                )
    except Exception:
        pass
    
    # Отправляем аудио
    if audio_data and len(audio_data) > 10000:
        try:
            bot.send_audio(
                message.chat.id,
                audio_data,
                title=music.get("title", "Неизвестно"),
                performer=music.get("artist", "Неизвестен"),
                duration=music.get("duration", 0),
                thumb=art_data,
            )
        except Exception as e:
            print(f"⚠️ Ошибка отправки аудио: {e}")
            bot.reply_to(
                message,
                f"🎵 {music.get('title', 'Неизвестно')} — {music.get('artist', 'Неизвестен')}"
            )
    else:
        bot.reply_to(
            message,
            f"🎵 {music.get('title', 'Неизвестно')} — {music.get('artist', 'Неизвестен')}"
        )
    
    # Отправляем текст в ЛС
    try:
        lyrics = get_music_lyrics(music)
        if lyrics:
            msg = f"📝 ТЕКСТ ПЕСНИ: {music.get('title', 'Неизвестно')}\n\n{lyrics}"
            
            if len(msg) > 4000:
                parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                for part in parts:
                    bot.send_message(user_id, part)
            else:
                bot.send_message(user_id, msg)
        else:
            bot.send_message(
                user_id,
                f"❌ Не удалось найти текст: {music.get('title', 'Неизвестно')}"
            )
    except Exception as e:
        print(f"⚠️ Ошибка отправки текста: {e}")

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🎵 Музыкальный модуль загружен (PC)")
print(f"📦 yt-dlp: {'✅' if YT_DLP_AVAILABLE else '❌'}")
print(f"📦 ffmpeg: {'✅' if FFMPEG_AVAILABLE else '❌'}")
print(f"📦 Кэш: {len(music_cache)} записей")
print(f"📁 Temp: {TEMP_DIR}")

if not YT_DLP_AVAILABLE:
    print("⚠️ Установи yt-dlp: pip install yt-dlp")
if not FFMPEG_AVAILABLE:
    print("⚠️ Установи ffmpeg: winget install Gyan.FFmpeg")