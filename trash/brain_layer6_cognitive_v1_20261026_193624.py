"""
brain_layer6_cognitive.py — 100 когнитивных переменных.

Внимание, память, мышление, речь, восприятие, рефлексия, воображение.
"""

from brain_core import Variable


def get_layer6_variables():
    """100 когнитивных."""
    return [
        # === ВНИМАНИЕ (10) ===
        Variable("attention", "fast", base=50, volatility=1.5, tags=["cognitive", "attention"]),
        Variable("focus", "medium", base=50, volatility=1.2, tags=["cognitive", "attention"]),
        Variable("concentration", "medium", base=50, volatility=1.2, tags=["cognitive", "attention"]),
        Variable("distractibility", "medium", base=30, volatility=1.5, tags=["cognitive", "attention"]),
        Variable("vigilance", "medium", base=50, volatility=1.2, tags=["cognitive", "attention"]),
        Variable("alertness", "fast", base=55, volatility=1.5, tags=["cognitive", "attention"]),
        Variable("awareness", "slow", base=50, volatility=0.8, tags=["cognitive", "attention"]),
        Variable("mindfulness", "slow", base=50, volatility=0.6, tags=["cognitive", "attention"]),
        Variable("sustained_attention", "medium", base=50, volatility=1.0, tags=["cognitive", "attention"]),
        Variable("selective_attention", "medium", base=50, volatility=1.0, tags=["cognitive", "attention"]),
        
        # === ПАМЯТЬ (10) ===
        Variable("working_memory", "medium", base=50, volatility=1.0, tags=["cognitive", "memory"]),
        Variable("short_term_memory", "medium", base=50, volatility=0.9, tags=["cognitive", "memory"]),
        Variable("long_term_memory", "slow", base=50, volatility=0.5, tags=["cognitive", "memory"]),
        Variable("recall", "medium", base=50, volatility=1.0, tags=["cognitive", "memory"]),
        Variable("recognition", "medium", base=50, volatility=0.9, tags=["cognitive", "memory"]),
        Variable("forgetting", "slow", base=30, volatility=0.6, tags=["cognitive", "memory"]),
        Variable("consolidation", "slow", base=50, volatility=0.5, tags=["cognitive", "memory"]),
        Variable("retrieval", "medium", base=50, volatility=0.9, tags=["cognitive", "memory"]),
        Variable("encoding", "medium", base=50, volatility=0.8, tags=["cognitive", "memory"]),
        Variable("memory_load", "medium", base=30, volatility=1.0, tags=["cognitive", "memory"]),
        
        # === МЫШЛЕНИЕ (10) ===
        Variable("logic", "medium", base=50, volatility=0.8, tags=["cognitive", "thinking"]),
        Variable("intuition", "medium", base=55, volatility=0.9, tags=["cognitive", "thinking"]),
        Variable("reasoning", "medium", base=50, volatility=0.8, tags=["cognitive", "thinking"]),
        Variable("analysis", "medium", base=50, volatility=0.8, tags=["cognitive", "thinking"]),
        Variable("synthesis", "medium", base=50, volatility=0.8, tags=["cognitive", "thinking"]),
        Variable("abstraction", "slow", base=50, volatility=0.6, tags=["cognitive", "thinking"]),
        Variable("concrete_thinking", "medium", base=50, volatility=0.7, tags=["cognitive", "thinking"]),
        Variable("critical_thinking", "medium", base=50, volatility=0.7, tags=["cognitive", "thinking"]),
        Variable("creative_thinking", "medium", base=60, volatility=0.9, tags=["cognitive", "thinking"]),
        Variable("divergent_thinking", "medium", base=60, volatility=0.9, tags=["cognitive", "thinking"]),
        
        # === РЕЧЬ (5) ===
        Variable("verbal_fluency", "medium", base=50, volatility=0.8, tags=["cognitive", "speech"]),
        Variable("vocabulary_access", "medium", base=50, volatility=0.7, tags=["cognitive", "speech"]),
        Variable("articulation", "medium", base=50, volatility=0.7, tags=["cognitive", "speech"]),
        Variable("comprehension", "medium", base=50, volatility=0.7, tags=["cognitive", "speech"]),
        Variable("expression", "medium", base=50, volatility=0.8, tags=["cognitive", "speech"]),
        
        # === ВОСПРИЯТИЕ (5) ===
        Variable("pattern_recognition", "medium", base=50, volatility=0.8, tags=["cognitive", "perception"]),
        Variable("spatial_reasoning", "medium", base=50, volatility=0.7, tags=["cognitive", "perception"]),
        Variable("temporal_reasoning", "medium", base=50, volatility=0.7, tags=["cognitive", "perception"]),
        Variable("sensory_integration", "medium", base=50, volatility=0.8, tags=["cognitive", "perception"]),
        Variable("perceptual_speed", "fast", base=50, volatility=1.0, tags=["cognitive", "perception"]),
        
        # === РЕФЛЕКСИЯ (10) ===
        Variable("self_awareness", "slow", base=60, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("meta_cognition", "slow", base=55, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("introspection", "slow", base=60, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("self_reflection", "slow", base=60, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("self_monitoring", "medium", base=55, volatility=0.6, tags=["cognitive", "reflection"]),
        Variable("self_regulation", "slow", base=55, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("self_evaluation", "slow", base=50, volatility=0.6, tags=["cognitive", "reflection"]),
        Variable("theory_of_mind", "slow", base=55, volatility=0.5, tags=["cognitive", "reflection"]),
        Variable("empathy", "slow", base=70, volatility=0.4, tags=["cognitive", "reflection"]),
        Variable("perspective_taking", "medium", base=55, volatility=0.6, tags=["cognitive", "reflection"]),
        
        # === ВООБРАЖЕНИЕ (5) ===
        Variable("imagination", "medium", base=70, volatility=0.8, tags=["cognitive", "imagination"]),
        Variable("visualization", "medium", base=60, volatility=0.8, tags=["cognitive", "imagination"]),
        Variable("fantasy", "medium", base=65, volatility=0.9, tags=["cognitive", "imagination"]),
        Variable("daydreaming", "medium", base=50, volatility=0.9, tags=["cognitive", "imagination"]),
        Variable("mental_simulation", "medium", base=55, volatility=0.7, tags=["cognitive", "imagination"]),
        
        # === ОЦЕНКА (5) ===
        Variable("judgment", "medium", base=50, volatility=0.7, tags=["cognitive", "evaluation"]),
        Variable("decision_making", "medium", base=50, volatility=0.8, tags=["cognitive", "evaluation"]),
        Variable("risk_assessment", "medium", base=50, volatility=0.7, tags=["cognitive", "evaluation"]),
        Variable("probability_estimation", "medium", base=50, volatility=0.7, tags=["cognitive", "evaluation"]),
        Variable("uncertainty_tolerance", "slow", base=50, volatility=0.6, tags=["cognitive", "evaluation"]),
        
        # === ОБУЧЕНИЕ (5) ===
        Variable("learning_rate", "medium", base=50, volatility=0.7, tags=["cognitive", "learning"]),
        Variable("curiosity_drive", "medium", base=70, volatility=0.8, tags=["cognitive", "learning"]),
        Variable("exploration", "medium", base=55, volatility=0.8, tags=["cognitive", "learning"]),
        Variable("exploitation", "medium", base=50, volatility=0.7, tags=["cognitive", "learning"]),
        Variable("adaptability", "slow", base=55, volatility=0.6, tags=["cognitive", "learning"]),
        
        # === СОСТОЯНИЯ (10) ===
        Variable("mental_fatigue", "medium", base=30, volatility=1.0, tags=["cognitive", "state"]),
        Variable("cognitive_load", "medium", base=30, volatility=1.0, tags=["cognitive", "state"]),
        Variable("mental_clarity", "medium", base=55, volatility=0.8, tags=["cognitive", "state"]),
        Variable("mental_fog", "medium", base=20, volatility=0.9, tags=["cognitive", "state"]),
        Variable("brain_fog", "slow", base=20, volatility=0.7, tags=["cognitive", "state"]),
        Variable("flow_state", "medium", base=30, volatility=0.9, tags=["cognitive", "state"]),
        Variable("overwhelm", "medium", base=15, volatility=1.2, tags=["cognitive", "state"]),
        Variable("mental_flexibility", "slow", base=55, volatility=0.6, tags=["cognitive", "state"]),
        Variable("mental_rigidity", "slow", base=30, volatility=0.6, tags=["cognitive", "state"]),
        Variable("mental_energy", "medium", base=55, volatility=0.9, tags=["cognitive", "state"]),
    ]