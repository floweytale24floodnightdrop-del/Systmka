"""Поиск и получение текстов песен"""

import os
import re
import requests
import subprocess
from urllib.parse import quote

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

TEMP_DIR = "temp_music"
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================
# 2. ПОЛУЧЕНИЕ ТЕКСТА ПЕСНИ
# ============================================================

def get_music_lyrics(music_data):
    """Получить текст песни"""
    if not music_data:
        return None
    
    title = music_data.get('title', '')
    artist = music_data.get('artist', '')
    
    lyrics = get_lyrics(title, artist)
    
    if lyrics:
        return lyrics
    
    audio_url = music_data.get('url') or music_data.get('preview')
    if audio_url:
        transcribed = transcribe_audio_from_url(audio_url)
        if transcribed:
            return format_lyrics(transcribed)
    
    return None

def get_lyrics(song_title, artist=None):
    """Получить текст песни из интернета"""
    lyrics = get_lyrics_from_genius(song_title, artist)
    if lyrics:
        return lyrics
    
    lyrics = get_lyrics_from_azlyrics(song_title, artist)
    if lyrics:
        return lyrics
    
    lyrics = get_lyrics_from_musixmatch(song_title, artist)
    if lyrics:
        return lyrics
    
    return None

# ============================================================
# 3. ПОИСК ТЕКСТА В РАЗНЫХ ИСТОЧНИКАХ
# ============================================================

def get_lyrics_from_genius(song_title, artist=None):
    """Получить текст с Genius"""
    try:
        query = f"{song_title} {artist or ''} lyrics genius"
        url = f"https://api.genius.com/search?q={quote(query)}"
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('response', {}).get('hits'):
                hit = data['response']['hits'][0]
                url = hit['result']['url']
                
                page_response = requests.get(url, timeout=15)
                if page_response.status_code == 200:
                    lyrics_match = re.search(r'<div class="lyrics"[^>]*>(.*?)</div>', page_response.text, re.DOTALL)
                    if lyrics_match:
                        lyrics = lyrics_match.group(1)
                        lyrics = re.sub(r'<[^>]+>', '', lyrics)
                        lyrics = re.sub(r'\[[^\]]+\]', '', lyrics)
                        return format_lyrics(lyrics.strip())
    except:
        pass
    return None

def get_lyrics_from_azlyrics(song_title, artist=None):
    """Получить текст с AZLyrics"""
    try:
        artist_clean = (artist or '').lower().replace(' ', '')
        title_clean = song_title.lower().replace(' ', '')
        
        url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{title_clean}.html"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            lyrics_match = re.search(r'<!-- Usage of azlyrics.*?-->(.*?)</div>', response.text, re.DOTALL)
            if lyrics_match:
                lyrics = lyrics_match.group(1)
                lyrics = re.sub(r'<[^>]+>', '', lyrics)
                return format_lyrics(lyrics.strip())
    except:
        pass
    return None

def get_lyrics_from_musixmatch(song_title, artist=None):
    """Получить текст с Musixmatch"""
    try:
        url = f"https://api.musixmatch.com/ws/1.1/matcher.lyrics.get?q_track={quote(song_title)}&q_artist={quote(artist or '')}&apikey=YOUR_API_KEY"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('message', {}).get('body', {}).get('lyrics'):
                lyrics = data['message']['body']['lyrics']['lyrics_body']
                return format_lyrics(lyrics.strip())
    except:
        pass
    return None

# ============================================================
# 4. РАСПОЗНАВАНИЕ ИЗ АУДИО
# ============================================================

def transcribe_audio_from_url(audio_url):
    """Распознать текст из аудио (fallback)"""
    try:
        response = requests.get(audio_url, timeout=60)
        if response.status_code != 200:
            return None
        
        audio_path = os.path.join(TEMP_DIR, "temp_audio.mp3")
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        
        wav_path = os.path.join(TEMP_DIR, "temp_audio.wav")
        subprocess.run(['ffmpeg', '-i', audio_path, '-ar', '16000', wav_path], timeout=60, capture_output=True)
        
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='ru-RU')
        
        try:
            os.remove(audio_path)
            os.remove(wav_path)
        except:
            pass
        
        return text
    except:
        return None

# ============================================================
# 5. ФОРМАТИРОВАНИЕ
# ============================================================

def format_lyrics(lyrics):
    """Форматировать текст песни"""
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)
    
    lines = lyrics.split('\n')
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        lower = line.lower()
        if any(word in lower for word in ['припев', 'chorus', 'bridge', 'куплет', 'verse', 'outro', 'intro']):
            formatted.append(f"\n[{line.upper()}]\n")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

print("🎵 Модуль текстов песен загружен")