"""
brain_emergence.py — Эмерджентность мозга.

Мозг создаёт новые связи и новые переменные.
"""

import time
import random
import math
import threading
from datetime import datetime
from typing import List, Tuple, Dict, Optional

from brain_core import brain, Variable, Connection


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

CORRELATION_THRESHOLD = 0.7
MIN_OBSERVATIONS = 50
PATTERN_THRESHOLD = 20
MAX_EMERGENT_VARIABLES = 200
EMERGENCE_INTERVAL = 300
HISTORY_SIZE = 100


# ============================================================
# 2. ИСТОРИЯ ЗНАЧЕНИЙ
# ============================================================

class ValueHistory:
    def __init__(self, max_size=HISTORY_SIZE):
        self.values: List[float] = []
        self.max_size = max_size
    
    def add(self, value: float):
        self.values.append(value)
        if len(self.values) > self.max_size:
            self.values = self.values[-self.max_size:]
    
    def get(self) -> List[float]:
        return self.values
    
    def has_enough(self, min_count=MIN_OBSERVATIONS) -> bool:
        return len(self.values) >= min_count


_value_history: Dict[str, ValueHistory] = {}


def record_values():
    """Записать текущие значения всех переменных."""
    for name, var in brain.variables.items():
        if name not in _value_history:
            _value_history[name] = ValueHistory()
        _value_history[name].add(var.value)


# ============================================================
# 3. КОРРЕЛЯЦИЯ
# ============================================================

def compute_correlation(x: List[float], y: List[float]) -> float:
    """Вычислить корреляцию Пирсона."""
    n = min(len(x), len(y))
    if n < 10:
        return 0.0
    
    x = x[-n:]
    y = y[-n:]
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    var_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    var_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    denominator = math.sqrt(var_x * var_y)
    
    if denominator < 1e-10:
        return 0.0
    
    return numerator / denominator


def detect_correlations():
    """Найти пары с высокой корреляцией."""
    correlations = []
    
    names = [n for n, h in _value_history.items() if h.has_enough()]
    if len(names) < 2:
        return correlations
    
    names = names[:50]
    
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]
            
            if brain.has_connection(name_a, name_b):
                continue
            if brain.has_connection(name_b, name_a):
                continue
            
            hist_a = _value_history[name_a].get()
            hist_b = _value_history[name_b].get()
            
            corr = compute_correlation(hist_a, hist_b)
            
            if abs(corr) >= CORRELATION_THRESHOLD:
                correlations.append((name_a, name_b, corr))
    
    return correlations


# ============================================================
# 4. СОЗДАНИЕ СВЯЗЕЙ
# ============================================================

def create_connections_from_correlations():
    """Создать новые связи на основе корреляций."""
    correlations = detect_correlations()
    created = 0
    
    for name_a, name_b, corr in correlations:
        if corr > 0:
            brain.add_connection(name_a, name_b, weight=abs(corr) * 0.5)
            created += 1
        else:
            brain.add_connection(name_a, name_b, weight=-abs(corr) * 0.5)
            created += 1
        
        print(f"🔗 Новая связь: {name_a} → {name_b} ({corr:.2f})")
    
    return created


# ============================================================
# 5. ПАТТЕРНЫ
# ============================================================

class PatternDetector:
    def __init__(self):
        self.patterns: Dict[Tuple[str, ...], int] = {}
    
    def record(self):
        active = tuple(sorted([
            name for name, var in brain.variables.items()
            if var.value > 70 and "emotion" in var.tags
        ]))
        
        if len(active) < 2:
            return
        
        if len(active) > 5:
            active = active[:5]
        
        self.patterns[active] = self.patterns.get(active, 0) + 1
    
    def get_frequent_patterns(self, threshold=PATTERN_THRESHOLD):
        return [
            (pattern, count)
            for pattern, count in self.patterns.items()
            if count >= threshold
        ]


_pattern_detector = PatternDetector()


# ============================================================
# 6. СОЗДАНИЕ ПЕРЕМЕННЫХ
# ============================================================

def create_variable_from_pattern(pattern: Tuple[str, ...], count: int) -> Optional[Variable]:
    """Создать новую переменную из паттерна."""
    emergent_count = sum(
        1 for name in brain.variables
        if name.startswith("emergent_")
    )
    
    if emergent_count >= MAX_EMERGENT_VARIABLES:
        return None
    
    pattern_str = "_".join(p.replace("emergent_", "") for p in pattern)
    new_name = f"emergent_{pattern_str}"[:50]
    
    if new_name in brain.variables:
        return None
    
    new_var = Variable(
        name=new_name,
        level="medium",
        base=50,
        volatility=1.0,
        tags=["emergent", "pattern"],
    )
    
    for p in pattern:
        brain.add_connection(p, new_name, weight=0.4)
    
    brain.add_variable(new_var)
    
    print(f"✨ Новая переменная: {new_name} (из паттерна {pattern}, частота {count})")
    
    return new_var


def create_variables_from_patterns():
    """Создать переменные из частых паттернов."""
    created = 0
    for pattern, count in _pattern_detector.get_frequent_patterns():
        var = create_variable_from_pattern(pattern, count)
        if var:
            created += 1
    return created


# ============================================================
# 7. РАЗВИТИЕ ХАРАКТЕРА
# ============================================================

def develop_character_from_events():
    """Развивать черты характера."""
    for name, var in brain.variables.items():
        if "character" not in var.tags:
            continue
        
        if var.long_term > 70 and var.update_count > 100:
            if var.value < var.max_val:
                var.value += 0.1
                var.long_term += 0.1
        elif var.long_term < 30 and var.update_count > 100:
            if var.value > var.min_val:
                var.value -= 0.1
                var.long_term -= 0.1


# ============================================================
# 8. ГЛАВНЫЙ ЦИКЛ
# ============================================================

_emergence_running = False


def _emergence_loop():
    """Фоновый цикл эмерджентности."""
    global _emergence_running
    
    tick = 0
    
    while _emergence_running:
        time.sleep(10)
        
        try:
            record_values()
            _pattern_detector.record()
            
            tick += 1
            
            if tick * 10 >= EMERGENCE_INTERVAL:
                tick = 0
                
                print("🧬 Цикл эмерджентности...")
                
                new_conn = create_connections_from_correlations()
                if new_conn:
                    print(f"🔗 Создано связей: {new_conn}")
                
                new_vars = create_variables_from_patterns()
                if new_vars:
                    print(f"✨ Создано переменных: {new_vars}")
                
                develop_character_from_events()
        
        except Exception as e:
            print(f"⚠️ Ошибка в emergence_loop: {e}")


def start_emergence():
    """Запустить цикл эмерджентности."""
    global _emergence_running
    
    if _emergence_running:
        return
    
    _emergence_running = True
    thread = threading.Thread(target=_emergence_loop, daemon=True, name="brain_emergence")
    thread.start()
    print(f"🧬 Эмерджентность запущена (интервал {EMERGENCE_INTERVAL}с)")


def stop_emergence():
    """Остановить цикл."""
    global _emergence_running
    _emergence_running = False


# ============================================================
# 9. СТАТИСТИКА
# ============================================================

def get_emergence_stats():
    """Статистика эмерджентности."""
    emergent_vars = [
        name for name in brain.variables
        if name.startswith("emergent_")
    ]
    
    return {
        "total_variables": len(brain.variables),
        "emergent_variables": len(emergent_vars),
        "total_connections": len(brain.connections),
        "patterns_detected": len(_pattern_detector.patterns),
        "frequent_patterns": len(_pattern_detector.get_frequent_patterns()),
        "history_size": len(_value_history),
    }


def format_emergence_stats():
    """Форматировать статистику."""
    stats = get_emergence_stats()
    
    lines = [
        "🧬 ЭМЕРДЖЕНТНОСТЬ:",
        f"  📊 Всего переменных: {stats['total_variables']}",
        f"  ✨ Эмерджентных: {stats['emergent_variables']}",
        f"  🔗 Связей: {stats['total_connections']}",
        f"  🎯 Паттернов: {stats['patterns_detected']}",
        f"  🔥 Частых паттернов: {stats['frequent_patterns']}",
        f"  📜 Историй: {stats['history_size']}",
    ]
    
    return "\n".join(lines)


# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("🧬 brain_emergence загружен")
print(f"🔗 Порог корреляции: {CORRELATION_THRESHOLD}")
print(f"🎯 Порог паттерна: {PATTERN_THRESHOLD}")
print(f"📊 Макс. эмерджентных: {MAX_EMERGENT_VARIABLES}")
print(f"⏱ Интервал: {EMERGENCE_INTERVAL}с")