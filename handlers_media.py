"""Обработка медиа — голосовые, фото, видео, стикеры, документы"""

import telebot
import time
import os
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS

# ============================================================
# 2. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def register_media_handlers(bot, message, chat_id, user, is_owner_user):
    """
    Обработка медиа-сообщений.
    
    Returns:
        bool: True если медиа обработано
    """
    
    # ============================================================
    # 2.1 ГОЛОСОВЫЕ СООБЩЕНИЯ
    # ============================================================
    
    if hasattr(message, 'voice') and message.voice is not None:
        return _handle_voice(bot, message, chat_id, user)
    
    # ============================================================
    # 2.2 ФОТОГРАФИИ
    # ============================================================
    
    if hasattr(message, 'photo') and message.photo is not None:
        return _handle_photo(bot, message, chat_id, user)
    
    # ============================================================
    # 2.3 ВИДЕО
    # ============================================================
    
    if hasattr(message, 'video') and message.video is not None:
        return _handle_video(bot, message, chat_id, user)
    
    # ============================================================
    # 2.4 ВИДЕО-КРУЖКИ
    # ============================================================
    
    if hasattr(message, 'video_note') and message.video_note is not None:
        return _handle_video_note(bot, message, chat_id, user)
    
    # ============================================================
    # 2.5 СТИКЕРЫ
    # ============================================================
    
    if hasattr(message, 'sticker') and message.sticker is not None:
        return _handle_sticker(bot, message, chat_id, user)
    
    # ============================================================
    # 2.6 GIF/АНИМАЦИИ
    # ============================================================
    
    if hasattr(message, 'animation') and message.animation is not None:
        return _handle_animation(bot, message, chat_id, user)
    
    # ============================================================
    # 2.7 АУДИО
    # ============================================================
    
    if hasattr(message, 'audio') and message.audio is not None:
        return _handle_audio(bot, message, chat_id, user)
    
    # ============================================================
    # 2.8 ДОКУМЕНТЫ
    # ============================================================
    
    if hasattr(message, 'document') and message.document is not None:
        return _handle_document(bot, message, chat_id, user)
    
    # ============================================================
    # 2.9 КОНТАКТЫ
    # ============================================================
    
    if hasattr(message, 'contact') and message.contact is not None:
        return _handle_contact(bot, message, chat_id, user)
    
    # ============================================================
    # 2.10 ЛОКАЦИЯ
    # ============================================================
    
    if hasattr(message, 'location') and message.location is not None:
        return _handle_location(bot, message, chat_id, user)
    
    return False

# ============================================================
# 3. ОБРАБОТЧИКИ ПО ТИПАМ
# ============================================================

def _handle_voice(bot, message, chat_id, user):
    """Голосовое сообщение"""
    try:
        from utils_media import transcribe_voice
        from voice import generate_voice as generate_voice_emotion, detect_emotion
        
        voice_text = transcribe_voice(None, bot, message.voice.file_id)
        
        if voice_text:
            emotion = detect_emotion(voice_text)
            response_voice = generate_voice_emotion(
                f"Слышу: {voice_text}",
                emotion=emotion
            )
            
            if response_voice:
                bot.send_voice(chat_id, response_voice)
            else:
                bot.reply_to(message, f"🎤 {voice_text[:100]}")
        else:
            bot.reply_to(message, "🎤 Не удалось распознать голосовое")
    except Exception as e:
        print(f"⚠️ Ошибка обработки голосового: {e}")
        bot.reply_to(message, "❌ Ошибка обработки голосового")
        _notify_error(bot, e, chat_id, user.first_name, "голосовое")
    return True

def _handle_photo(bot, message, chat_id, user):
    """Фотография"""
    try:
        from utils_media import analyze_image_with_ai, extract_text_from_image
        
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # OCR
        ocr_text = extract_text_from_image(downloaded)
        
        # Анализ через ИИ
        analysis = analyze_image_with_ai(downloaded)
        
        response = f"🖼 Вижу: {analysis[:150]}"
        if ocr_text:
            response += f"\n\n📝 Текст на фото: {ocr_text[:200]}"
        
        bot.reply_to(message, response)
    except Exception as e:
        print(f"⚠️ Ошибка обработки фото: {e}")
        bot.reply_to(message, "🖼 Вижу картинку, но не могу проанализировать")
        _notify_error(bot, e, chat_id, user.first_name, "фото")
    return True

def _handle_video(bot, message, chat_id, user):
    """Видео"""
    try:
        from utils_media import analyze_video
        
        analysis = analyze_video(None, bot, message.video.file_id)
        if analysis:
            bot.reply_to(message, f"🎬 Видео: {analysis[:150]}")
        else:
            bot.reply_to(message, "🎬 Видео получено")
    except Exception as e:
        print(f"⚠️ Ошибка обработки видео: {e}")
        bot.reply_to(message, "🎬 Видео получено")
    return True

def _handle_video_note(bot, message, chat_id, user):
    """Видео-кружок"""
    try:
        from utils_media import analyze_video
        
        analysis = analyze_video(None, bot, message.video_note.file_id)
        if analysis:
            bot.reply_to(message, f"🔄 Кружок: {analysis[:150]}")
        else:
            bot.reply_to(message, "🔄 Кружок получен")
    except Exception as e:
        print(f"⚠️ Ошибка обработки кружка: {e}")
        bot.reply_to(message, "🔄 Кружок получен")
    return True

def _handle_sticker(bot, message, chat_id, user):
    """Стикер"""
    try:
        from utils_media import analyze_sticker
        from stickers_custom import add_custom_sticker
        import random
        
        analysis = analyze_sticker(bot, message.sticker.file_id)
        
        # Сохраняем стикер с 30% шансом
        if random.random() < 0.3:
            try:
                add_custom_sticker(
                    file_id=message.sticker.file_id,
                    set_name=message.sticker.set_name or "unknown",
                    source_user=user.username or user.first_name,
                    description=analysis[:50] if analysis else "Стикер"
                )
            except Exception:
                pass
        
        if analysis:
            bot.reply_to(message, f"🏷 Стикер: {analysis[:100]}")
        else:
            bot.reply_to(message, "🏷 Стикер получен")
    except Exception as e:
        print(f"⚠️ Ошибка обработки стикера: {e}")
        bot.reply_to(message, "🏷 Стикер получен")
    return True

def _handle_animation(bot, message, chat_id, user):
    """GIF/Анимация"""
    try:
        from utils_media import analyze_gif
        
        analysis = analyze_gif(bot, message.animation.file_id)
        if analysis:
            bot.reply_to(message, f"🎞 Гиф: {analysis[:100]}")
        else:
            bot.reply_to(message, "🎞 Гиф получен")
    except Exception as e:
        print(f"⚠️ Ошибка обработки гиф: {e}")
        bot.reply_to(message, "🎞 Гиф получен")
    return True

def _handle_audio(bot, message, chat_id, user):
    """Аудиофайл"""
    try:
        audio = message.audio
        title = audio.title or "Аудио"
        performer = audio.performer or "Неизвестный исполнитель"
        duration = audio.duration or 0
        
        minutes = duration // 60
        seconds = duration % 60
        
        bot.reply_to(
            message,
            f"🎵 {title} — {performer}\n⏱ {minutes}:{seconds:02d}"
        )
    except Exception as e:
        print(f"⚠️ Ошибка обработки аудио: {e}")
        bot.reply_to(message, "🎵 Аудио получено")
    return True

def _handle_document(bot, message, chat_id, user):
    """Документ"""
    try:
        doc = message.document
        file_name = doc.file_name or "Документ"
        file_size = doc.file_size or 0
        
        size_kb = file_size // 1024
        if size_kb > 1024:
            size_str = f"{size_kb // 1024}MB"
        else:
            size_str = f"{size_kb}KB"
        
        bot.reply_to(message, f"📄 {file_name}\n💾 {size_str}")
    except Exception as e:
        print(f"⚠️ Ошибка обработки документа: {e}")
        bot.reply_to(message, "📄 Документ получен")
    return True

def _handle_contact(bot, message, chat_id, user):
    """Контакт"""
    try:
        contact = message.contact
        name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
        phone = contact.phone_number or "Не указан"
        
        bot.reply_to(message, f"👤 {name}\n📞 {phone}")
    except Exception as e:
        print(f"⚠️ Ошибка обработки контакта: {e}")
        bot.reply_to(message, "👤 Контакт получен")
    return True

def _handle_location(bot, message, chat_id, user):
    """Локация"""
    try:
        loc = message.location
        lat = loc.latitude
        lon = loc.longitude
        
        bot.reply_to(message, f"📍 {lat:.6f}, {lon:.6f}")
    except Exception as e:
        print(f"⚠️ Ошибка обработки локации: {e}")
        bot.reply_to(message, "📍 Локация получена")
    return True

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def _notify_error(bot, error, chat_id, user_name, source):
    """Уведомить владельцев об ошибке"""
    try:
        from error_reporter import notify_error
        notify_error(bot, OWNER_IDS, error, chat_id, user_name, source)
    except Exception:
        pass

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("📨 Обработчик медиа загружен (PC)")