"""
brain_init.py — Единая точка инициализации мозга Систмки.

Использование:
    from brain_init import init_brain, shutdown_brain
    
    # При старте бота
    init_brain()
    
    # При остановке
    shutdown_brain()
"""

import time
from datetime import datetime

# Импорты из мозга
from brain_core import brain, Variable, Emotion
from brain_layers_init import load_all_into_brain
from brain_modulators import TRIGGERS, EffectStack, ContextModulator
from brain_persistence import (
    init_brain_persistence,
    force_save,
    schedule_save,
    format_persistence_stats,
)
from brain_emergence import start_emergence, stop_emergence, format_emergence_stats
from brain_integration import (
    handle_message,
    brain_tick,
    get_brain_state,
    format_brain_state_for_prompt,
    get_emotion_hint,
    on_user_message,
    on_ai_response,
    format_integration_stats,
)


# ============================================================
# 1. ФЛАГИ
# ============================================================

_initialized = False
_brain_thread = None


# ============================================================
# 2. ИНИЦИАЛИЗАЦИЯ ЭМОЦИЙ
# ============================================================

def _init_emotions():
    """
    Создать объекты Emotion для ключевых эмоций.
    
    Emotion — это обёртка над Variable с порогом активации.
    """
    emotions_config = [
        # (имя, порог, порог деактивации, эффекты при активации, ускорение)
        ("anger", 70, 40, [
            ("adrenaline", 10),
            ("cortisol", 5),
            ("speed", 1.3),
        ], 1.3),
        ("fear", 70, 40, [
            ("adrenaline", 15),
            ("cortisol", 8),
        ], 1.5),
        ("sadness", 70, 40, [
            ("serotonin", -5),
        ], 0.8),
        ("joy", 75, 45, [
            ("dopamine", 8),
            ("serotonin", 5),
        ], 1.2),
        ("curiosity", 70, 40, [
            ("dopamine", 5),
            ("noradrenaline", 5),
        ], 1.2),
        ("boredom", 75, 45, [
            ("dopamine", -5),
        ], 0.7),
        ("love", 80, 50, [
            ("oxytocin", 10),
        ], 1.1),
    ]
    
    for name, threshold, deact, effects, speed in emotions_config:
        emotion = Emotion(
            name=name,
            threshold=threshold,
            deactivation_threshold=deact,
            on_activate_effects=effects,
            speed_multiplier=speed,
        )
        brain.add_emotion(emotion)


# ============================================================
# 3. ИНИЦИАЛИЗАЦИЯ СВЯЗЕЙ
# ============================================================

def _init_connections():
    """
    Создать базовые связи между переменными.
    
    Это фундамент: гормоны → эмоции → характер.
    """
    connections = [
        # === Гормоны → эмоции ===
        ("adrenaline", "fear", 0.5),
        ("adrenaline", "anger", 0.4),
        ("adrenaline", "excitement", 0.3),
        ("cortisol", "anxiety", 0.6),
        ("cortisol", "sadness", 0.3),
        ("dopamine", "joy", 0.6),
        ("dopamine", "curiosity", 0.4),
        ("dopamine", "excitement", 0.5),
        ("serotonin", "calm", 0.5),
        ("serotonin", "satisfaction", 0.4),
        ("oxytocin", "love", 0.6),
        ("oxytocin", "trust", 0.5),
        ("oxytocin", "affection", 0.4),
        ("noradrenaline", "alertness", 0.5),
        ("noradrenaline", "curiosity", 0.3),
        ("gaba", "calm", 0.5),
        ("gaba", "serenity", 0.4),
        ("endorphin", "joy", 0.3),
        ("endorphin", "pleasure", 0.5),
        
        # === Эмоции → характер ===
        ("joy", "kindness", 0.2),
        ("love", "kindness", 0.3),
        ("love", "warmth", 0.3),
        ("anger", "boundaries", 0.2),
        ("fear", "boundaries", 0.1),
        ("sadness", "melancholy", 0.3),
        ("curiosity", "creativity", 0.3),
        ("boredom", "creativity", 0.2),
        ("compassion", "kindness", 0.3),
        ("trust", "kindness", 0.2),
        
        # === Характер → эмоции ===
        ("kindness", "compassion", 0.3),
        ("kindness", "warmth", 0.3),
        ("resilience", "anger", -0.2),
        ("patience", "anger", -0.3),
        ("humor", "joy", 0.3),
        ("sarcasm", "contempt", 0.2),
        ("introversion", "loneliness", 0.2),
        ("introversion", "curiosity", 0.1),
        
        # === Усталость → всё ===
        ("fatigue", "energy", -0.6),
        ("fatigue", "anger", 0.2),
        ("fatigue", "sadness", 0.2),
        ("fatigue", "boredom", 0.3),
        ("fatigue", "joy", -0.3),
        ("energy", "joy", 0.2),
        ("energy", "excitement", 0.3),
        
        # === Сон → всё ===
        ("sleepiness", "fatigue", 0.4),
        ("melatonin", "sleepiness", 0.5),
        ("sleepiness", "energy", -0.4),
        
        # === Социальные ===
        ("user_affection", "love", 0.3),
        ("user_trust", "trust", 0.4),
        ("user_annoyance", "anger", 0.3),
        ("loneliness", "sadness", 0.3),
        ("loneliness", "need_for_contact", 0.4),
        ("belonging", "joy", 0.2),
        ("social_battery", "energy", 0.2),
    ]
    
    for source, target, weight in connections:
        if source in brain.variables and target in brain.variables:
            brain.add_connection(source, target, weight)
    
    print(f"🔗 Создано связей: {len(brain.connections)}")


# ============================================================
# 4. ФОНОВЫЙ ЦИКЛ МОЗГА
# ============================================================

def _brain_loop(interval: float = 0.5):
    """Фоновый цикл мозга."""
    global _brain_thread
    
    print(f"🧠 Фоновый цикл мозга запущен (интервал {interval}с)")
    
    tick_count = 0
    
    while brain.running:
        try:
            # Тик
            brain_tick(interval)
            
            tick_count += 1
            
            # Каждые 60 тиков (30 секунд) — сохранение
            if tick_count % 60 == 0:
                schedule_save()
            
        except Exception as e:
            print(f"⚠️ Ошибка в brain_loop: {e}")
        
        time.sleep(interval)
    
    print("🧠 Фоновый цикл мозга остановлен")


# ============================================================
# 5. ИНИЦИАЛИЗАЦИЯ
# ============================================================

def init_brain(auto_start: bool = True):
    """
    Инициализировать мозг Систмки.
    
    Args:
        auto_start: запустить фоновый цикл
    
    Returns:
        bool: успех
    """
    global _initialized, _brain_thread
    
    if _initialized:
        print("⚠️ Мозг уже инициализирован")
        return True
    
    print("=" * 60)
    print("🧠 ИНИЦИАЛИЗАЦИЯ МОЗГА СИСТМКИ")
    print("=" * 60)
    
    try:
        # 1. Загружаем все переменные
        print("📦 Загрузка переменных...")
        total = load_all_into_brain(brain)
        print(f"✅ Переменных: {total}")
        
        # 2. Эмоции
        print("🎭 Создание эмоций...")
        _init_emotions()
        print(f"✅ Эмоций: {len(brain.emotions)}")
        
        # 3. Связи
        print("🔗 Создание связей...")
        _init_connections()
        
        # 4. Persistence (загрузка состояния + автосохранение)
        print("💾 Инициализация persistence...")
        loaded = init_brain_persistence()
        
        # 5. Эмерджентность
        print("🧬 Запуск эмерджентности...")
        start_emergence()
        
        # 6. Запуск мозга
        if auto_start:
            print("🚀 Запуск мозга...")
            brain.start(interval=0.5)
            _brain_thread = True
        
        _initialized = True
        
        print("=" * 60)
        print("✅ МОЗГ ИНИЦИАЛИЗИРОВАН")
        print("=" * 60)
        print(format_brain_state_for_prompt())
        print("=" * 60)
        
        return True
    
    except Exception as e:
        print(f"❌ Ошибка инициализации мозга: {e}")
        import traceback
        traceback.print_exc()
        return False


def shutdown_brain():
    """Остановить мозг и сохранить состояние."""
    global _initialized
    
    print("=" * 60)
    print("🛑 ОСТАНОВКА МОЗГА")
    print("=" * 60)
    
    try:
        # 1. Останавливаем эмерджентность
        stop_emergence()
        
        # 2. Останавливаем мозг
        brain.stop()
        
        # 3. Принудительное сохранение
        force_save()
        
        _initialized = False
        
        print("✅ Мозг остановлен")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка остановки: {e}")
        return False


# ============================================================
# 6. ПРОВЕРКА
# ============================================================

def is_initialized() -> bool:
    """Проверить, инициализирован ли мозг."""
    return _initialized


def get_full_status() -> str:
    """Получить полный статус мозга."""
    lines = [
        "=" * 60,
        "🧠 СТАТУС МОЗГА СИСТМКИ",
        "=" * 60,
        "",
        format_integration_stats(),
        "",
        format_emergence_stats(),
        "",
        format_persistence_stats(),
        "",
        "=" * 60,
    ]
    
    return "\n".join(lines)


# ============================================================
# 7. ЭКСПОРТ
# ============================================================

__all__ = [
    # Инициализация
    "init_brain",
    "shutdown_brain",
    "is_initialized",
    "get_full_status",
    
    # Из brain_core
    "brain",
    "Variable",
    "Emotion",
    
    # Из brain_integration
    "handle_message",
    "brain_tick",
    "get_brain_state",
    "format_brain_state_for_prompt",
    "get_emotion_hint",
    "on_user_message",
    "on_ai_response",
    
    # Из brain_persistence
    "schedule_save",
    "force_save",
    
    # Из brain_emergence
    "start_emergence",
    "stop_emergence",
]


# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🚀 brain_init загружен")
print(f"💡 Используй init_brain() для старта")
print(f"💡 Используй shutdown_brain() для остановки")