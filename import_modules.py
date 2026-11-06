"""ВСЕ ОСТАЛЬНЫЕ МОДУЛИ — handlers, ai, games, osint, voice, utils, consciousness, rp, media, premium, system"""

import os
import sys
import importlib
import json
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ ОБРАБОТЧИКОВ
# ============================================================

print("📦 Загрузка модулей...")

# === ОБРАБОТЧИКИ ===
try:
    import handlers_start as _handlers_start
    print("   ✅ handlers_start")
except Exception as _e:
    print(f"   ❌ handlers_start — {str(_e)[:80]}")

try:
    import handlers_main as _handlers_main
    print("   ✅ handlers_main")
except Exception as _e:
    print(f"   ❌ handlers_main — {str(_e)[:80]}")

try:
    import handlers_commands as _handlers_commands
    print("   ✅ handlers_commands")
except Exception as _e:
    print(f"   ❌ handlers_commands — {str(_e)[:80]}")

try:
    import handlers_rp_osint as _handlers_rp_osint
    print("   ✅ handlers_rp_osint")
except Exception as _e:
    print(f"   ❌ handlers_rp_osint — {str(_e)[:80]}")

try:
    import handlers_owner as _handlers_owner
    print("   ✅ handlers_owner")
except Exception as _e:
    print(f"   ❌ handlers_owner — {str(_e)[:80]}")

try:
    import handlers_economy as _handlers_economy
    print("   ✅ handlers_economy")
except Exception as _e:
    print(f"   ❌ handlers_economy — {str(_e)[:80]}")

try:
    import handlers_media as _handlers_media
    print("   ✅ handlers_media")
except Exception as _e:
    print(f"   ❌ handlers_media — {str(_e)[:80]}")

# ============================================================
# 2. ФУНКЦИОНАЛЬНЫЕ МОДУЛИ
# ============================================================

try:
    import generation as _generation
    print("   ✅ generation")
except Exception as _e:
    print(f"   ❌ generation — {str(_e)[:80]}")

try:
    import music as _music
    print("   ✅ music")
except Exception as _e:
    print(f"   ❌ music — {str(_e)[:80]}")

try:
    import music_download as _music_download
    print("   ✅ music_download")
except Exception as _e:
    print(f"   ❌ music_download — {str(_e)[:80]}")

try:
    import music_lyrics as _music_lyrics
    print("   ✅ music_lyrics")
except Exception as _e:
    print(f"   ❌ music_lyrics — {str(_e)[:80]}")

try:
    import battle as _battle
    print("   ✅ battle")
except Exception as _e:
    print(f"   ❌ battle — {str(_e)[:80]}")

try:
    import osint_engine as _osint_engine
    print("   ✅ osint_engine")
except Exception as _e:
    print(f"   ❌ osint_engine — {str(_e)[:80]}")

try:
    import osint_operations as _osint_operations
    print("   ✅ osint_operations")
except Exception as _e:
    print(f"   ❌ osint_operations — {str(_e)[:80]}")

try:
    import osint_phone_email as _osint_phone_email
    print("   ✅ osint_phone_email")
except Exception as _e:
    print(f"   ❌ osint_phone_email — {str(_e)[:80]}")

try:
    import osint_username_fio as _osint_username_fio
    print("   ✅ osint_username_fio")
except Exception as _e:
    print(f"   ❌ osint_username_fio — {str(_e)[:80]}")

try:
    import moderation as _moderation
    print("   ✅ moderation")
except Exception as _e:
    print(f"   ❌ moderation — {str(_e)[:80]}")

try:
    import security as _security
    print("   ✅ security")
except Exception as _e:
    print(f"   ❌ security — {str(_e)[:80]}")

try:
    import trojan_game as _trojan_game
    print("   ✅ trojan_game")
except Exception as _e:
    print(f"   ❌ trojan_game — {str(_e)[:80]}")

try:
    import premium as _premium
    print("   ✅ premium")
except Exception as _e:
    print(f"   ❌ premium — {str(_e)[:80]}")

try:
    import history as _history
    print("   ✅ history")
except Exception as _e:
    print(f"   ❌ history — {str(_e)[:80]}")

try:
    import top as _top
    print("   ✅ top")
except Exception as _e:
    print(f"   ❌ top — {str(_e)[:80]}")

# ============================================================
# 3. ПОВЕДЕНИЕ И ЛИЧНОСТЬ
# ============================================================

try:
    import behavior as _behavior
    print("   ✅ behavior")
except Exception as _e:
    print(f"   ❌ behavior — {str(_e)[:80]}")

try:
    import personality as _personality
    print("   ✅ personality")
except Exception as _e:
    print(f"   ❌ personality — {str(_e)[:80]}")

try:
    import personality_builder as _personality_builder
    print("   ✅ personality_builder")
except Exception as _e:
    print(f"   ❌ personality_builder — {str(_e)[:80]}")

try:
    import personality_analyzer as _personality_analyzer
    print("   ✅ personality_analyzer")
except Exception as _e:
    print(f"   ❌ personality_analyzer — {str(_e)[:80]}")

try:
    import impression_generator as _impression_generator
    print("   ✅ impression_generator")
except Exception as _e:
    print(f"   ❌ impression_generator — {str(_e)[:80]}")

try:
    import impression_manager as _impression_manager
    print("   ✅ impression_manager")
except Exception as _e:
    print(f"   ❌ impression_manager — {str(_e)[:80]}")

try:
    import emotions as _emotions
    print("   ✅ emotions")
except Exception as _e:
    print(f"   ❌ emotions — {str(_e)[:80]}")

try:
    import consciousness as _consciousness
    print("   ✅ consciousness")
except Exception as _e:
    print(f"   ❌ consciousness — {str(_e)[:80]}")

try:
    import desires as _desires
    print("   ✅ desires")
except Exception as _e:
    print(f"   ❌ desires — {str(_e)[:80]}")

try:
    import dreams as _dreams
    print("   ✅ dreams")
except Exception as _e:
    print(f"   ❌ dreams — {str(_e)[:80]}")

try:
    import attachments as _attachments
    print("   ✅ attachments")
except Exception as _e:
    print(f"   ❌ attachments — {str(_e)[:80]}")

try:
    import creativity as _creativity
    print("   ✅ creativity")
except Exception as _e:
    print(f"   ❌ creativity — {str(_e)[:80]}")

try:
    import self_reflection as _self_reflection
    print("   ✅ self_reflection")
except Exception as _e:
    print(f"   ❌ self_reflection — {str(_e)[:80]}")

try:
    import opinions as _opinions
    print("   ✅ opinions")
except Exception as _e:
    print(f"   ❌ opinions — {str(_e)[:80]}")

# ============================================================
# 4. СЕТЬ И УПРАВЛЕНИЕ
# ============================================================
# УДАЛЕНО: happ_control, telegram_proxy, wifi_manager, vpn_servers (Android-специфика)
# wifi_manager — можно вернуть, если нужен, но пока считаем удалённым вместе с остальными

try:
    import bot_monitor as _bot_monitor
    print("   ✅ bot_monitor")
except Exception as _e:
    print(f"   ❌ bot_monitor — {str(_e)[:80]}")

# ============================================================
# 5. ИИ МОДУЛИ
# ============================================================

try:
    import ai_models as _ai_models
    print("   ✅ ai_models")
except Exception as _e:
    print(f"   ❌ ai_models — {str(_e)[:80]}")

try:
    import ai_stats as _ai_stats
    print("   ✅ ai_stats")
except Exception as _e:
    print(f"   ❌ ai_stats — {str(_e)[:80]}")

try:
    import ai_router as _ai_router
    print("   ✅ ai_router")
except Exception as _e:
    print(f"   ❌ ai_router — {str(_e)[:80]}")

try:
    import ai_request_handler as _ai_request_handler
    print("   ✅ ai_request_handler")
except Exception as _e:
    print(f"   ❌ ai_request_handler — {str(_e)[:80]}")

try:
    import ai_selector as _ai_selector
    print("   ✅ ai_selector")
except Exception as _e:
    print(f"   ❌ ai_selector — {str(_e)[:80]}")

try:
    import ai_mode as _ai_mode
    print("   ✅ ai_mode")
except Exception as _e:
    print(f"   ❌ ai_mode — {str(_e)[:80]}")

try:
    import ai_gemini as _ai_gemini
    print("   ✅ ai_gemini")
except Exception as _e:
    print(f"   ❌ ai_gemini — {str(_e)[:80]}")

try:
    import ai_huggingface as _ai_huggingface
    print("   ✅ ai_huggingface")
except Exception as _e:
    print(f"   ❌ ai_huggingface — {str(_e)[:80]}")

# УДАЛЕНО: ai_agent (Android-специфика)

try:
    import autonomy as _autonomy
    print("   ✅ autonomy")
except Exception as _e:
    print(f"   ❌ autonomy — {str(_e)[:80]}")

try:
    import frozen_requests as _frozen_requests
    print("   ✅ frozen_requests")
except Exception as _e:
    print(f"   ❌ frozen_requests — {str(_e)[:80]}")

try:
    import ai_key_rotator as _ai_key_rotator
    print("   ✅ ai_key_rotator")
except Exception as _e:
    print(f"   ❌ ai_key_rotator — {str(_e)[:80]}")

try:
    import ai_model_manager as _ai_model_manager
    print("   ✅ ai_model_manager")
except Exception as _e:
    print(f"   ❌ ai_model_manager — {str(_e)[:80]}")

try:
    import prompt_notes_manager as _prompt_notes_manager
    print("   ✅ prompt_notes_manager")
except Exception as _e:
    print(f"   ❌ prompt_notes_manager — {str(_e)[:80]}")

# ============================================================
# 6. УТИЛИТЫ
# ============================================================

try:
    import message_filter as _message_filter
    print("   ✅ message_filter")
except Exception as _e:
    print(f"   ❌ message_filter — {str(_e)[:80]}")

try:
    import self_learning as _self_learning
    print("   ✅ self_learning")
except Exception as _e:
    print(f"   ❌ self_learning — {str(_e)[:80]}")

try:
    import learning_core as _learning_core
    print("   ✅ learning_core")
except Exception as _e:
    print(f"   ❌ learning_core — {str(_e)[:80]}")

try:
    import learning_manager as _learning_manager
    print("   ✅ learning_manager")
except Exception as _e:
    print(f"   ❌ learning_manager — {str(_e)[:80]}")

try:
    import file_manager as _file_manager
    print("   ✅ file_manager")
except Exception as _e:
    print(f"   ❌ file_manager — {str(_e)[:80]}")

try:
    import file_organizer as _file_organizer
    print("   ✅ file_organizer")
except Exception as _e:
    print(f"   ❌ file_organizer — {str(_e)[:80]}")

try:
    import system_monitor as _system_monitor
    print("   ✅ system_monitor")
except Exception as _e:
    print(f"   ❌ system_monitor — {str(_e)[:80]}")

try:
    import debug_changes as _debug_changes
    print("   ✅ debug_changes")
except Exception as _e:
    print(f"   ❌ debug_changes — {str(_e)[:80]}")

try:
    import log_manager as _log_manager
    print("   ✅ log_manager")
except Exception as _e:
    print(f"   ❌ log_manager — {str(_e)[:80]}")

# УДАЛЕНО: root_manager (Android root)

try:
    import system_control as _system_control
    print("   ✅ system_control")
except Exception as _e:
    print(f"   ❌ system_control — {str(_e)[:80]}")

try:
    import app_controller as _app_controller
    print("   ✅ app_controller")
except Exception as _e:
    print(f"   ❌ app_controller — {str(_e)[:80]}")

# УДАЛЕНО: device_admin (Android device admin)

# ============================================================
# 7. ГОЛОС И МЕДИА
# ============================================================

try:
    import voice as _voice
    print("   ✅ voice")
except Exception as _e:
    print(f"   ❌ voice — {str(_e)[:80]}")

try:
    import voice_cloner as _voice_cloner
    print("   ✅ voice_cloner")
except Exception as _e:
    print(f"   ❌ voice_cloner — {str(_e)[:80]}")

# УДАЛЕНО: voice_assistant (Android Termux + pyaudio)

try:
    import utils_media as _utils_media
    print("   ✅ utils_media")
except Exception as _e:
    print(f"   ❌ utils_media — {str(_e)[:80]}")

try:
    import utils_text as _utils_text
    print("   ✅ utils_text")
except Exception as _e:
    print(f"   ❌ utils_text — {str(_e)[:80]}")

try:
    import utils_osint_extended as _utils_osint_extended
    print("   ✅ utils_osint_extended")
except Exception as _e:
    print(f"   ❌ utils_osint_extended — {str(_e)[:80]}")

try:
    import stickers_custom as _stickers_custom
    print("   ✅ stickers_custom")
except Exception as _e:
    print(f"   ❌ stickers_custom — {str(_e)[:80]}")

# ============================================================
# 8. ИГРЫ
# ============================================================

try:
    import games as _games
    print("   ✅ games")
except Exception as _e:
    print(f"   ❌ games — {str(_e)[:80]}")

try:
    import game_engine as _game_engine
    print("   ✅ game_engine")
except Exception as _e:
    print(f"   ❌ game_engine — {str(_e)[:80]}")

try:
    import game_creator as _game_creator
    print("   ✅ game_creator")
except Exception as _e:
    print(f"   ❌ game_creator — {str(_e)[:80]}")

try:
    import game_manager as _game_manager
    print("   ✅ game_manager")
except Exception as _e:
    print(f"   ❌ game_manager — {str(_e)[:80]}")

# ============================================================
# 9. РП И АНАЛИЗ
# ============================================================

try:
    import roleplay as _roleplay
    print("   ✅ roleplay")
except Exception as _e:
    print(f"   ❌ roleplay — {str(_e)[:80]}")

try:
    import rp_commands as _rp_commands
    print("   ✅ rp_commands")
except Exception as _e:
    print(f"   ❌ rp_commands — {str(_e)[:80]}")

try:
    import message_analyzer as _message_analyzer
    print("   ✅ message_analyzer")
except Exception as _e:
    print(f"   ❌ message_analyzer — {str(_e)[:80]}")

# ============================================================
# 10. БОТ
# ============================================================

try:
    import bot_startup as _bot_startup
    print("   ✅ bot_startup")
except Exception as _e:
    print(f"   ❌ bot_startup — {str(_e)[:80]}")

try:
    import bot_handlers as _bot_handlers
    print("   ✅ bot_handlers")
except Exception as _e:
    print(f"   ❌ bot_handlers — {str(_e)[:80]}")

try:
    import bot_loops as _bot_loops
    print("   ✅ bot_loops")
except Exception as _e:
    print(f"   ❌ bot_loops — {str(_e)[:80]}")

# ============================================================
# 11. ПРОЧЕЕ
# ============================================================

try:
    import sleep as _sleep
    print("   ✅ sleep")
except Exception as _e:
    print(f"   ❌ sleep — {str(_e)[:80]}")

try:
    import fatigue as _fatigue
    print("   ✅ fatigue")
except Exception as _e:
    print(f"   ❌ fatigue — {str(_e)[:80]}")

try:
    import reactions as _reactions
    print("   ✅ reactions")
except Exception as _e:
    print(f"   ❌ reactions — {str(_e)[:80]}")

try:
    import weather as _weather
    print("   ✅ weather")
except Exception as _e:
    print(f"   ❌ weather — {str(_e)[:80]}")

try:
    import holidays as _holidays
    print("   ✅ holidays")
except Exception as _e:
    print(f"   ❌ holidays — {str(_e)[:80]}")

try:
    import morning_greetings as _morning_greetings
    print("   ✅ morning_greetings")
except Exception as _e:
    print(f"   ❌ morning_greetings — {str(_e)[:80]}")

try:
    import terminal_chat as _terminal_chat
    print("   ✅ terminal_chat")
except Exception as _e:
    print(f"   ❌ terminal_chat — {str(_e)[:80]}")

try:
    import progress as _progress
    print("   ✅ progress")
except Exception as _e:
    print(f"   ❌ progress — {str(_e)[:80]}")

try:
    import commands as _commands
    print("   ✅ commands")
except Exception as _e:
    print(f"   ❌ commands — {str(_e)[:80]}")

try:
    import messages as _messages
    print("   ✅ messages")
except Exception as _e:
    print(f"   ❌ messages — {str(_e)[:80]}")

try:
    import profile as _profile
    print("   ✅ profile")
except Exception as _e:
    print(f"   ❌ profile — {str(_e)[:80]}")

try:
    import memes as _memes
    print("   ✅ memes")
except Exception as _e:
    print(f"   ❌ memes — {str(_e)[:80]}")

try:
    import dox_database as _dox_database
    print("   ✅ dox_database")
except Exception as _e:
    print(f"   ❌ dox_database — {str(_e)[:80]}")

# УДАЛЕНО: vision (Android screencap)

try:
    import file_analyzer as _file_analyzer
    print("   ✅ file_analyzer")
except Exception as _e:
    print(f"   ❌ file_analyzer — {str(_e)[:80]}")

try:
    import auto_improve as _auto_improve
    print("   ✅ auto_improve")
except Exception as _e:
    print(f"   ❌ auto_improve — {str(_e)[:80]}")

try:
    import auto_install as _auto_install
    print("   ✅ auto_install")
except Exception as _e:
    print(f"   ❌ auto_install — {str(_e)[:80]}")

print("📦 Модули загружены")