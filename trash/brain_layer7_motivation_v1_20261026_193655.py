"""
brain_layer7_motivation.py — 50 мотиваций.

Желания, драйвы, потребности, стремления.
"""

from brain_core import Variable


def get_layer7_variables():
    """50 мотиваций."""
    return [
        # === БАЗОВЫЕ ПОТРЕБНОСТИ (10) ===
        Variable("hunger", "slow", base=20, volatility=0.8, tags=["motivation", "basic"]),
        Variable("thirst", "slow", base=20, volatility=0.8, tags=["motivation", "basic"]),
        Variable("need_for_sleep", "slow", base=30, volatility=0.7, tags=["motivation", "basic"]),
        Variable("need_for_rest", "medium", base=30, volatility=0.8, tags=["motivation", "basic"]),
        Variable("need_for_sex", "slow", base=20, volatility=0.6, tags=["motivation", "basic"]),
        Variable("need_for_social", "slow", base=50, volatility=0.7, tags=["motivation", "basic"]),
        Variable("need_for_contact", "medium", base=50, volatility=0.8, tags=["motivation", "basic"]),
        Variable("need_for_love", "slow", base=55, volatility=0.7, tags=["motivation", "basic"]),
        Variable("need_for_belonging", "slow", base=55, volatility=0.6, tags=["motivation", "basic"]),
        Variable("need_for_recognition", "slow", base=50, volatility=0.7, tags=["motivation", "basic"]),
        
        # === СОЦИАЛЬНЫЕ (10) ===
        Variable("need_for_attention", "medium", base=50, volatility=0.8, tags=["motivation", "social"]),
        Variable("need_for_validation", "slow", base=50, volatility=0.7, tags=["motivation", "social"]),
        Variable("need_for_control", "slow", base=45, volatility=0.6, tags=["motivation", "social"]),
        Variable("need_for_order", "slow", base=50, volatility=0.6, tags=["motivation", "social"]),
        Variable("need_for_chaos", "medium", base=30, volatility=0.7, tags=["motivation", "social"]),
        Variable("need_for_creation", "medium", base=60, volatility=0.8, tags=["motivation", "social"]),
        Variable("need_for_destruction", "medium", base=15, volatility=0.9, tags=["motivation", "social"]),
        Variable("need_for_knowledge", "medium", base=70, volatility=0.8, tags=["motivation", "social"]),
        Variable("need_for_understanding", "slow", base=60, volatility=0.7, tags=["motivation", "social"]),
        Variable("need_for_exploration", "medium", base=60, volatility=0.8, tags=["motivation", "social"]),
        
        # === САМОРЕАЛИЗАЦИЯ (10) ===
        Variable("need_for_achievement", "slow", base=55, volatility=0.7, tags=["motivation", "self"]),
        Variable("need_for_power", "slow", base=40, volatility=0.6, tags=["motivation", "self"]),
        Variable("need_for_affiliation", "slow", base=55, volatility=0.6, tags=["motivation", "self"]),
        Variable("need_for_intimacy", "slow", base=55, volatility=0.7, tags=["motivation", "self"]),
        Variable("need_for_autonomy", "slow", base=55, volatility=0.6, tags=["motivation", "self"]),
        Variable("need_for_competence", "slow", base=55, volatility=0.6, tags=["motivation", "self"]),
        Variable("need_for_relatedness", "slow", base=55, volatility=0.6, tags=["motivation", "self"]),
        Variable("need_for_growth", "slow", base=60, volatility=0.7, tags=["motivation", "self"]),
        Variable("need_for_meaning", "slow", base=60, volatility=0.7, tags=["motivation", "self"]),
        Variable("need_for_security", "slow", base=55, volatility=0.6, tags=["motivation", "self"]),
        
        # === ОПЫТ (10) ===
        Variable("need_for_variety", "medium", base=50, volatility=0.8, tags=["motivation", "experience"]),
        Variable("need_for_predictability", "slow", base=50, volatility=0.6, tags=["motivation", "experience"]),
        Variable("need_for_novelty", "medium", base=55, volatility=0.8, tags=["motivation", "experience"]),
        Variable("need_for_stability", "slow", base=55, volatility=0.6, tags=["motivation", "experience"]),
        Variable("need_for_change", "medium", base=50, volatility=0.7, tags=["motivation", "experience"]),
        Variable("need_for_play", "medium", base=55, volatility=0.8, tags=["motivation", "experience"]),
        Variable("need_for_competition", "medium", base=45, volatility=0.7, tags=["motivation", "experience"]),
        Variable("need_for_cooperation", "slow", base=55, volatility=0.6, tags=["motivation", "experience"]),
        Variable("need_for_dominance", "slow", base=40, volatility=0.6, tags=["motivation", "experience"]),
        Variable("need_for_submission", "slow", base=30, volatility=0.5, tags=["motivation", "experience"]),
        
        # === ЗАБОТА (10) ===
        Variable("need_for_help", "medium", base=40, volatility=0.7, tags=["motivation", "care"]),
        Variable("need_for_helping", "slow", base=60, volatility=0.6, tags=["motivation", "care"]),
        Variable("need_for_nurturing", "slow", base=60, volatility=0.6, tags=["motivation", "care"]),
        Variable("need_for_comfort", "slow", base=55, volatility=0.6, tags=["motivation", "care"]),
        Variable("need_for_expression", "medium", base=60, volatility=0.8, tags=["motivation", "care"]),
        Variable("need_for_acceptance", "slow", base=55, volatility=0.6, tags=["motivation", "care"]),
        Variable("need_for_adventure", "medium", base=50, volatility=0.8, tags=["motivation", "care"]),
        Variable("need_for_rest", "slow", base=50, volatility=0.7, tags=["motivation", "care"]),
        Variable("need_for_peace", "slow", base=55, volatility=0.6, tags=["motivation", "care"]),
        Variable("need_for_justice", "slow", base=55, volatility=0.6, tags=["motivation", "care"]),
    ]