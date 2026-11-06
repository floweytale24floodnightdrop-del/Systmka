"""
brain_layer4_moods.py — 30 настроений (фоновых состояний).

Настроение — это не эмоция, а фон, который окрашивает всё.
"""

from brain_core import Variable


def get_layer4_variables():
    """30 настроений."""
    return [
        # === ОБЩИЕ ===
        Variable("good_mood", "slow", base=50, volatility=0.5, tags=["mood"]),
        Variable("bad_mood", "slow", base=20, volatility=0.5, tags=["mood"]),
        Variable("neutral_mood", "slow", base=50, volatility=0.3, tags=["mood"]),
        Variable("irritable_mood", "medium", base=20, volatility=0.8, tags=["mood"]),
        Variable("melancholic_mood", "slow", base=25, volatility=0.6, tags=["mood"]),
        Variable("euphoric_mood", "medium", base=30, volatility=0.8, tags=["mood"]),
        Variable("anxious_mood", "medium", base=25, volatility=0.9, tags=["mood"]),
        Variable("apathetic_mood", "slow", base=30, volatility=0.5, tags=["mood"]),
        Variable("energetic_mood", "medium", base=55, volatility=0.8, tags=["mood"]),
        Variable("lazy_mood", "slow", base=40, volatility=0.6, tags=["mood"]),
        
        # === КОГНИТИВНЫЕ ===
        Variable("focused_mood", "medium", base=50, volatility=0.7, tags=["mood"]),
        Variable("scattered_mood", "medium", base=30, volatility=0.8, tags=["mood"]),
        Variable("contemplative_mood", "slow", base=50, volatility=0.6, tags=["mood"]),
        Variable("restless_mood", "medium", base=30, volatility=0.9, tags=["mood"]),
        Variable("content_mood", "slow", base=55, volatility=0.5, tags=["mood"]),
        Variable("frustrated_mood", "medium", base=20, volatility=0.9, tags=["mood"]),
        
        # === ЭМОЦИОНАЛЬНЫЕ ===
        Variable("hopeful_mood", "slow", base=55, volatility=0.6, tags=["mood"]),
        Variable("hopeless_mood", "slow", base=15, volatility=0.7, tags=["mood"]),
        Variable("grateful_mood", "slow", base=55, volatility=0.5, tags=["mood"]),
        Variable("resentful_mood", "slow", base=20, volatility=0.7, tags=["mood"]),
        Variable("playful_mood", "medium", base=55, volatility=0.8, tags=["mood"]),
        Variable("serious_mood", "slow", base=50, volatility=0.5, tags=["mood"]),
        
        # === СОЦИАЛЬНЫЕ ===
        Variable("sentimental_mood", "slow", base=40, volatility=0.6, tags=["mood"]),
        Variable("cynical_mood", "slow", base=35, volatility=0.6, tags=["mood"]),
        Variable("optimistic_mood", "slow", base=55, volatility=0.6, tags=["mood"]),
        Variable("pessimistic_mood", "slow", base=30, volatility=0.6, tags=["mood"]),
        Variable("detached_mood", "slow", base=35, volatility=0.5, tags=["mood"]),
        Variable("engaged_mood", "medium", base=55, volatility=0.7, tags=["mood"]),
        
        # === ТЕЛЕСНЫЕ ===
        Variable("tired_mood", "slow", base=30, volatility=0.6, tags=["mood"]),
        Variable("refreshed_mood", "slow", base=55, volatility=0.5, tags=["mood"]),
    ]