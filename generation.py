"""Генерация и анализ изображений — PC-версия (opencv вместо Pillow)"""

import os
import io
import re
import json
import time
import base64
import random
import tempfile
import urllib.parse
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. ОПЦИОНАЛЬНЫЕ ИМПОРТЫ
# ============================================================

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ opencv/numpy не установлены — генерация недоступна")

# ============================================================
# 3. НАСТРОЙКИ
# ============================================================

BOT_USERNAME = "@SystmkaAI_bot"
LEARNING_IMAGES_FILE = "learned_images.json"

TEMP_DIR = os.path.join(tempfile.gettempdir(), "systmka_generation")
os.makedirs(TEMP_DIR, exist_ok=True)

# Шрифты (по приоритету)
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

# Модель для анализа картинок
VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct"

# Стили
SYSTMKA_FAVORITE_STYLES = [
    "anime", "manga", "manhwa", "digital art",
    "fantasy art", "ethereal", "dreamy", "vibrant",
    "pixel art", "watercolor", "sketch", "oil painting",
]

# ============================================================
# 4. ДАННЫЕ ОБУЧЕНИЯ
# ============================================================

learned_images = {
    "styles": {},
    "ai_art": [],
    "human_art": [],
    "learning_stats": {
        "total_images_analyzed": 0,
        "ai_images_learned": 0,
        "human_images_learned": 0,
        "styles_learned": 0,
        "last_learning": None,
    },
}

# ============================================================
# 5. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_learned_images():
    """Сохранить данные обучения"""
    try:
        with open(LEARNING_IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(learned_images, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения обучения: {e}")
        return False


def load_learned_images():
    """Загрузить данные обучения"""
    global learned_images
    try:
        if os.path.exists(LEARNING_IMAGES_FILE):
            with open(LEARNING_IMAGES_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                if isinstance(loaded.get("styles"), dict):
                    learned_images["styles"] = loaded["styles"]
                if isinstance(loaded.get("ai_art"), list):
                    learned_images["ai_art"] = loaded["ai_art"]
                if isinstance(loaded.get("human_art"), list):
                    learned_images["human_art"] = loaded["human_art"]
                if isinstance(loaded.get("learning_stats"), dict):
                    learned_images["learning_stats"].update(loaded["learning_stats"])
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON обучения: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки обучения: {e}")
        return False


load_learned_images()

# ============================================================
# 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def _find_font():
    """Найти доступный шрифт"""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

# ============================================================
# 7. АНАЛИЗ ИЗОБРАЖЕНИЙ
# ============================================================

def analyze_image_from_url(image_url):
    """Анализ изображения по URL"""
    if not image_url:
        return None
    
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            return None
        
        image_data = response.content
        analysis = analyze_image_deep(image_data, "анализ изображения", "анализ")
        style = detect_style_from_analysis(analysis)
        is_ai = detect_ai_art(analysis, image_data)
        
        if is_ai:
            learned_images["ai_art"].append({
                "url": image_url,
                "style": style,
                "features": analysis.get("features", {}),
                "quality": analysis.get("quality", 5),
                "learned_at": datetime.now().isoformat(),
            })
            learned_images["learning_stats"]["ai_images_learned"] += 1
        else:
            learned_images["human_art"].append({
                "url": image_url,
                "style": style,
                "features": analysis.get("features", {}),
                "quality": analysis.get("quality", 8),
                "learned_at": datetime.now().isoformat(),
            })
            learned_images["learning_stats"]["human_images_learned"] += 1
        
        learned_images["learning_stats"]["total_images_analyzed"] += 1
        learned_images["learning_stats"]["last_learning"] = datetime.now().isoformat()
        
        # Обновляем статистику стилей
        if style:
            if style not in learned_images["styles"]:
                learned_images["styles"][style] = {"count": 0, "examples": [], "quality": 0}
            learned_images["styles"][style]["count"] += 1
            learned_images["styles"][style]["quality"] = (
                learned_images["styles"][style]["quality"] + analysis.get("quality", 5)
            ) / 2
            if len(learned_images["styles"][style]["examples"]) < 5:
                learned_images["styles"][style]["examples"].append(image_url)
        
        learned_images["learning_stats"]["styles_learned"] = len(learned_images["styles"])
        save_learned_images()
        
        return {
            "style": style,
            "is_ai": is_ai,
            "quality": analysis.get("quality", 5),
            "features": analysis.get("features", {}),
            "analysis": analysis.get("full_analysis", ""),
        }
    except Exception as e:
        print(f"⚠️ Ошибка анализа картинки: {e}")
        return None


def detect_style_from_analysis(analysis):
    """Определить стиль из анализа"""
    if not analysis:
        return "unknown"
    
    text = str(analysis).lower()
    
    styles = {
        "anime": ["аниме", "anime", "манга", "manga", "каваи", "kawaii"],
        "pixel": ["пиксель", "pixel", "8bit", "16bit", "32bit", "ретро"],
        "realism": ["реализм", "realism", "фото", "photo", "фотореалист", "photorealistic"],
        "3d": ["3d", "3д", "объём", "rendering", "cg"],
        "fantasy": ["фэнтези", "fantasy", "сказоч", "волшеб", "magic"],
        "cyberpunk": ["кибер", "cyber", "неон", "neon", "future", "футуристич"],
        "gothic": ["готик", "gothic", "тёмн", "dark", "мрачн"],
        "watercolor": ["акварель", "watercolor", "размыт"],
        "sketch": ["скетч", "sketch", "набросок", "карандаш"],
        "oil": ["масло", "oil", "живопись", "painting"],
    }
    
    for style, keywords in styles.items():
        for keyword in keywords:
            if keyword in text:
                return style
    
    return "unknown"


def detect_ai_art(analysis, image_data):
    """Определить AI-арт или реальное изображение"""
    if not analysis:
        return "unknown"
    
    text = str(analysis).lower()
    ai_indicators = [
        "искусственный интеллект", "ai", "нейросеть", "сгенерирова",
        "digital", "рендер", "render", "нейронная сеть",
    ]
    
    for indicator in ai_indicators:
        if indicator in text:
            return True
    
    quality = analysis.get("quality", 5)
    if quality < 4:
        return True
    
    return False

# ============================================================
# 8. ОБУЧЕНИЕ НА СТИЛЯХ
# ============================================================

def learn_style_from_image(image_url):
    """Учить стиль из картинки"""
    result = analyze_image_from_url(image_url)
    if result:
        style = result.get("style")
        if style and style != "unknown":
            print(f"🎨 Выучен стиль: {style}")
            return style
    return None


def get_learned_styles():
    """Получить все выученные стили"""
    return list(learned_images["styles"].keys())


def get_best_style_for_prompt(prompt):
    """Выбрать лучший стиль под запрос"""
    prompt_lower = prompt.lower() if prompt else ""
    
    styles = get_learned_styles()
    if not styles:
        return random.choice(SYSTMKA_FAVORITE_STYLES)
    
    for style in styles:
        if style.lower() in prompt_lower:
            return style
    
    best_style = None
    best_count = 0
    for style, data in learned_images["styles"].items():
        if data.get("count", 0) > best_count:
            best_count = data["count"]
            best_style = style
    
    return best_style or random.choice(SYSTMKA_FAVORITE_STYLES)

# ============================================================
# 9. ГЕНЕРАЦИЯ
# ============================================================

def generate_image(prompt, width=512, height=512, style=None):
    """Главная функция генерации"""
    if not prompt:
        return None
    
    if not CV2_AVAILABLE:
        print("⚠️ opencv недоступен")
        return None
    
    if not style:
        style = get_best_style_for_prompt(prompt)
    
    # Фикс рук
    hand_fix = (
        ", correctly drawn hands, 5 fingers per hand, "
        "no extra fingers, no missing fingers, realistic hands"
    )
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["человек", "девушк", "парн", "люди",
                                        "person", "girl", "boy", "woman", "man"]):
        prompt += hand_fix
    
    quality_prompt = ", high quality, detailed, sharp, clear, masterpiece"
    enhanced_prompt = f"{prompt}, {style} style, {quality_prompt}"
    
    best_image = None
    best_quality = 0
    
    for attempt in range(3):
        img_data = generate_image_raw(enhanced_prompt, width, height)
        if not img_data:
            continue
        
        analysis = analyze_image_deep(img_data, prompt, enhanced_prompt)
        quality = analysis.get("quality", 0)
        hands_ok = check_hands(img_data)
        
        if quality >= 7 and hands_ok:
            best_image = img_data
            best_quality = quality
            break
        
        if quality > best_quality:
            best_image = img_data
            best_quality = quality
        
        if analysis.get("fixed_prompt"):
            enhanced_prompt = analysis["fixed_prompt"]
    
    if best_image:
        return add_watermark(best_image)
    
    # Fallback без анализа
    fallback_img = generate_image_raw(prompt, width, height)
    if fallback_img:
        return add_watermark(fallback_img)
    
    return None


def check_hands(image_data):
    """Проверить качество рук"""
    try:
        analysis = analyze_image_deep(image_data, "проверка рук", "проверка")
        text = str(analysis).lower()
        
        if "6 пальцев" in text or "six fingers" in text:
            return False
        if "неправильные руки" in text or "bad hands" in text:
            return False
        if "искажённые руки" in text or "distorted hands" in text:
            return False
        
        return True
    except Exception:
        return True

# ============================================================
# 10. АНАЛИЗ ЧЕРЕЗ ИИ
# ============================================================

def analyze_image_deep(image_data, original_prompt, generated_prompt):
    """Глубокий анализ изображения через ИИ"""
    if not image_data:
        return {
            "is_match": False,
            "problems": ["Изображение не создано"],
            "quality": 0,
            "fixes_needed": [],
        }
    
    key = _get_openrouter_key()
    if not key:
        return _default_analysis()
    
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Проанализируй изображение.\n\n"
                                    f"ОРИГИНАЛЬНЫЙ ЗАПРОС: {original_prompt}\n"
                                    f"СГЕНЕРИРОВАННЫЙ ПРОМТ: {generated_prompt}\n\n"
                                    "ОТВЕТЬ ПО ФОРМАТУ:\n"
                                    "СООТВЕТСТВУЕТ: ДА или НЕТ\n"
                                    "ПРОБЛЕМЫ: список через запятую или 'нет'\n"
                                    "КАЧЕСТВО: число от 1 до 10\n"
                                    "СТИЛЬ: какой стиль\n"
                                    "РУКИ: правильные/неправильные/нет рук\n"
                                    "КОЛИЧЕСТВО ПАЛЬЦЕВ: число\n"
                                    "ЧТО ИСПРАВИТЬ: что нужно изменить в промте\n\n"
                                    "Если есть ошибки — предложи ИСПРАВЛЕННЫЙ ПРОМТ."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 800,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                result = data['choices'][0]['message']['content']
                
                is_match = "СООТВЕТСТВУЕТ: ДА" in result.upper()
                problems = extract_problems(result)
                quality = extract_quality(result)
                fixed_prompt = extract_fixed_prompt(result)
                fingers = extract_fingers(result)
                
                return {
                    "is_match": is_match,
                    "problems": problems,
                    "quality": quality,
                    "needs_fix": not is_match or quality < 7,
                    "fixed_prompt": fixed_prompt,
                    "fingers": fingers,
                    "full_analysis": result,
                    "features": {
                        "style": extract_style(result),
                        "has_hands": "руки" in result.lower() and "нет рук" not in result.lower(),
                        "fingers_ok": fingers <= 5 if fingers else True,
                    },
                }
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
    
    return _default_analysis()


def _default_analysis():
    """Анализ по умолчанию (если ИИ недоступен)"""
    return {
        "is_match": True,
        "problems": [],
        "quality": 5,
        "needs_fix": False,
        "fixed_prompt": None,
        "fingers": 5,
        "features": {
            "style": "unknown",
            "has_hands": True,
            "fingers_ok": True,
        },
    }


def extract_problems(text):
    """Извлечь список проблем"""
    try:
        match = re.search(r'ПРОБЛЕМЫ:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if match:
            problems = match.group(1).strip()
            if problems.lower() == "нет":
                return []
            return [p.strip() for p in problems.split(",") if p.strip()]
    except Exception:
        pass
    return []


def extract_quality(text):
    """Извлечь качество"""
    try:
        match = re.search(r'КАЧЕСТВО:\s*(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 5


def extract_fixed_prompt(text):
    """Извлечь исправленный промт"""
    try:
        match = re.search(
            r'ИСПРАВЛЕННЫЙ ПРОМТ:\s*(.+?)(?:\n\n|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None


def extract_fingers(text):
    """Извлечь количество пальцев"""
    try:
        match = re.search(r'КОЛИЧЕСТВО ПАЛЬЦЕВ:\s*(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 5


def extract_style(text):
    """Извлечь стиль"""
    try:
        match = re.search(r'СТИЛЬ:\s*(.+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()
    except Exception:
        pass
    return "unknown"

# ============================================================
# 11. ГЕНЕРАЦИЯ (RAW)
# ============================================================

def generate_image_raw(prompt, width=512, height=512):
    """Сгенерировать изображение через Pollinations"""
    if not prompt:
        return None
    
    encoded_prompt = urllib.parse.quote(prompt)
    
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=flux",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=turbo",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true",
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200 and len(response.content) > 10000:
                return response.content
        except Exception:
            continue
    
    return None

# ============================================================
# 12. ВОДЯНОЙ ЗНАК (OPENCV)
# ============================================================

def add_watermark(image_data, text=None):
    """
    Добавить водяной знак через opencv.
    
    Args:
        image_data: bytes исходного изображения
        text: текст (по умолчанию BOT_USERNAME)
    
    Returns:
        bytes: PNG с водяным знаком
    """
    if not CV2_AVAILABLE:
        print("⚠️ opencv недоступен, водяной знак не добавлен")
        return image_data
    
    if not image_data:
        return image_data
    
    if text is None:
        text = BOT_USERNAME
    
    try:
        # Декодируем
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_data
        
        height, width = img.shape[:2]
        
        # Размер шрифта
        font_scale = max(0.5, min(width, height) * 0.001)
        thickness = max(1, int(font_scale * 2))
        
        # Цвет (фиолетовый BGR)
        color = (255, 0, 128)
        
        # Размер текста
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        
        # Позиция (правый нижний угол)
        padding = int(min(width, height) * 0.02)
        x = width - text_width - padding
        y = height - padding
        
        # Полупрозрачный фон
        overlay = img.copy()
        bg_padding = int(padding * 0.5)
        cv2.rectangle(
            overlay,
            (x - bg_padding, y - text_height - bg_padding),
            (x + text_width + bg_padding, y + baseline + bg_padding),
            (128, 0, 255),
            -1,
        )
        
        # Смешиваем с прозрачностью
        alpha = 0.3
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        # Рисуем текст
        cv2.putText(
            img, text, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA
        )
        
        # Кодируем в PNG
        success, buffer = cv2.imencode(".png", img)
        if success:
            return buffer.tobytes()
        
        return image_data
    except Exception as e:
        print(f"❌ Ошибка добавления водяного знака: {e}")
        return image_data

# ============================================================
# 13. СЕЛФИ СИСТМКИ
# ============================================================

def generate_selfie():
    """Селфи Систмки"""
    styles = get_learned_styles() or SYSTMKA_FAVORITE_STYLES
    style = random.choice(styles)
    
    prompt = (
        f"pixel art anime girl, long black hair with bangs, blue eyes, "
        f"yellow flower hairpin, blue dress with yellow skirt, "
        f"starry night, {style}, high quality, detailed"
    )
    
    return generate_image(prompt)

# ============================================================
# 14. СТАТИСТИКА
# ============================================================

def get_generation_stats():
    """Получить статистику генерации"""
    return {
        "styles_learned": len(learned_images["styles"]),
        "ai_images": learned_images["learning_stats"]["ai_images_learned"],
        "human_images": learned_images["learning_stats"]["human_images_learned"],
        "total_analyzed": learned_images["learning_stats"]["total_images_analyzed"],
        "last_learning": learned_images["learning_stats"]["last_learning"],
        "styles": list(learned_images["styles"].keys()),
    }


def format_generation_stats():
    """Форматировать статистику"""
    stats = get_generation_stats()
    
    lines = [
        "🎨 СТАТИСТИКА ГЕНЕРАЦИИ:",
        f"📚 Выучено стилей: {stats['styles_learned']}",
        f"🤖 AI картинок изучено: {stats['ai_images']}",
        f"👤 Человеческих картинок изучено: {stats['human_images']}",
        f"📊 Всего проанализировано: {stats['total_analyzed']}",
    ]
    
    if stats["last_learning"]:
        lines.append(f"🕐 Последнее обучение: {stats['last_learning'][:16]}")
    
    if stats["styles"]:
        lines.append(f"🎭 Стили: {', '.join(stats['styles'][:5])}")
    
    return "\n".join(lines)

# ============================================================
# 15. ЗАГРУЗКА
# ============================================================

_font = _find_font()

print("🎨 Генератор изображений загружен (PC / opencv)")
print(f"📦 opencv: {'✅' if CV2_AVAILABLE else '❌'}")
print(f"📚 Выучено стилей: {len(learned_images['styles'])}")

if _font:
    print(f"🔤 Шрифт: {_font}")
else:
    print("⚠️ Шрифт не найден — водяной знак будет без текста")

if learned_images["styles"]:
    styles_preview = ", ".join(list(learned_images["styles"].keys())[:3])
    print(f"🎭 Стили: {styles_preview}")