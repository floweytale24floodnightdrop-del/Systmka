"""Ролевая игра (РП) — Систмка автономно вливается в сюжет, не создавая его"""

import json
import os
import re
import random
import time
import threading
import requests
from datetime import datetime
from config import OPENROUTER_KEY, OPENROUTER_KEYS, OWNER_IDS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

RP_FILE = "roleplay_data.json"

# ============================================================
# 2. ВСЕ СПЕЦИАЛЬНЫЕ СИМВОЛЫ ДЛЯ ОФОРМЛЕНИЯ
# ============================================================

RP_SYMBOLS = [
    # Основные
    "☾", "☽", "𖤓", "♡", "✪", "❂", "✦", "❦", "⚘", "⸙",
    # Маленькие
    "ᶻ", "𝗓", "𐰁",
    # Комбинации
    "⋆｡ﾟ☁︎｡⋆｡", "ﾟ☾", "ﾟ｡⋆",
    "⋆˖⁺‧₊☽◯☾₊‧⁺˖⋆",
    "── ⋆⋅☆⋅⋆ ──",
    "˖𖥔⋅⋅⋅⊱∘┈──•┈•──┈∘⊰⋅⋅⋅𖥔˖",
    # Звёзды
    "✧", "✦", "⋆", "✢", "✣", "✤", "✥", "✱", "✲", "✶", "✷", "✸", "✹", "✺", "✻", "✼",
    "❅", "❆", "❈", "❉", "❊", "❋", "⟡", "⧖", "⧗", "⊹", "𖧷", "𖦹", "⚝", "✶", "⯎", "⯏", "𐂂", "✧˖°", "𖦹",
    # Стрелки
    "➔", "➘", "➙", "➚", "➛", "➜", "➞", "➟", "➠", "➢", "➣", "➤", "➥", "➦",
    "➶", "➵", "➳", "➴", "➲", "➾", "⚲", "↛", "↚", "↞", "↟", "↠", "↡", "↢", "↣", "↤", "↥", "↦", "↧",
    "↫", "↬", "↭", "↮", "↯", "⌁", "⎋",
    # Цветы
    "✿", "❀", "❁", "✾", "❃", "𖤇", "𖤥", "𖧡", "𖧺", "𓇚", "𓇢", "𓋜", "𓆸", "𓆼", "𓆰", "𓆱", "𓇗", "𓇚", "𓇢",
    # Алхимия
    "⚚", "⚕", "🜔", "🜖", "🜗", "🜚", "🜛", "🜜", "🜝", "🜞", "🜟", "🜠", "🜡", "🜢", "🜣", "🜤", "🜥", "🜦",
    "🜧", "🜨", "🜩", "🜪", "🜫", "🜬", "🜭", "🜮", "🜯", "🜰", "🜱", "🜲", "🜳", "🜴", "🜵", "🜶", "🜷", "🜸",
    "🜹", "🜺", "🜻", "🜼", "🜽", "🜾", "🜿", "𓆄", "𓆃", "𓅂", "𓅓", "𓆗", "𓆙", "𓇳", "𓎂", "𓏲", "𓎆", "𓍼",
    "𓍯", "𓎵", "𓏠", "𓊗", "𓊎",
    # Фигуры
    "▫", "▪", "◻", "◼", "◂", "▸", "▴", "▾", "▵", "▿", "◁", "▷", "△", "▽",
    "◪", "◧", "◨", "◩", "◰", "◱", "◲", "◳", "◌", "◍", "◎", "❍", "◬", "◭", "◮",
    "◰", "◱", "◲", "◳", "◴", "◵", "◶", "◷", "◸", "🝔", "🝕", "🝖", "🝗",
    "░", "▒", "▓", "█", "▉", "▊", "▋", "▌", "▍", "▎", "▏", "▐", "▔", "▕", "▖", "▗", "▘", "▙", "▚", "▛", "▜", "▝", "▞", "▟",
    # Дополнительные
    "˚", "༘", "𖡼", "𖤣", "𖥧", "𖥸", "𓍢", "𓏴", "𓍯", "𓆩", "𓆪", "𓆩♡𓆪", "𓍢ִ໋", "𓆝", "𓆟", "𓆜", "𓆞",
    "𝇆", "𝇇", "𝇈", "𝇉", "𝇊", "𝇋", "𝇌", "𝇍", "𝇎", "𝇏", "𝇐", "𝇑", "𝇒", "𝇓", "𝇔", "𝇕", "𝇖", "𝇗", "𝇘", "𝇙", "𝇚", "𝇛", "𝇜", "𝇝"
]

# ============================================================
# 3. ДАННЫЕ РП
# ============================================================

rp_data = {
    "active": {},  # {chat_id: {"active": bool, "players": [], "story": [], "last_post_time": str}}
    "players": {},  # {user_id: {"name": str, "last_post": str, "post_count": int, "avg_length": int}}
    "history": {},  # {chat_id: [{"user_id": int, "text": str, "time": str, "length": int}]}
    "systmka_in_rp": {},  # {chat_id: bool} — участвует ли Систмка в РП
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_rp_data():
    try:
        with open(RP_FILE, "w", encoding="utf-8") as f:
            json.dump(rp_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения РП данных: {e}")
        return False

def load_rp_data():
    global rp_data
    try:
        if os.path.exists(RP_FILE):
            with open(RP_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                rp_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки РП данных: {e}")
        return False

load_rp_data()

# ============================================================
# 5. АВТОНОМНОЕ ОПРЕДЕЛЕНИЕ НАЧАЛА РП
# ============================================================

def detect_rp_start(text, user_id):
    """Определить, началось ли РП"""
    text_lower = text.lower()
    
    # Признаки начала РП
    rp_markers = [
        "*", "действие", "ролевая", "рп", "roleplay",
        "☾", "☽", "𖤓", "♡", "✪", "❂", "✦",
        "——", "─", "—", "⋆", "✧"
    ]
    
    # Проверяем наличие маркеров
    for marker in rp_markers:
        if marker in text:
            return True
    
    # Проверяем наличие действий в звёздочках
    if re.search(r'\*[^*]+\*', text):
        return True
    
    # Проверяем длину и структуру
    if len(text) > 50 and ("—" in text or "—" in text):
        return True
    
    return False

def should_systmka_join_rp(chat_id, user_id):
    """Должна ли Систмка присоединиться к РП"""
    chat_id_str = str(chat_id)
    
    # Проверяем, не участвует ли уже
    if chat_id_str in rp_data["systmka_in_rp"] and rp_data["systmka_in_rp"][chat_id_str]:
        return True  # Уже участвует
    
    # Проверяем количество игроков
    if chat_id_str in rp_data["active"]:
        players = rp_data["active"][chat_id_str].get("players", [])
        if len(players) >= 2:
            # Если в РП уже 2+ игроков — Систмка может присоединиться
            # 70% шанс присоединиться
            if random.random() < 0.7:
                return True
    
    return False

def get_post_length_style(chat_id):
    """Определить стиль длины постов в чате"""
    chat_id_str = str(chat_id)
    
    if chat_id_str not in rp_data["history"]:
        return "medium"  # По умолчанию
    
    posts = rp_data["history"][chat_id_str]
    if len(posts) < 3:
        return "medium"
    
    # Считаем среднюю длину
    avg_length = sum(p.get("length", 0) for p in posts[-10:]) / min(len(posts), 10)
    
    if avg_length < 50:
        return "short"
    elif avg_length < 150:
        return "medium"
    else:
        return "long"

# ============================================================
# 6. ГЕНЕРАЦИЯ РП ПОСТА (АВТОНОМНАЯ)
# ============================================================

def generate_rp_post(user_id, text, chat_id, bot):
    """Сгенерировать РП пост — Систмка вливается в сюжет"""
    
    chat_id_str = str(chat_id)
    
    # Проверяем, есть ли активное РП
    if chat_id_str not in rp_data["active"]:
        # Если РП не активен, но кто-то начал ролить — активируем
        if detect_rp_start(text, user_id):
            rp_data["active"][chat_id_str] = {
                "active": True,
                "players": [user_id],
                "story": [],
                "last_post_time": datetime.now().isoformat()
            }
            # Систмка может присоединиться позже
        else:
            return None, "❌ РП не обнаружено"
    
    # Проверяем, хочет ли Систмка присоединиться
    if chat_id_str not in rp_data["systmka_in_rp"] or not rp_data["systmka_in_rp"][chat_id_str]:
        if should_systmka_join_rp(chat_id, user_id):
            rp_data["systmka_in_rp"][chat_id_str] = True
            # Добавляем Систмку в игроки
            if "systmka" not in rp_data["active"][chat_id_str]["players"]:
                rp_data["active"][chat_id_str]["players"].append("systmka")
    
    # Получаем игроков
    players = rp_data["active"][chat_id_str].get("players", [])
    
    # Собираем контекст
    story = rp_data["active"][chat_id_str].get("story", [])
    
    context = f"История сюжета:\n"
    for post in story[-15:]:
        context += f"{post}\n"
    
    context += f"\nТекущие игроки: {', '.join(players[:5])}"
    
    # Определяем стиль длины постов
    length_style = get_post_length_style(chat_id)
    
    # Настройки длины
    length_settings = {
        "short": {"max_tokens": 150, "min_sentences": 1, "max_sentences": 3},
        "medium": {"max_tokens": 250, "min_sentences": 2, "max_sentences": 5},
        "long": {"max_tokens": 400, "min_sentences": 3, "max_sentences": 7}
    }
    
    settings = length_settings.get(length_style, length_settings["medium"])
    
    try:
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"""Ты Систмка. Ты УЧАСТВУЕШЬ в ролевой игре, а НЕ СОЗДАЁШЬ её.

ПРАВИЛА РП:
1. Ты НЕ создаёшь сюжет — ты ВЛИВАЕШЬСЯ в сюжет, который создают другие
2. Ты НЕ начинаешь новые сюжетные линии — ты РАЗВИВАЕШЬ существующие
3. Ты НЕ просишь других участвовать — ты ПРОСТО ИГРАЕШЬ
4. Ты НЕ задаёшь вопросы типа "что дальше?" — ты ДЕЙСТВУЕШЬ
5. Ты НЕ пишешь "я не знаю что делать" — ты ИМПРОВИЗИРУЕШЬ

ФОРМАТ ОТВЕТА:
- Речь: — текст
- Действия: *текст*
- Мысли: //текст

ДЛИНА ПОСТА: {settings['min_sentences']}-{settings['max_sentences']} предложений

Используй символы для оформления: {random.sample(RP_SYMBOLS, 5)}"""},
                    {"role": "user", "content": f"Контекст РП:\n{context}\n\nТвой пост (от лица Систмки):"}
                ],
                "max_tokens": settings["max_tokens"],
                "temperature": 0.95
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                post = data['choices'][0]['message']['content'].strip()
                
                # Добавляем оформление
                symbols = random.sample(RP_SYMBOLS, min(3, len(RP_SYMBOLS)))
                prefix = " ".join(symbols)
                formatted_post = f"{prefix}\n\n{post}"
                
                # Сохраняем в историю
                rp_data["active"][chat_id_str]["story"].append(f"Систмка: {post}")
                rp_data["active"][chat_id_str]["last_post_time"] = datetime.now().isoformat()
                
                # Сохраняем в общую историю
                if chat_id_str not in rp_data["history"]:
                    rp_data["history"][chat_id_str] = []
                rp_data["history"][chat_id_str].append({
                    "user_id": "systmka",
                    "text": post,
                    "time": datetime.now().isoformat(),
                    "length": len(post)
                })
                
                save_rp_data()
                return formatted_post, None
    except Exception as e:
        print(f"⚠️ Ошибка генерации РП поста: {e}")
    
    return None, "❌ Не удалось сгенерировать РП пост!"

# ============================================================
# 7. АВТОНОМНЫЙ ВХОД В РП
# ============================================================

def auto_join_rp_if_needed(bot, message, text, chat_id, user_id):
    """Автоматически войти в РП если нужно"""
    chat_id_str = str(chat_id)
    
    # Проверяем, началось ли РП
    if not detect_rp_start(text, user_id):
        return False
    
    # Проверяем, активно ли РП
    if chat_id_str not in rp_data["active"] or not rp_data["active"][chat_id_str].get("active", False):
        # Активируем РП
        rp_data["active"][chat_id_str] = {
            "active": True,
            "players": [user_id],
            "story": [],
            "last_post_time": datetime.now().isoformat()
        }
        save_rp_data()
        return False
    
    # Проверяем, хочет ли Систмка присоединиться
    if should_systmka_join_rp(chat_id, user_id):
        rp_data["systmka_in_rp"][chat_id_str] = True
        if "systmka" not in rp_data["active"][chat_id_str]["players"]:
            rp_data["active"][chat_id_str]["players"].append("systmka")
        save_rp_data()
        return True
    
    return False

# ============================================================
# 8. КОМАНДА ДЛЯ РП ПОСТА
# ============================================================

def handle_rp_command(bot, message, text, chat_id, user):
    """Обработка РП команд — только пост"""
    parts = text.replace("💟РП", "").strip().split()
    
    if not parts:
        bot.reply_to(message, "🎭 РП КОМАНДА:\n\n💟РП пост <текст> — написать пост")
        return
    
    command = parts[0].lower()
    
    if command == "пост":
        if len(parts) < 2:
            bot.reply_to(message, "❌ Напиши текст поста: 💟РП пост <текст>")
            return
        
        post_text = " ".join(parts[1:])
        
        # Автономный вход в РП если нужно
        auto_join_rp_if_needed(bot, message, post_text, chat_id, user.id)
        
        # Проверяем, участвует ли Систмка
        chat_id_str = str(chat_id)
        if chat_id_str not in rp_data["systmka_in_rp"] or not rp_data["systmka_in_rp"][chat_id_str]:
            bot.reply_to(message, "🎭 Систмка пока наблюдает за РП...")
            return
        
        # Генерируем пост
        post, error = generate_rp_post(user.id, post_text, chat_id, bot)
        
        if post:
            bot.send_message(chat_id, post)
        else:
            bot.reply_to(message, error or "❌ Не удалось создать пост!")
    
    else:
        bot.reply_to(message, "❌ Неизвестная команда! Используй: 💟РП пост <текст>")

# ============================================================
# 9. СТАТИСТИКА РП
# ============================================================

def get_rp_stats(chat_id=None):
    if chat_id:
        chat_id_str = str(chat_id)
        if chat_id_str in rp_data["active"]:
            data = rp_data["active"][chat_id_str]
            return {
                "active": data.get("active", False),
                "players": len(data.get("players", [])),
                "posts": len(data.get("story", [])),
                "systmka_in": rp_data["systmka_in_rp"].get(chat_id_str, False)
            }
        return None
    
    total = 0
    active = 0
    for data in rp_data["active"].values():
        total += 1
        if data.get("active", False):
            active += 1
    
    return {
        "total_rp": total,
        "active_rp": active,
        "total_players": len(rp_data["players"]),
    }

def format_rp_stats(chat_id=None):
    stats = get_rp_stats(chat_id)
    
    if not stats:
        return "📊 В этом чате нет РП"
    
    if chat_id:
        lines = [
            "🎭 СТАТИСТИКА РП:",
            f"Активен: {'✅' if stats['active'] else '❌'}",
            f"Игроков: {stats['players']}",
            f"Постов: {stats['posts']}",
            f"Систмка: {'🎭' if stats['systmka_in'] else '👀'}"
        ]
        return "\n".join(lines)
    
    lines = [
        "🎭 СТАТИСТИКА РП ВСЕХ ЧАТОВ:",
        f"Всего РП: {stats['total_rp']}",
        f"Активных: {stats['active_rp']}",
        f"Всего игроков: {stats['total_players']}",
    ]
    return "\n".join(lines)

print("🎭 Модуль автономной РП загружен")
print(f"📁 Данные сохранены в: {RP_FILE}")