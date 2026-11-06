"""Загрузка всех данных и инициализация модулей"""

import time
import os
from datetime import datetime

# ============================================================
# 1. ЗАГРУЗКА ДАННЫХ
# ============================================================

def load_all_data(bot, log_error=None, bot_status=None):
    """
    Загрузить все данные и модули.
    
    Args:
        bot: telebot instance
        log_error: функция логирования ошибок (опционально)
        bot_status: словарь статуса бота (опционально)
    """
    
    def _log(e, source="init"):
        if log_error:
            try:
                log_error(e, source)
                return
            except Exception:
                pass
        print(f"⚠️ [{source}] {e}")
    
    print("=" * 60)
    print("🤖 СИСТМКА ЗАПУСКАЕТСЯ...")
    print("=" * 60)
    
    # ------------------------------------------------------------
    # 1.1 Состояние бота
    # ------------------------------------------------------------
    try:
        from bot import load_state
        load_state()
        print("✅ Состояние бота загружено")
    except Exception as e:
        _log(e, "load_state")
    
    # ------------------------------------------------------------
    # 1.2 Проверка интернета
    # ------------------------------------------------------------
    try:
        from config_network import check_internet
        state = check_internet()
        status_icon = "✅" if state in ("online", "restored") else "❌"
        print(f"🌐 Интернет: {status_icon}")
    except Exception as e:
        print(f"⚠️ Не удалось проверить интернет: {e}")
    
    # ------------------------------------------------------------
    # 1.3 Очистка логов
    # ------------------------------------------------------------
    try:
        from bot import clean_logs_now
        clean_logs_now()
    except Exception:
        try:
            from bot_monitor import clean_logs
            clean_logs()
        except Exception:
            pass
    
    # ============================================================
    # 2. ЗАГРУЗКА ДАННЫХ
    # ============================================================
    
    print("📦 Загрузка данных...")
    
    loaders = [
        ("trash", "init_trash"),
        ("stickers_custom", "load_stickers"),
        ("debug_changes", "load_changes"),
        ("rp_commands", "load_rp_commands"),
        ("error_fixer", "load_error_history"),
        ("error_reporter", "load_notifications"),
        ("consciousness", "load_consciousness"),
        ("self_reflection", "load_reflections"),
        ("attachments", "load_attachments"),
        ("desires", "load_desires"),
        ("frozen_requests", "load_frozen"),
        ("personality", "load_personality"),
        ("games", "load_games"),
        ("dreams", "load_dreams"),
        ("roleplay", "load_rp_data"),
        ("message_analyzer", "load_analysis"),
        ("osint_engine", "load_osint_data"),
        ("osint_engine", "load_accounts"),
        ("premium", "load_premium_data"),
        ("morning_greetings", "load_morning_data"),
    ]
    
    loaded_count = 0
    failed_count = 0
    
    for module_name, func_name in loaders:
        try:
            module = __import__(module_name)
            func = getattr(module, func_name, None)
            if func:
                func()
                loaded_count += 1
            else:
                print(f"⚠️ {module_name}.{func_name} не найдена")
                failed_count += 1
        except Exception as e:
            print(f"⚠️ {module_name}.{func_name}: {str(e)[:80]}")
            failed_count += 1
    
    print(f"✅ Загружено: {loaded_count}, ошибок: {failed_count}")
    
    # ============================================================
    # 3. ВПЕЧАТЛЕНИЯ
    # ============================================================
    
    try:
        from impression_manager import initialize_impressions
        initialize_impressions()
    except Exception as e:
        print(f"⚠️ initialize_impressions: {e}")
    
    # ============================================================
    # 4. ИСПРАВЛЕНИЕ ОШИБОК
    # ============================================================
    
    try:
        from error_fixer import auto_fix_all
        result = auto_fix_all()
        fixed = result.get('stats', {}).get('fixed_count', 0)
        if fixed > 0:
            print(f"🔧 Исправлено ошибок: {fixed}")
    except Exception as e:
        print(f"⚠️ auto_fix_all: {e}")
    
    # ============================================================
    # 5. БАЗА ДАННЫХ
    # ============================================================
    
    try:
        import database as db
        db.load_all_data()
        print(f"✅ Пользователей: {len(db.user_profiles)}")
    except Exception as e:
        print(f"⚠️ db.load_all_data: {e}")
    
    # ============================================================
    # 6. СТАРТОВЫЕ ОБРАБОТЧИКИ
    # ============================================================
    
    try:
        from handlers_start import register_start_handlers
        register_start_handlers(bot, bot_status)
        print("✅ Обработчики зарегистрированы")
    except Exception as e:
        _log(e, "handlers_start")
    
    # ============================================================
    # 7. ОБУЧЕНИЕ
    # ============================================================
    
    try:
        from learning_manager import init_learning
        init_learning()
    except Exception as e:
        print(f"⚠️ init_learning: {e}")
    
    # ============================================================
    # 8. ИТОГ
    # ============================================================
    
    print("=" * 60)
    print("✅ ВСЕ ДАННЫЕ ЗАГРУЖЕНЫ")
    print("=" * 60)

# ============================================================
# 2. ЗАГРУЗКА
# ============================================================

print("📦 Модуль загрузки данных готов")