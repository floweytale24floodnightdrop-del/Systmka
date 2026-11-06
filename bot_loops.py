"""Фоновые потоки и циклы"""

import time
import threading

# ============================================================
# 1. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# ============================================================

def _safe_thread(target, args=(), kwargs=None, name=None):
    """Запустить поток безопасно"""
    if kwargs is None:
        kwargs = {}
    
    try:
        if not callable(target):
            return None
        
        thread = threading.Thread(
            target=target,
            args=args,
            kwargs=kwargs,
            daemon=True,
            name=name or target.__name__
        )
        thread.start()
        return thread
    except Exception as e:
        print(f"⚠️ safe_thread ({name or '?'}): {e}")
        return None

# ============================================================
# 2. ЦИКЛЫ
# ============================================================

def auto_save_loop():
    """
    Автосохранение данных каждые 5 минут.
    
    ИСПРАВЛЕНО: используем db._schedule_save() вместо блокирующего
    db.save_all_data(). Реальная запись произойдёт в фоновом потоке
    database.py с дебаунсом.
    """
    while True:
        try:
            time.sleep(300)
            
            import database as db
            
            # ИСПРАВЛЕНО: дебаунс-сохранение вместо блокирующего
            if hasattr(db, "_schedule_save"):
                db._schedule_save()
            else:
                # Fallback для старых версий
                db.save_all_data()
            
            try:
                from consciousness import save_consciousness
                save_consciousness()
            except Exception:
                pass
            
            try:
                from bot import save_state
                save_state()
            except Exception:
                pass
            
            try:
                from roleplay import save_rp_data
                save_rp_data()
            except Exception:
                pass
            
            try:
                from message_analyzer import save_analysis
                save_analysis()
            except Exception:
                pass
            
            try:
                from osint_engine import save_osint_data, save_accounts
                save_osint_data()
                save_accounts()
            except Exception:
                pass
        
        except Exception as e:
            print(f"⚠️ auto_save_loop: {e}")


def autonomy_loop_wrapper(bot, owner_ids, db):
    """Обёртка для autonomy_loop"""
    try:
        from autonomy import autonomy_loop
        autonomy_loop(bot, owner_ids, db)
    except Exception as e:
        print(f"⚠️ autonomy_loop_wrapper: {e}")


def clean_temp_loop():
    """Очистка временных файлов каждые 30 минут"""
    while True:
        try:
            time.sleep(1800)
            
            try:
                from autonomy import clean_temp_files
                cleaned = clean_temp_files()
                if cleaned:
                    print(f"🧹 Очищено временных файлов: {len(cleaned)}")
            except Exception:
                pass
        
        except Exception as e:
            print(f"⚠️ clean_temp_loop: {e}")


def games_and_creativity_loop(bot, owner_ids, db):
    """Игры и творчество"""
    while True:
        try:
            time.sleep(300)
            
            try:
                from games import auto_create_game_loop, auto_offer_game_loop
                auto_create_game_loop(bot, owner_ids, db)
                auto_offer_game_loop(bot, db)
            except Exception as e:
                print(f"⚠️ games loop: {e}")
            
            try:
                from creativity import auto_creativity_loop
                auto_creativity_loop()
            except Exception as e:
                print(f"⚠️ creativity loop: {e}")
        
        except Exception as e:
            print(f"⚠️ games_and_creativity_loop: {e}")


def network_loop(bot, owner_ids):
    """Сеть — обработка замороженных запросов"""
    while True:
        try:
            time.sleep(60)
            
            try:
                from frozen_requests import auto_process_frozen_loop
                auto_process_frozen_loop(bot, owner_ids)
            except Exception as e:
                print(f"⚠️ network_loop: {e}")
        
        except Exception as e:
            print(f"⚠️ network_loop outer: {e}")


def error_watchdog_loop():
    """Мониторинг ошибок"""
    while True:
        try:
            time.sleep(120)
            
            try:
                from error_fixer import watchdog_loop
                watchdog_loop()
            except Exception:
                pass
        
        except Exception as e:
            print(f"⚠️ error_watchdog_loop: {e}")


def moderation_loop(bot):
    """Модерация — снятие истёкших мутов"""
    while True:
        try:
            time.sleep(60)
            
            try:
                from moderation import check_expired_mutes
                expired = check_expired_mutes(bot)
                if expired:
                    print(f"🔊 Снято мутов: {len(expired)}")
            except Exception:
                pass
        
        except Exception as e:
            print(f"⚠️ moderation_loop: {e}")


def morning_greetings_loop_wrapper(bot, db, owner_ids):
    """Утренние приветствия"""
    try:
        from morning_greetings import morning_greeting_loop
        morning_greeting_loop(bot, db, owner_ids)
    except Exception as e:
        print(f"⚠️ morning_greetings: {e}")


def system_monitor_loop(bot, owner_ids):
    """Мониторинг системы"""
    try:
        from system_monitor import monitor_loop as sm_monitor_loop
        sm_monitor_loop(bot, owner_ids, interval=300)
    except Exception as e:
        print(f"⚠️ system_monitor: {e}")


def terminal_chat_wrapper(bot, owner_ids):
    """Терминал-чат"""
    try:
        from terminal_chat import terminal_chat_loop
        terminal_chat_loop(bot, owner_ids)
    except Exception as e:
        print(f"⚠️ terminal_chat: {e}")


def attachments_loop_wrapper(bot, db):
    """Проверка скучания"""
    try:
        from attachments import check_missing_loop
        check_missing_loop(bot, db)
    except Exception as e:
        print(f"⚠️ attachments: {e}")


def credits_loop(bot):
    """
    Кредитный цикл — обработка ежедневных платежей по кредитам.
    
    НОВОЕ: раз в час проходит по всем кредитам и списывает платежи.
    Вызывает handlers_economy.credits_background_loop.
    """
    try:
        from handlers_economy import credits_background_loop
        credits_background_loop(bot, interval=3600)
    except Exception as e:
        print(f"⚠️ credits_loop: {e}")


def meme_learning_loop():
    """Автообучение мемам"""
    while True:
        try:
            time.sleep(1800)  # 30 минут
            
            try:
                from memes import learn_memes_from_internet
                learned = learn_memes_from_internet()
                if learned > 0:
                    print(f"🎭 Выучено мемов: {learned}")
            except Exception:
                pass
        
        except Exception as e:
            print(f"⚠️ meme_learning_loop: {e}")

# ============================================================
# 3. ЗАПУСК ПОТОКОВ
# ============================================================

def start_background_threads(bot, OWNER_IDS, db):
    """
    Запустить все фоновые потоки.
    
    Returns:
        list: список запущенных потоков
    """
    threads = []
    
    # 1. Автосохранение
    threads.append(_safe_thread(auto_save_loop, name="auto_save"))
    
    # 2. Автономия
    threads.append(_safe_thread(
        autonomy_loop_wrapper,
        args=(bot, OWNER_IDS, db),
        name="autonomy"
    ))
    
    # 3. Очистка temp
    threads.append(_safe_thread(clean_temp_loop, name="clean_temp"))
    
    # 4. Игры и творчество
    threads.append(_safe_thread(
        games_and_creativity_loop,
        args=(bot, OWNER_IDS, db),
        name="games_creativity"
    ))
    
    # 5. Сеть (замороженные запросы)
    threads.append(_safe_thread(
        network_loop,
        args=(bot, OWNER_IDS),
        name="network"
    ))
    
    # 6. Мониторинг ошибок
    threads.append(_safe_thread(error_watchdog_loop, name="error_watchdog"))
    
    # 7. Модерация (снятие истёкших мутов)
    threads.append(_safe_thread(
        moderation_loop,
        args=(bot,),
        name="moderation"
    ))
    
    # 8. Утренние приветствия
    threads.append(_safe_thread(
        morning_greetings_loop_wrapper,
        args=(bot, db, OWNER_IDS),
        name="morning_greetings"
    ))
    
    # 9. Системный мониторинг (PC)
    threads.append(_safe_thread(
        system_monitor_loop,
        args=(bot, OWNER_IDS),
        name="system_monitor"
    ))
    
    # 10. Терминал-чат
    threads.append(_safe_thread(
        terminal_chat_wrapper,
        args=(bot, OWNER_IDS),
        name="terminal_chat"
    ))
    
    # 11. Привязанности (скучание)
    threads.append(_safe_thread(
        attachments_loop_wrapper,
        args=(bot, db),
        name="attachments"
    ))
    
    # 12. НОВОЕ: Кредитный цикл
    threads.append(_safe_thread(
        credits_loop,
        args=(bot,),
        name="credits"
    ))
    
    # 13. НОВОЕ: Автообучение мемам
    threads.append(_safe_thread(
        meme_learning_loop,
        name="meme_learning"
    ))
    
    # ============================================================
    # 4. ОПЦИОНАЛЬНЫЕ ЗАПУСКИ (не в потоках)
    # ============================================================
    
    # Мемы (автообучение) — уже запущено в meme_learning_loop
    # УБРАНО: больше не вызываем start_auto_learning дважды
    
    # Автоулучшения (безопасный режим)
    try:
        from auto_improve import start_auto_improve
        start_auto_improve()
    except Exception as e:
        print(f"⚠️ auto_improve: {e}")
    
    # ============================================================
    # 5. ИТОГ
    # ============================================================
    
    active = [t for t in threads if t is not None]
    print(f"✅ Запущено потоков: {len(active)}")
    
    return threads

# ============================================================
# 6. СОЗНАНИЕ
# ============================================================

def initialize_consciousness():
    """Инициализировать сознание при старте"""
    try:
        from consciousness import think, feel, set_goal
        think("Я запустилась")
        feel("happiness", 2)
        set_goal("Быть лучшей для Флауи")
        print("🧠 Сознание инициализировано")
    except Exception as e:
        print(f"⚠️ Не удалось инициализировать сознание: {e}")

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🔁 Модуль фоновых потоков загружен")
print(f"📋 Всего циклов: 13")