"""
brain_layers — все переменные мозга Систмки.

Разбито на модули:
- layer1_neuromodulators.py — 30 гормонов
- layer2_emotions_primary.py — 40 базовых эмоций
- layer3_emotions_complex.py — 60 сложных эмоций
- layer4_moods.py — 30 настроений
- layer5_character.py — 25 черт характера
- layer6_cognitive.py — 100 когнитивных
- layer7_motivation.py — 50 мотиваций
- layer8_social.py — 100 социальных
- layer9_homeostatic.py — 30 гомеостатических
- layer10_dynamic.py — 200+ динамических

Итого: ~665 переменных (растёт до 1000 через эмерджентность).
"""

from brain_layers.layer1_neuromodulators import get_layer1_variables
from brain_layers.layer2_emotions_primary import get_layer2_variables
from brain_layers.layer3_emotions_complex import get_layer3_variables
from brain_layers.layer4_moods import get_layer4_variables
from brain_layers.layer5_character import get_layer5_variables
from brain_layers.layer6_cognitive import get_layer6_variables
from brain_layers.layer7_motivation import get_layer7_variables
from brain_layers.layer8_social import get_layer8_variables
from brain_layers.layer9_homeostatic import get_layer9_variables
from brain_layers.layer10_dynamic import get_layer10_variables


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
    for var in get_all_variables():
        brain.add_variable(var)
        total += 1
    print(f"🧠 Загружено переменных: {total}")
    return total