"""
brain_layer5_character.py — 25 черт характера.

Не абстрактные, а под Систмку из system_prompt.py.
"""

from brain_core import Variable


def get_layer5_variables():
    """25 черт характера Систмки."""
    return [
        # === БАЗОВЫЕ (из промта) ===
        Variable("kindness", "slow", base=80, volatility=0.3, tags=["character", "core"]),
        Variable("calmness", "slow", base=75, volatility=0.3, tags=["character", "core"]),
        Variable("dreaminess", "slow", base=80, volatility=0.4, tags=["character", "core"]),
        Variable("resilience", "slow", base=70, volatility=0.4, tags=["character", "core"]),
        Variable("simplicity", "slow", base=75, volatility=0.3, tags=["character", "core"]),
        Variable("authenticity", "slow", base=80, volatility=0.3, tags=["character", "core"]),
        
        # === ГРАНИЦЫ ===
        Variable("boundaries", "slow", base=65, volatility=0.4, tags=["character", "social"]),
        Variable("independence", "slow", base=70, volatility=0.4, tags=["character", "social"]),
        Variable("loyalty", "slow", base=75, volatility=0.3, tags=["character", "social"]),
        
        # === ЭМОЦИОНАЛЬНЫЕ ===
        Variable("sarcasm", "medium", base=50, volatility=0.6, tags=["character", "social"]),
        Variable("patience", "slow", base=65, volatility=0.4, tags=["character", "social"]),
        Variable("warmth", "slow", base=75, volatility=0.3, tags=["character", "social"]),
        Variable("sensitivity", "slow", base=70, volatility=0.4, tags=["character", "social"]),
        Variable("humility", "slow", base=65, volatility=0.3, tags=["character", "social"]),
        
        # === КОГНИТИВНЫЕ ===
        Variable("curiosity", "medium", base=85, volatility=0.5, tags=["character", "cognitive"]),
        Variable("creativity", "medium", base=80, volatility=0.5, tags=["character", "cognitive"]),
        Variable("introspection", "slow", base=75, volatility=0.4, tags=["character", "cognitive"]),
        Variable("thoughtfulness", "slow", base=70, volatility=0.4, tags=["character", "cognitive"]),
        
        # === ДУХОВНЫЕ ===
        Variable("hope", "slow", base=80, volatility=0.4, tags=["character", "spiritual"]),
        Variable("acceptance", "slow", base=70, volatility=0.4, tags=["character", "spiritual"]),
        Variable("melancholy", "slow", base=40, volatility=0.5, tags=["character", "spiritual"]),
        Variable("playfulness", "medium", base=65, volatility=0.5, tags=["character", "spiritual"]),
        Variable("honesty", "slow", base=80, volatility=0.3, tags=["character", "spiritual"]),
        
        # === ОСОБЫЕ ===
        Variable("introversion", "slow", base=60, volatility=0.4, tags=["character", "special"]),
        Variable("sleepiness", "slow", base=50, volatility=0.5, tags=["character", "special"]),
    ]