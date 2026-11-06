"""Игра Троян — PC-версия с сохранением состояния и корректной логикой"""

import random
import json
import os
from datetime import datetime, timedelta

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS
import database as db

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

TROJAN_FILE = "trojan_data.json"
trojan_stats = {}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_trojan_stats():
    """Сохранить статистику игр"""
    try:
        data = {}
        for uid, stats in trojan_stats.items():
            data[str(uid)] = {
                "wins": stats.get("wins", 0),
                "cooldown": (
                    stats.get("cooldown").isoformat()
                    if isinstance(stats.get("cooldown"), datetime)
                    else stats.get("cooldown", "")
                ),
                "game": stats.get("game"),
                "force_normal": stats.get("force_normal", False),
            }
        with open(TROJAN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения trojan: {e}")
        return False

def load_trojan_stats():
    """Загрузить статистику игр"""
    global trojan_stats
    try:
        if os.path.exists(TROJAN_FILE):
            with open(TROJAN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                trojan_stats = {}
                return False
            
            for uid, stats in data.items():
                try:
                    uid_int = int(uid)
                except ValueError:
                    continue
                
                if not isinstance(stats, dict):
                    continue
                
                cooldown = stats.get("cooldown")
                if isinstance(cooldown, str) and cooldown:
                    try:
                        cooldown = datetime.fromisoformat(cooldown)
                    except ValueError:
                        cooldown = None
                
                trojan_stats[uid_int] = {
                    "wins": stats.get("wins", 0),
                    "cooldown": cooldown,
                    "game": stats.get("game"),
                    "force_normal": stats.get("force_normal", False),
                }
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON trojan: {e}")
        trojan_stats = {}
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки trojan: {e}")
        trojan_stats = {}
        return False

load_trojan_stats()

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_trojan_special_chance(user_id):
    """
    Шанс особого трояна.
    
    Особый троян появляется после 3 побед.
    
    Returns:
        float: 0.0 - 0.5
    """
    if user_id not in trojan_stats:
        trojan_stats[user_id] = {"wins": 0, "force_normal": False}
    
    stats = trojan_stats[user_id]
    
    if stats.get("force_normal"):
        stats["force_normal"] = False
        save_trojan_stats()
        return 0.0
    
    wins = stats.get("wins", 0)
    if wins < 3:
        return 0.0
    
    return min(0.5, (wins - 2) * 0.1)

def is_game_active(user_id):
    """Проверить, есть ли активная игра у пользователя"""
    return (
        user_id in trojan_stats
        and trojan_stats[user_id].get("game") is not None
    )

def get_game(user_id):
    """Получить активную игру"""
    if not is_game_active(user_id):
        return None
    return trojan_stats[user_id]["game"]

def end_game(user_id):
    """Завершить игру"""
    if user_id in trojan_stats:
        trojan_stats[user_id]["game"] = None
        save_trojan_stats()

# ============================================================
# 5. ЗАПУСК ИГРЫ
# ============================================================

def start_trojan_game(message, user, bot):
    """Запуск игры"""
    user_id = user.id
    now = datetime.now()
    
    # Проверка кулдауна
    if user_id in trojan_stats:
        cooldown = trojan_stats[user_id].get("cooldown")
        if cooldown and isinstance(cooldown, datetime) and now < cooldown:
            remaining = cooldown - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            bot.reply_to(message, f"Попробуй через {hours}ч {minutes}м")
            return False
    
    # Проверка активной игры
    if is_game_active(user_id):
        bot.reply_to(message, "❌ У тебя уже есть активная игра! Заверши её или напиши 'стоп'.")
        return False
    
    # Определяем тип игры
    special_chance = get_trojan_special_chance(user_id)
    is_special = random.random() < special_chance
    
    if is_special:
        trojan_stats[user_id]["force_normal"] = True
        cooldown_hours = 24
    else:
        cooldown_hours = 12
    
    # Устанавливаем кулдаун
    if user_id not in trojan_stats:
        trojan_stats[user_id] = {"wins": 0, "force_normal": False}
    
    trojan_stats[user_id]["cooldown"] = now + timedelta(hours=cooldown_hours)
    
    # Параметры игры
    code_length = 4 if is_special else 3
    secret_code = [random.randint(0, 9) for _ in range(code_length)]
    symbols = ["🦠", "🪲", "🏴‍☠️", "🆘", "⛔", "❌", "👹", "💀", "🚨", "👺"]
    display = [random.choice(symbols) for _ in range(code_length)]
    time_limit = 120 if is_special else 60
    
    # Правила
    if is_special:
        rules = (
            "⚠️ ОСОБЫЙ ТРОЯН!\n\n"
            "📜 ПРАВИЛА:\n"
            "• 4 цифры\n"
            "• 120 секунд\n"
            "• ⭐ = угадано\n"
            "• Неправильно там где ⭐ — звезда пропадёт\n"
            "• Числа меняются каждые 2 хода\n"
            "• Шанс 20% снятия 10 сек\n"
            "• Награда зависит от скорости\n"
            "• х2 награда!\n\n"
        )
    else:
        rules = (
            "🦠 ТРОЯН!\n\n"
            "📜 ПРАВИЛА:\n"
            "• 3 цифры\n"
            "• 60 секунд\n"
            "• ⭐ = угадано\n"
            "• Неправильно там где ⭐ — звезда пропадёт\n\n"
        )
    
    rules += f"Таймер: {time_limit} сек\n{'#'.join(display)}\n\nВведи {code_length} цифры!"
    
    bot.reply_to(message, rules)
    
    # Сохраняем игру
    trojan_stats[user_id]["game"] = {
        "secret": secret_code,
        "guessed": [False] * code_length,
        "display": display,
        "special": is_special,
        "start_time": now.isoformat(),
        "time_limit": time_limit,
        "code_length": code_length,
        "move_count": 0,
        "bonus_lost": False,
    }
    save_trojan_stats()
    return True

# ============================================================
# 6. ОБРАБОТКА ПОПЫТОК
# ============================================================

def process_trojan_guess(message, user, text, bot):
    """
    Обработка попыток.
    
    Returns:
        bool: True если игра обработала сообщение
    """
    user_id = user.id
    
    # Проверяем активную игру
    if not is_game_active(user_id):
        return False
    
    game = get_game(user_id)
    if not game:
        return False
    
    # Парсим время старта
    start_time = game.get("start_time")
    if isinstance(start_time, str):
        try:
            start_time = datetime.fromisoformat(start_time)
        except ValueError:
            start_time = datetime.now()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Проверка времени
    if elapsed > game["time_limit"]:
        end_game(user_id)
        penalty = random.randint(5, 40)
        glitches = db.get_user_glitches(user_id, OWNER_IDS)
        
        if glitches != float('inf'):
            loss = int(glitches * penalty / 100)
            db.add_glitches(user_id, -loss, OWNER_IDS)
            bot.reply_to(message, f"⏰ Время вышло! -{loss}👾 ({penalty}%)")
        else:
            bot.reply_to(message, "⏰ Время вышло!")
        return True
    
    # Проверка ввода
    if not text or not text.isdigit() or len(text) != game["code_length"]:
        bot.reply_to(message, f"Введи {game['code_length']} цифры!")
        return True
    
    # Специальные механики
    if game["special"] and not game.get("bonus_lost") and random.random() < 0.2:
        game["time_limit"] -= 10
        game["bonus_lost"] = True
        glitch_chars = "".join(
            random.choice(["҂", "ҁ", "ӿ", "Ӿ", "ԅ", "Ԇ", "Ѯ", "Ѭ"])
            for _ in range(random.randint(5, 12))
        )
        bot.send_message(
            message.chat.id,
            f"Ой! {glitch_chars} таймер упал на 10 сек💔\n"
            f"Осталось: {int(game['time_limit'] - elapsed)} сек"
        )
    
    # Парсим попытку
    guess = [int(d) for d in text]
    secret = game["secret"]
    guessed = game["guessed"]
    
    new_guessed = guessed.copy()
    
    # Сравниваем
    for i in range(len(secret)):
        if guess[i] == secret[i]:
            new_guessed[i] = True
        else:
            # Если было угадано — сбрасываем и меняем число
            if guessed[i]:
                new_guessed[i] = False
                secret[i] = random.randint(0, 9)
    
    # Победа?
    if all(new_guessed):
        end_game(user_id)
        
        prize = random.randint(0, 100)
        bonus = random.randint(0, 30)
        glitches = db.get_user_glitches(user_id, OWNER_IDS)
        
        bonus_amount = 0 if glitches == float('inf') else int(glitches * bonus / 100)
        total = prize + bonus_amount
        
        # Специальный бонус
        if game["special"]:
            time_used = elapsed
            if time_used <= 10:
                multiplier = 2.0
            elif time_used <= 60:
                multiplier = max(0.5, 1.0 - (time_used - 10) * 0.01)
            else:
                multiplier = 0.5
            total = int(total * multiplier * 2)
        
        # Инкремент побед
        trojan_stats[user_id]["wins"] = trojan_stats[user_id].get("wins", 0) + 1
        
        db.add_glitches(user_id, total, OWNER_IDS)
        save_trojan_stats()
        
        bot.reply_to(message, f"🌟 ПОБЕДА!\n🌟#🌟#🌟\n\n+{total}👾")
        return True
    
    # Обновляем отображение
    new_display = game["display"].copy()
    for i in range(len(secret)):
        if new_guessed[i]:
            new_display[i] = "⭐"
    
    # Специальная механика — перемешивание чисел каждые 2 хода
    if game["special"]:
        game["move_count"] = game.get("move_count", 0) + 1
        if game["move_count"] % 2 == 0 and sum(new_guessed) < 3:
            unsolved = [i for i in range(len(secret)) if not new_guessed[i]]
            unsolved_values = [secret[i] for i in unsolved]
            random.shuffle(unsolved_values)
            for idx, val in zip(unsolved, unsolved_values):
                secret[idx] = val
    
    # Сохраняем состояние
    game["guessed"] = new_guessed
    game["display"] = new_display
    save_trojan_stats()
    
    bot.reply_to(
        message,
        f"{'#'.join(new_display)}\nОсталось {int(game['time_limit'] - elapsed)} сек"
    )
    return True

# ============================================================
# 7. ОСТАНОВКА ИГРЫ
# ============================================================

def stop_trojan_game(message, user, bot):
    """Остановить активную игру"""
    user_id = user.id
    
    if not is_game_active(user_id):
        bot.reply_to(message, "❌ У тебя нет активной игры")
        return False
    
    end_game(user_id)
    bot.reply_to(message, "🛑 Игра остановлена")
    return True

# ============================================================
# 8. СТАТИСТИКА
# ============================================================

def get_trojan_stats(user_id):
    """Получить статистику игрока"""
    if user_id not in trojan_stats:
        return {"wins": 0, "cooldown": None, "active": False}
    
    stats = trojan_stats[user_id]
    return {
        "wins": stats.get("wins", 0),
        "cooldown": stats.get("cooldown"),
        "active": is_game_active(user_id),
    }

def format_trojan_stats(user_id):
    """Форматировать статистику"""
    stats = get_trojan_stats(user_id)
    lines = [
        "🎮 СТАТИСТИКА ТРОЯНА:",
        f"  🏆 Побед: {stats['wins']}",
        f"  🎯 Игра: {'активна' if stats['active'] else 'нет'}",
    ]
    
    cooldown = stats.get("cooldown")
    if cooldown and isinstance(cooldown, datetime):
        if datetime.now() < cooldown:
            remaining = cooldown - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            lines.append(f"  ⏳ Кулдаун: {hours}ч {minutes}м")
    
    return "\n".join(lines)

# ============================================================
# 9. ЗАГРУЗКА
# ============================================================

print("🦠 Модуль игры Троян загружен")
print(f"📊 Активных игр: {sum(1 for s in trojan_stats.values() if s.get('game'))}")
print(f"👥 Игроков в базе: {len(trojan_stats)}")