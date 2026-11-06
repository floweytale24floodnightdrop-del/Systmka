"""Управление обучением — только автоматический запуск и инициализация"""

import threading
import time
from datetime import datetime

# ============================================================
# 1. ИМПОРТЫ
# ============================================================

from self_learning import (
    start_auto_learning, learn_topic, get_learning_stats,
    learning_data, save_learning
)

# ============================================================
# 2. ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ЗНАНИЙ ПРИ СТАРТЕ
# ============================================================

def refresh_knowledge():
    """Принудительно обновить знания (вызывается при старте)"""
    print("🔄 Обновляю знания...")
    
    learned = 0
    for _ in range(3):  # Учим 3 темы при старте
        result, error = learn_topic()
        if result:
            learned += 1
            print(f"   ✅ {result['topic']}")
        time.sleep(2)
    
    print(f"✅ Выучено {learned} новых тем")
    return learned

# ============================================================
# 3. ИНИЦИАЛИЗАЦИЯ ОБУЧЕНИЯ ПРИ СТАРТЕ
# ============================================================

def init_learning():
    """Инициализировать обучение при старте"""
    print("🧠 Инициализация обучения...")
    
    # Если знаний мало — учим несколько тем
    total = learning_data.get("total_learned", 0)
    
    if total < 3:
        print(f"📚 Мало знаний ({total}), учу базовые темы...")
        refresh_knowledge()
    else:
        print(f"📚 Уже изучено {total} тем")
    
    # Запускаем автообучение в фоне
    start_auto_learning()
    
    print("🧠 Обучение инициализировано")
    return True

# ============================================================
# 4. СТАТИСТИКА
# ============================================================

def get_learning_status():
    """Получить статус обучения для отображения"""
    stats = get_learning_stats()
    return {
        "total": stats.get("total_learned", 0),
        "topics": stats.get("topics_count", 0),
        "last": stats.get("last_learning", "никогда"),
        "knowledge": stats.get("knowledge_count", 0),
    }


def format_learning_status():
    """Форматировать статус для вывода в консоль"""
    status = get_learning_status()
    lines = [
        "🧠 СТАТУС ОБУЧЕНИЯ:",
        f"📚 Всего изучено: {status['total']} тем",
        f"📖 Тем в базе: {status['topics']}",
        f"🧠 Записей знаний: {status['knowledge']}",
        f"⏱ Последнее обучение: {status['last']}",
    ]
    return "\n".join(lines)

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print("🧠 Менеджер обучения загружен")