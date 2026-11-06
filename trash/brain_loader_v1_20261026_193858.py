"""
brain_loader.py — загрузка всех переменных в мозг.

Использование:
    from brain_loader import load_brain
    load_brain()
"""

from brain_core import brain
from brain_layers_init import load_all_into_brain


def load_brain():
    """Загрузить все переменные в глобальный мозг."""
    print("🧠 Загрузка мозга Систмки...")
    total = load_all_into_brain(brain)
    print(f"✅ Мозг загружен: {total} переменных")
    return brain


def start_brain(interval=0.5):
    """Загрузить и запустить мозг."""
    load_brain()
    brain.start(interval)
    return brain