"""Все модели ИИ — OpenRouter, Gemini, Hugging Face"""

# ============================================================
# 1. OPENROUTER МОДЕЛИ (ЧЕРЕЗ API)
# ============================================================

OPENROUTER_MODELS = {
    "deepseek/deepseek-chat": {
        "name": "DeepSeek Chat",
        "provider": "OpenRouter",
        "strengths": ["общий", "рассуждение", "код"],
        "weaknesses": ["креативность"],
        "speed": 0.8,
        "quality": 0.9,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "openrouter",
    },
    "deepseek/deepseek-r1": {
        "name": "DeepSeek R1",
        "provider": "OpenRouter",
        "strengths": ["рассуждение", "логика", "математика"],
        "weaknesses": ["скорость"],
        "speed": 0.6,
        "quality": 0.95,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "openrouter",
    },
}

# ============================================================
# 2. GOOGLE GEMINI МОДЕЛИ (БЕСПЛАТНО!)
# ============================================================

GEMINI_MODELS = {
    "gemini/gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "provider": "Google",
        "strengths": ["скорость", "общий", "креативность"],
        "weaknesses": ["сложные задачи"],
        "speed": 0.95,
        "quality": 0.8,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "gemini",
    },
    "gemini/gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash Lite",
        "provider": "Google",
        "strengths": ["очень быстрая", "лёгкая"],
        "weaknesses": ["качество"],
        "speed": 0.99,
        "quality": 0.6,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "gemini",
    },
    "gemini/gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "provider": "Google",
        "strengths": ["мощная", "качество", "рассуждение"],
        "weaknesses": ["скорость"],
        "speed": 0.5,
        "quality": 0.95,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "gemini",
    },
}

# ============================================================
# 3. HUGGING FACE МОДЕЛИ (БЕСПЛАТНО!)
# ============================================================

HUGGINGFACE_MODELS = {
    "huggingface/phi-3.5-mini": {
        "name": "Phi-3.5 Mini",
        "provider": "Hugging Face",
        "strengths": ["быстрая", "лёгкая"],
        "weaknesses": ["сложные задачи"],
        "speed": 0.9,
        "quality": 0.7,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "huggingface",
    },
    "huggingface/mistral-7b": {
        "name": "Mistral 7B",
        "provider": "Hugging Face",
        "strengths": ["баланс", "качество"],
        "weaknesses": ["скорость"],
        "speed": 0.7,
        "quality": 0.8,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "huggingface",
    },
    "huggingface/llama-3.2-3b": {
        "name": "Llama 3.2 3B",
        "provider": "Hugging Face",
        "strengths": ["быстрая", "лёгкая"],
        "weaknesses": ["качество"],
        "speed": 0.9,
        "quality": 0.65,
        "available": True,
        "last_used": None,
        "success_rate": 1.0,
        "total_uses": 0,
        "failures": 0,
        "last_check": None,
        "type": "huggingface",
    },
}

# ============================================================
# 4. ОБЪЕДИНЁННЫЙ СПИСОК
# ============================================================

FREE_MODELS = {}

# Добавляем все модели
for models_dict in [OPENROUTER_MODELS, GEMINI_MODELS, HUGGINGFACE_MODELS]:
    for model_id, data in models_dict.items():
        FREE_MODELS[model_id] = data

# ============================================================
# 5. ЗАГРУЗКА
# ============================================================

print(f"📋 Загружено моделей: {len(FREE_MODELS)}")
print(f"   OpenRouter: {len(OPENROUTER_MODELS)}")
print(f"   Gemini: {len(GEMINI_MODELS)}")
print(f"   Hugging Face: {len(HUGGINGFACE_MODELS)}")