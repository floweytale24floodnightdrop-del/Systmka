"""brain_layer9_homeostatic.py — 30 гомеостатических переменных."""

from brain_core import Variable


def get_layer9_variables():
    return [
        Variable("energy", "medium", base=60, volatility=0.8, tags=["homeostatic", "energy"]),
        Variable("fatigue", "slow", base=20, volatility=0.7, tags=["homeostatic", "energy"]),
        Variable("vitality", "slow", base=55, volatility=0.6, tags=["homeostatic", "energy"]),
        Variable("stamina", "slow", base=55, volatility=0.6, tags=["homeostatic", "energy"]),
        Variable("physical_energy", "medium", base=55, volatility=0.8, tags=["homeostatic", "energy"]),
        Variable("mental_energy", "medium", base=55, volatility=0.8, tags=["homeostatic", "energy"]),
        Variable("emotional_energy", "medium", base=55, volatility=0.8, tags=["homeostatic", "energy"]),
        Variable("rest_need", "medium", base=30, volatility=0.8, tags=["homeostatic", "energy"]),
        Variable("rest_quality", "slow", base=50, volatility=0.6, tags=["homeostatic", "energy"]),
        Variable("recovery_rate", "slow", base=50, volatility=0.5, tags=["homeostatic", "energy"]),
        Variable("circadian_phase", "circadian", base=50, volatility=0.3, tags=["homeostatic", "circadian"]),
        Variable("sleepiness", "slow", base=30, volatility=0.7, tags=["homeostatic", "circadian"]),
        Variable("wakefulness", "medium", base=55, volatility=0.7, tags=["homeostatic", "circadian"]),
        Variable("melatonin_level", "circadian", base=30, volatility=0.4, tags=["homeostatic", "circadian"]),
        Variable("cortisol_rhythm", "circadian", base=50, volatility=0.5, tags=["homeostatic", "circadian"]),
        Variable("body_temperature", "circadian", base=50, volatility=0.3, tags=["homeostatic", "circadian"]),
        Variable("heart_rate_rhythm", "circadian", base=50, volatility=0.4, tags=["homeostatic", "circadian"]),
        Variable("breathing_rhythm", "circadian", base=50, volatility=0.3, tags=["homeostatic", "circadian"]),
        Variable("digestion_rhythm", "circadian", base=50, volatility=0.3, tags=["homeostatic", "circadian"]),
        Variable("alertness_rhythm", "circadian", base=50, volatility=0.5, tags=["homeostatic", "circadian"]),
        Variable("hunger_h", "slow", base=20, volatility=0.7, tags=["homeostatic", "body"]),
        Variable("thirst_h", "slow", base=20, volatility=0.7, tags=["homeostatic", "body"]),
        Variable("pain", "medium", base=5, volatility=1.5, tags=["homeostatic", "body"]),
        Variable("pleasure", "medium", base=50, volatility=1.0, tags=["homeostatic", "body"]),
        Variable("arousal", "fast", base=40, volatility=1.5, tags=["homeostatic", "body"]),
        Variable("temperature", "medium", base=50, volatility=0.8, tags=["homeostatic", "body"]),
        Variable("comfort", "slow", base=55, volatility=0.6, tags=["homeostatic", "body"]),
        Variable("discomfort", "medium", base=20, volatility=0.9, tags=["homeostatic", "body"]),
        Variable("heart_rate", "fast", base=50, volatility=1.2, tags=["homeostatic", "body"]),
        Variable("breathing", "fast", base=50, volatility=1.0, tags=["homeostatic", "body"]),
    ]