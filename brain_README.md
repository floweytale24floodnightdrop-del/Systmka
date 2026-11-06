# 🧠 Мозг Систмки

## Что это

Мозг Систмки — система из **665 переменных**, которые живут своей жизнью:
- Меняются с разной частотой
- Влияют друг на друга
- Создают новые связи
- Создают новые переменные
- Развивают характер

Мозг **не заменяет** `consciousness.py`. Он **дополняет** его:
- `consciousness.py` — единый источник правды для эмоций (0-10)
- `brain` — глубинная система (0-100), которая питает `consciousness`

## Файлы

| Файл | Что делает |
|---|---|
| `brain_core.py` | Ядро: Variable, Emotion, Connection, Brain |
| `brain_layers_init.py` | Загрузчик всех слоёв |
| `brain_layer1_neuromodulators.py` | 30 гормонов |
| `brain_layer2_emotions_primary.py` | 40 базовых эмоций |
| `brain_layer3_emotions_complex.py` | 60 сложных эмоций |
| `brain_layer4_moods.py` | 30 настроений |
| `brain_layer5_character.py` | 25 черт характера |
| `brain_layer6_cognitive.py` | 100 когнитивных |
| `brain_layer7_motivation.py` | 50 мотиваций |
| `brain_layer8_social.py` | 100 социальных |
| `brain_layer9_homeostatic.py` | 30 гомеостатических |
| `brain_layer10_dynamic.py` | 200+ динамических |
| `brain_modulators.py` | 20 триггеров, эффекты, стеккинг |
| `brain_persistence.py` | Сохранение/загрузка |
| `brain_emergence.py` | Эмерджентность |
| `brain_integration.py` | Интеграция |
| `brain_init.py` | Единая точка инициализации |

## Установка

### Шаг 1: Скопировать все файлы в корень проекта

systmka/
├── brain_core.py
├── brain_layers_init.py
├── brain_layer1_neuromodulators.py
├── ... (все brain_*.py)
├── bot.py
├── config.py
└── ...

### Шаг 2: Интегрировать в `bot.py`

Добавить **в начало** (после `import telebot`):

```python
from brain_init import init_brain, shutdown_brain, is_initialized

init_brain(auto_start=True)