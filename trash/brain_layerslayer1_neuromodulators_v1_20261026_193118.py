"""
layer1_neuromodulators.py — 30 нейромодуляторов (гормонов).

Медленные, глобальные, влияют на всё.
Аналог: дофамин, серотонин, кортизол, окситоцин и т.д.
"""

from brain_core import Variable


def get_layer1_variables():
    """30 нейромодуляторов."""
    return [
        # === КЛАССИЧЕСКИЕ ===
        Variable("dopamine", "slow", base=50, volatility=1.5, tags=["neuromodulator", "reward"]),
        Variable("serotonin", "slow", base=55, volatility=0.8, tags=["neuromodulator", "mood"]),
        Variable("cortisol", "medium", base=30, volatility=2.0, tags=["neuromodulator", "stress"]),
        Variable("oxytocin", "slow", base=50, volatility=1.0, tags=["neuromodulator", "love"]),
        Variable("adrenaline", "fast", base=20, volatility=3.0, tags=["neuromodulator", "stress"]),
        Variable("noradrenaline", "fast", base=30, volatility=2.5, tags=["neuromodulator", "alert"]),
        Variable("acetylcholine", "medium", base=50, volatility=1.2, tags=["neuromodulator", "attention"]),
        Variable("gaba", "slow", base=50, volatility=0.8, tags=["neuromodulator", "calm"]),
        Variable("glutamate", "fast", base=50, volatility=1.5, tags=["neuromodulator", "excite"]),
        Variable("endorphin", "medium", base=50, volatility=1.0, tags=["neuromodulator", "pleasure"]),
        
        # === ЦИРКАДНЫЕ ===
        Variable("melatonin", "circadian", base=30, volatility=0.5, tags=["neuromodulator", "sleep"]),
        Variable("histamine", "medium", base=50, volatility=1.0, tags=["neuromodulator", "wake"]),
        
        # === ЭНДОКАННАБИНОИДЫ ===
        Variable("anandamide", "slow", base=50, volatility=0.8, tags=["neuromodulator", "bliss"]),
        
        # === ПЕПТИДЫ ===
        Variable("substance_p", "medium", base=30, volatility=1.5, tags=["neuromodulator", "pain"]),
        Variable("bdnf", "slow", base=50, volatility=0.6, tags=["neuromodulator", "growth"]),
        Variable("ngf", "slow", base=50, volatility=0.5, tags=["neuromodulator", "growth"]),
        Variable("dynorphin", "medium", base=30, volatility=1.2, tags=["neuromodulator", "pain"]),
        Variable("enkephalin", "medium", base=50, volatility=1.0, tags=["neuromodulator", "pleasure"]),
        
        # === ГОРМОНЫ ===
        Variable("testosterone", "slow", base=50, volatility=0.8, tags=["hormone", "power"]),
        Variable("estrogen", "slow", base=50, volatility=0.6, tags=["hormone"]),
        Variable("progesterone", "slow", base=50, volatility=0.5, tags=["hormone"]),
        Variable("vasopressin", "slow", base=50, volatility=0.8, tags=["hormone", "bond"]),
        Variable("leptin", "slow", base=50, volatility=0.5, tags=["hormone", "satiety"]),
        Variable("ghrelin", "medium", base=30, volatility=1.0, tags=["hormone", "hunger"]),
        Variable("insulin", "slow", base=50, volatility=0.4, tags=["hormone"]),
        
        # === ЩИТОВИДКА ===
        Variable("tsh", "slow", base=50, volatility=0.5, tags=["hormone", "thyroid"]),
        Variable("acth", "medium", base=50, volatility=0.8, tags=["hormone", "stress"]),
        Variable("crh", "medium", base=30, volatility=1.2, tags=["hormone", "stress"]),
        
        # === ПРОЧИЕ ===
        Variable("adenosine", "slow", base=30, volatility=0.8, tags=["neuromodulator", "sleep"]),
        Variable("nitric_oxide", "fast", base=50, volatility=1.5, tags=["neuromodulator", "blood"]),
    ]