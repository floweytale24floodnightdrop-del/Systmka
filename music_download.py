"""Скачивание и конвертация музыки"""

import os
import subprocess
import requests
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

TEMP_DIR = "temp_music"
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================
# 2. СКАЧИВАНИЕ ПОЛНОЙ ВЕРСИИ
# ============================================================

def download_full_music(music_data):
    """Скачать полную версию музыки"""
    if not music_data:
        return None
    
    if music_data.get('source') == 'YouTube':
        return download_youtube_full(music_data['url'])
    
    if music_data.get('url'):
        try:
            response = requests.get(music_data['url'], timeout=60, stream=True)
            if response.status_code == 200:
                audio_data = response.content
                if len(audio_data) > 10000:
                    return audio_data
        except:
            pass
    
    if music_data.get('preview'):
        try:
            response = requests.get(music_data['preview'], timeout=60, stream=True)
            if response.status_code == 200:
                audio_data = response.content
                if len(audio_data) > 10000:
                    return audio_data
        except:
            pass
    
    return None

def download_youtube_full(video_url):
    """Скачать полную версию с YouTube"""
    try:
        output_file = os.path.join(TEMP_DIR, f"music_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        cmd = [
            'yt-dlp',
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '-o', f"{output_file}.%(ext)s",
            '--no-playlist',
            video_url
        ]
        
        result = subprocess.run(cmd, timeout=180, capture_output=True)
        
        if result.returncode == 0:
            for f in os.listdir(TEMP_DIR):
                if f.startswith(os.path.basename(output_file)) and f.endswith('.mp3'):
                    file_path = os.path.join(TEMP_DIR, f)
                    with open(file_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                    os.remove(file_path)
                    return audio_data
    except:
        pass
    
    return None

def get_music_audio(music_data):
    """Получить аудио музыки (алиас)"""
    return download_full_music(music_data)

# ============================================================
# 3. КОНВЕРТАЦИЯ
# ============================================================

def convert_audio(input_file, output_file, output_format="mp3"):
    """Конвертировать аудио через ffmpeg"""
    try:
        subprocess.run(["ffmpeg", "-i", input_file, output_file], timeout=60, capture_output=True)
        if os.path.exists(output_file):
            return True
    except:
        pass
    return False

def get_audio_duration(file_path):
    """Получить длительность аудио"""
    try:
        result = subprocess.run(["ffmpeg", "-i", file_path], capture_output=True, text=True, timeout=10)
        import re
        match = re.search(r'Duration: (\d+):(\d+):(\d+)', result.stderr)
        if match:
            hours, minutes, seconds = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
    except:
        pass
    return 0

print("🎵 Модуль скачивания музыки загружен")