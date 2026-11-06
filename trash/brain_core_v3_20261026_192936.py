"""
brain_core.py — Ядро мозга Систмки

Содержит:
- Variable (переменная с instant/short_term/long_term/trauma/momentum)
- Emotion (эмоция с активацией)
- Connection (связь с весом, Hebbian learning)
- Brain (главный контейнер)
- speed_multiplier (глобальный ускоритель)

НЕ ЗАВИСИТ от consciousness.py — наоборот, consciousness будет читать отсюда.
"""

import time
import math
import random
import threading
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================
# 1. КОНСТАНТЫ
# ============================================================

MIN_VALUE = 0.0
MAX_VALUE = 100.0
BASE_VALUE = 50.0

# Уровни тиков (секунды)
TICK_LEVELS = {
    "fast": (0.5, 2.0),
    "medium": (5.0, 15.0),
    "slow": (60.0, 300.0),
    "circadian": (3600.0, 86400.0),
}


# ============================================================
# 2. VARIABLE — ПЕРЕМЕННАЯ МОЗГА
# ============================================================

@dataclass
class Variable:
    """
    Переменная мозга.
    
    instant — мгновенное значение
    short_term — среднее за минуты
    long_term — накопленное за дни
    trauma — след от сильных событий (затухает медленно)
    momentum — инерция (куда движется)
    """
    
    name: str
    level: str = "medium"  # fast / medium / slow / circadian
    base: float = BASE_VALUE
    value: float = BASE_VALUE  # это instant
    min_val: float = MIN_VALUE
    max_val: float = MAX_VALUE
    volatility: float = 1.0
    decay: float = 0.01  # возврат к базе
    tags: List[str] = field(default_factory=list)
    
    # Следы
    short_term: float = BASE_VALUE
    long_term: float = BASE_VALUE
    trauma: float = 0.0
    momentum: float = 0.0
    
    # Таймер
    last_update: float = field(default_factory=time.time)
    next_update: float = 0.0
    
    # Зависимости (заполняются в brain_modulators)
    influences: List[Tuple[str, float]] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # Статистика
    update_count: int = 0
    last_delta: float = 0.0
    
    def __post_init__(self):
        if self.next_update == 0.0:
            self.next_update = self.last_update + self.compute_interval()
    
    def compute_interval(self) -> float:
        """Вычислить интервал до следующего обновления."""
        lo, hi = TICK_LEVELS.get(self.level, TICK_LEVELS["medium"])
        base_interval = random.uniform(lo, hi)
        
        # Чем дальше от базы — тем чаще (переменная «беспокоится»)
        distance = abs(self.value - self.base) / max(1, self.max_val - self.min_val)
        base_interval *= (1 - distance * 0.5)
        
        # Jitter
        base_interval *= random.uniform(0.8, 1.2)
        
        return max(0.1, base_interval)
    
    def should_update(self, now: float) -> bool:
        return now >= self.next_update
    
    def update(self, dt: float, all_vars: Dict[str, 'Variable'], speed: float):
        """Обновить переменную."""
        old = self.value
        
        # 1. Случайное изменение
        delta = random.uniform(-self.volatility, self.volatility) * dt
        
        # 2. Влияние других переменных
        for other_name, weight in self.influences:
            other = all_vars.get(other_name)
            if other:
                delta += (other.value - BASE_VALUE) * weight * 0.01 * dt
        
        # 3. Возврат к базе
        delta += (self.base - self.value) * self.decay * dt
        
        # 4. Инерция
        delta += self.momentum * 0.1 * dt
        
        # 5. Применение
        self.value = max(self.min_val, min(self.max_val, self.value + delta * speed))
        
        # 6. Обновление следов
        self.momentum = self.momentum * (1 - 0.05 * dt) + delta * 0.2
        self.short_term += (self.value - self.short_term) * dt * 0.1
        self.long_term += (self.short_term - self.long_term) * dt * 0.01
        self.trauma *= (1 - dt * 0.001)
        
        # 7. Статистика
        self.last_delta = self.value - old
        self.update_count += 1
        self.last_update = time.time()
        self.next_update = self.last_update + self.compute_interval()
    
    def apply_impulse(self, amount: float, duration: float = 1.0):
        """
        Применить импульс (событие).
        
        amount — сила
        duration — сколько секунд действует
        """
        # Модуляция следами
        modifier = 1.0
        
        # Если эмоция и так высокая — новые события слабее
        if self.long_term > 70:
            modifier *= 0.5
        elif self.long_term < 30:
            modifier *= 1.5
        
        # Травма усиливает реакцию
        if self.trauma > 50:
            modifier *= 1.5
        
        final = amount * modifier
        
        self.value = max(self.min_val, min(self.max_val, self.value + final))
        self.momentum += final * 0.2
        
        # Сильное событие оставляет травму
        if abs(final) > 20:
            self.trauma = min(100, self.trauma + abs(final) * 0.5)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "value": round(self.value, 2),
            "short_term": round(self.short_term, 2),
            "long_term": round(self.long_term, 2),
            "trauma": round(self.trauma, 2),
            "momentum": round(self.momentum, 2),
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Variable':
        v = cls(
            name=data["name"],
            level=data.get("level", "medium"),
            value=data.get("value", BASE_VALUE),
            short_term=data.get("short_term", BASE_VALUE),
            long_term=data.get("long_term", BASE_VALUE),
            trauma=data.get("trauma", 0.0),
            momentum=data.get("momentum", 0.0),
            tags=data.get("tags", []),
        )
        return v


# ============================================================
# 3. EMOTION — АКТИВНАЯ ЭМОЦИЯ
# ============================================================

@dataclass
class Emotion:
    """
    Эмоция — это переменная + порог активации.
    
    Когда value > threshold — эмоция активна.
    Активная эмоция влияет на speed_multiplier и другие переменные.
    """
    
    name: str
    threshold: float = 60.0
    deactivation_threshold: float = 30.0  # гистерезис
    active: bool = False
    
    # Что делает при активации (список (target, weight))
    on_activate_effects: List[Tuple[str, float]] = field(default_factory=list)
    on_deactivate_effects: List[Tuple[str, float]] = field(default_factory=list)
    
    # Ускорение мозга
    speed_multiplier: float = 1.0
    
    # Переменные, которые заставляют обновляться
    force_update_tags: List[str] = field(default_factory=list)
    
    # Статистика
    activation_count: int = 0
    last_activated: Optional[float] = None
    
    def check(self, value: float, brain) -> Optional[str]:
        """
        Проверить активацию.
        
        Returns:
            "activated" / "deactivated" / None
        """
        if not self.active and value >= self.threshold:
            self.active = True
            self.activation_count += 1
            self.last_activated = time.time()
            return "activated"
        
        if self.active and value <= self.deactivation_threshold:
            self.active = False
            return "deactivated"
        
        return None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "threshold": self.threshold,
            "active": self.active,
            "activation_count": self.activation_count,
            "last_activated": self.last_activated,
        }


# ============================================================
# 4. CONNECTION — СВЯЗЬ МЕЖДУ ПЕРЕМЕННЫМИ
# ============================================================

@dataclass
class Connection:
    """
    Связь между переменными.
    
    Hebbian learning: «fire together, wire together».
    """
    
    source: str
    target: str
    weight: float = 0.3
    usage_count: int = 0
    last_used: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    
    def use(self, amount: float = 1.0):
        """Использовать связь — усилить."""
        self.usage_count += 1
        self.last_used = time.time()
        self.weight += 0.01 * amount * (1 - self.weight)
        self.weight = min(1.0, self.weight)
    
    def decay(self, dt: float):
        """Затухание неиспользуемых связей."""
        time_since = time.time() - self.last_used
        if time_since > 3600:  # час без использования
            self.weight *= (1 - dt * 0.001)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "weight": round(self.weight, 3),
            "usage_count": self.usage_count,
        }


# ============================================================
# 5. BRAIN — ГЛАВНЫЙ КОНТЕЙНЕР
# ============================================================

class Brain:
    """
    Мозг Систмки.
    
    Содержит все переменные, эмоции, связи.
    Работает всегда — loop в отдельном потоке.
    """
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.emotions: Dict[str, Emotion] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        
        self.speed_multiplier: float = 1.0
        self.running: bool = False
        self._lock = threading.RLock()
        
        self.stats = {
            "total_updates": 0,
            "total_impulses": 0,
            "started_at": datetime.now().isoformat(),
            "last_update": None,
        }
    
    # ============================================================
    # 5.1 УПРАВЛЕНИЕ ПЕРЕМЕННЫМИ
    # ============================================================
    
    def add_variable(self, var: Variable):
        """Добавить переменную."""
        with self._lock:
            self.variables[var.name] = var
    
    def get_variable(self, name: str) -> Optional[Variable]:
        return self.variables.get(name)
    
    def get_value(self, name: str, default: float = BASE_VALUE) -> float:
        var = self.variables.get(name)
        return var.value if var else default
    
    def set_value(self, name: str, value: float):
        var = self.variables.get(name)
        if var:
            var.value = max(var.min_val, min(var.max_val, value))
    
    def impulse(self, name: str, amount: float, duration: float = 1.0):
        """Применить импульс к переменной."""
        var = self.variables.get(name)
        if var:
            var.apply_impulse(amount, duration)
            self.stats["total_impulses"] += 1
    
    def impulse_many(self, impulses: List[Tuple[str, float]]):
        """Применить несколько импульсов."""
        for name, amount in impulses:
            self.impulse(name, amount)
    
    # ============================================================
    # 5.2 УПРАВЛЕНИЕ ЭМОЦИЯМИ
    # ============================================================
    
    def add_emotion(self, emotion: Emotion):
        with self._lock:
            self.emotions[emotion.name] = emotion
    
    def get_emotion(self, name: str) -> Optional[Emotion]:
        return self.emotions.get(name)
    
    def is_emotion_active(self, name: str) -> bool:
        emotion = self.emotions.get(name)
        return emotion.active if emotion else False
    
    # ============================================================
    # 5.3 УПРАВЛЕНИЕ СВЯЗЯМИ
    # ============================================================
    
    def add_connection(self, source: str, target: str, weight: float = 0.3):
        """Добавить связь."""
        key = (source, target)
        if key not in self.connections:
            self.connections[key] = Connection(source, target, weight)
        else:
            self.connections[key].weight = weight
    
    def get_connection(self, source: str, target: str) -> Optional[Connection]:
        return self.connections.get((source, target))
    
    def use_connection(self, source: str, target: str):
        conn = self.get_connection(source, target)
        if conn:
            conn.use()
    
    def has_connection(self, source: str, target: str) -> bool:
        return (source, target) in self.connections
    
    # ============================================================
    # 5.4 SPEED MULTIPLIER
    # ============================================================
    
    def compute_speed_multiplier(self) -> float:
        """
        Вычислить глобальный ускоритель.
        
        Зависит от:
        - адреналина (ускоряет)
        - кортизола (ускоряет)
        - дофамина (ускоряет)
        - усталости (замедляет)
        """
        adrenaline = self.get_value("adrenaline")
        cortisol = self.get_value("cortisol")
        dopamine = self.get_value("dopamine")
        fatigue = self.get_value("fatigue")
        
        arousal = (adrenaline + cortisol + dopamine) / 3
        speed = 1.0 + (arousal - 50) / 100
        speed *= (1 - fatigue / 200)
        
        return max(0.3, min(3.0, speed))
    
    # ============================================================
    # 5.5 ГЛАВНЫЙ ТИК
    # ============================================================
    
    def tick(self, dt: float = 1.0):
        """
        Один тик мозга.
        
        Обновляет:
        1. speed_multiplier
        2. эмоции (активация)
        3. переменные (только те, чьё время пришло)
        4. связи (затухание)
        """
        with self._lock:
            now = time.time()
            
            # 1. speed_multiplier
            self.speed_multiplier = self.compute_speed_multiplier()
            
            # 2. Эмоции
            for emotion in self.emotions.values():
                var = self.variables.get(emotion.name)
                if var:
                    result = emotion.check(var.value, self)
                    
                    if result == "activated":
                        # Применяем эффекты
                        for target, amount in emotion.on_activate_effects:
                            self.impulse(target, amount)
                        
                        # Ускоряем мозг
                        self.speed_multiplier *= emotion.speed_multiplier
                        
                        # Заставляем обновиться переменные с нужными тегами
                        if emotion.force_update_tags:
                            for v in self.variables.values():
                                if any(tag in v.tags for tag in emotion.force_update_tags):
                                    v.next_update = now
                    
                    elif result == "deactivated":
                        for target, amount in emotion.on_deactivate_effects:
                            self.impulse(target, amount)
            
            # 3. Переменные
            for var in self.variables.values():
                if var.should_update(now):
                    var.update(dt, self.variables, self.speed_multiplier)
                    self.stats["total_updates"] += 1
            
            # 4. Связи (затухание)
            for conn in self.connections.values():
                conn.decay(dt)
            
            self.stats["last_update"] = datetime.now().isoformat()
    
    # ============================================================
    # 5.6 ФОНОВЫЙ ЦИКЛ
    # ============================================================
    
    def start(self, interval: float = 0.5):
        """Запустить мозг в фоновом потоке."""
        if self.running:
            return
        
        self.running = True
        thread = threading.Thread(target=self._loop, args=(interval,), daemon=True)
        thread.start()
        print(f"🧠 Мозг запущен (интервал: {interval}с)")
    
    def stop(self):
        self.running = False
    
    def _loop(self, interval: float):
        while self.running:
            try:
                self.tick(interval)
            except Exception as e:
                print(f"⚠️ Ошибка в мозге: {e}")
            time.sleep(interval)
    
    # ============================================================
    # 5.7 СЕРИАЛИЗАЦИЯ
    # ============================================================
    
    def to_dict(self) -> dict:
        with self._lock:
            return {
                "variables": {
                    name: var.to_dict()
                    for name, var in self.variables.items()
                },
                "emotions": {
                    name: emo.to_dict()
                    for name, emo in self.emotions.items()
                },
                "connections": [
                    conn.to_dict()
                    for conn in self.connections.values()
                ],
                "speed_multiplier": round(self.speed_multiplier, 3),
                "stats": self.stats.copy(),
            }
    
    def load_from_dict(self, data: dict):
        """Загрузить состояние."""
        with self._lock:
            for name, var_data in data.get("variables", {}).items():
                if name in self.variables:
                    self.variables[name].value = var_data.get("value", BASE_VALUE)
                    self.variables[name].short_term = var_data.get("short_term", BASE_VALUE)
                    self.variables[name].long_term = var_data.get("long_term", BASE_VALUE)
                    self.variables[name].trauma = var_data.get("trauma", 0.0)
                    self.variables[name].momentum = var_data.get("momentum", 0.0)
            
            for name, emo_data in data.get("emotions", {}).items():
                if name in self.emotions:
                    self.emotions[name].active = emo_data.get("active", False)
                    self.emotions[name].activation_count = emo_data.get("activation_count", 0)
            
            self.stats.update(data.get("stats", {}))
    
    # ============================================================
    # 5.8 СТАТИСТИКА
    # ============================================================
    
    def get_state_summary(self) -> str:
        """Краткая сводка состояния."""
        lines = ["🧠 СОСТОЯНИЕ МОЗГА:"]
        lines.append(f"  Переменных: {len(self.variables)}")
        lines.append(f"  Эмоций: {len(self.emotions)}")
        lines.append(f"  Связей: {len(self.connections)}")
        lines.append(f"  Скорость: {self.speed_multiplier:.2f}x")
        
        active_emotions = [e.name for e in self.emotions.values() if e.active]
        if active_emotions:
            lines.append(f"  Активные эмоции: {', '.join(active_emotions)}")
        
        return "\n".join(lines)


# ============================================================
# 6. ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================

brain = Brain()


# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("🧠 brain_core загружен")
print(f"📦 Готов к добавлению переменных")
print(f"💡 Используй brain.add_variable(Variable(...))")