"""brain_layers_init.py — Загрузка всех переменных мозга."""

from brain_layer1_neuromodulators import get_layer1_variables
from brain_layer2_emotions_primary import get_layer2_variables
from brain_layer3_emotions_complex import get_layer3_variables
from brain_layer4_moods import get_layer4_variables
from brain_layer5_character import get_layer5_variables
from brain_layer6_cognitive import get_layer6_variables
from brain_layer7_motivation import get_layer7_variables
from brain_layer8_social import get_layer8_variables
from brain_layer9_homeostatic import get_layer9_variables
from brain_layer10_dynamic import get_layer10_variables


def get_all_variables():
    """Получить все переменные всех слоёв."""
    all_vars = []
    all_vars.extend(get_layer1_variables())
    all_vars.extend(get_layer2_variables())
    all_vars.extend(get_layer3_variables())
    all_vars.extend(get_layer4_variables())
    all_vars.extend(get_layer5_variables())
    all_vars.extend(get_layer6_variables())
    all_vars.extend(get_layer7_variables())
    all_vars.extend(get_layer8_variables())
    all_vars.extend(get_layer9_variables())
    all_vars.extend(get_layer10_variables())
    return all_vars


def load_all_into_brain(brain):
    """Загрузить все переменные в мозг."""
    total = 0
    seen = set()
    for var in get_all_variables():
        if var.name in seen:
            continue
        seen.add(var.name)
        brain.add_variable(var)
        total += 1
    print(f"🧠 Загружено переменных: {total}")
    return total