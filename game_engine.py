"""Движок базовых игр — угадай число, КНБ, виселица, крестики-нолики"""

import random
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

BASE_GAMES = {
    "угадай число": {
        "description": "Угадай число от 1 до 100",
        "type": "number_guess",
    },
    "камень ножницы бумага": {
        "description": "Камень-ножницы-бумага",
        "type": "rps",
    },
    "виселица": {
        "description": "Угадай слово по буквам",
        "type": "hangman",
    },
    "крестики нолики": {
        "description": "Крестики-нолики",
        "type": "tic_tac_toe",
    },
}

# Слова для виселицы
HANGMAN_WORDS = [
    "систмка", "флауи", "андертейл", "телеграм", "питон",
    "цветок", "ночь", "звезда", "мечта", "любовь",
    "дружба", "солнце", "луна", "космос", "весна",
]

# ============================================================
# 2. ЗАПУСК БАЗОВЫХ ИГР
# ============================================================

def start_base_game(bot, chat_id, game_type, active_games=None):
    """
    Запустить базовую игру по типу.
    
    Args:
        bot: telebot instance
        chat_id: ID чата
        game_type: тип игры
        active_games: словарь активных игр (если None — берём из games)
    
    Returns:
        bool: успех
    """
    if active_games is None:
        active_games = _get_active_games()
    
    if active_games is None:
        print("⚠️ active_games недоступны")
        return False
    
    if game_type == "number_guess":
        number = random.randint(1, 100)
        active_games[chat_id] = {
            "type": "number_guess",
            "number": number,
            "attempts": 0,
        }
        bot.send_message(
            chat_id,
            "🎮 Я загадала число от 1 до 100! Угадывай!",
        )
        return True
    
    elif game_type == "rps":
        active_games[chat_id] = {"type": "rps"}
        bot.send_message(
            chat_id,
            "🎮 Камень, ножницы, бумага! Напиши свой выбор!",
        )
        return True
    
    elif game_type == "hangman":
        word = random.choice(HANGMAN_WORDS)
        active_games[chat_id] = {
            "type": "hangman",
            "word": word,
            "guessed": [],
            "attempts": 6,
        }
        display = " ".join(["_" for _ in word])
        bot.send_message(
            chat_id,
            f"🎮 Виселица!\nСлово: {display}\nПопыток: 6",
        )
        return True
    
    elif game_type == "tic_tac_toe":
        board = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        active_games[chat_id] = {
            "type": "tic_tac_toe",
            "board": board,
            "turn": "X",
        }
        bot.send_message(
            chat_id,
            f"🎮 Крестики-нолики!\n{format_ttt_board(board)}\nХод: X",
        )
        return True
    
    return False


def _get_active_games():
    """Получить словарь active_games из games (ленивая загрузка)"""
    try:
        from games import active_games
        return active_games
    except ImportError:
        return None

# ============================================================
# 3. УГАДАЙ ЧИСЛО
# ============================================================

def process_number_guess(bot, chat_id, text, active_games):
    """
    Обработка игры 'Угадай число'.
    
    Returns:
        bool: True если игра обработала
    """
    if chat_id not in active_games:
        return False
    
    game = active_games[chat_id]
    
    if not text or not text.strip():
        bot.send_message(chat_id, "Введи число!")
        return True
    
    try:
        guess = int(text.strip())
    except ValueError:
        bot.send_message(chat_id, "❌ Это не число! Введи число от 1 до 100.")
        return True
    
    # Ограничение диапазона
    if guess < 1 or guess > 100:
        bot.send_message(chat_id, "❌ Число от 1 до 100!")
        return True
    
    game["attempts"] = game.get("attempts", 0) + 1
    
    if guess < game["number"]:
        bot.send_message(
            chat_id,
            f"Больше! ⬆️ (попытка {game['attempts']})",
        )
    elif guess > game["number"]:
        bot.send_message(
            chat_id,
            f"Меньше! ⬇️ (попытка {game['attempts']})",
        )
    else:
        bot.send_message(
            chat_id,
            f"🎉 Угадал за {game['attempts']} попыток!",
        )
        del active_games[chat_id]
    
    return True

# ============================================================
# 4. КАМЕНЬ-НОЖНИЦЫ-БУМАГА
# ============================================================

def process_rps(bot, chat_id, text, active_games):
    """Обработка игры 'Камень-ножницы-бумага'"""
    if chat_id not in active_games:
        return False
    
    if not text or not text.strip():
        bot.send_message(chat_id, "Напиши: камень, ножницы или бумага")
        return True
    
    choices = ["камень", "ножницы", "бумага"]
    text_lower = text.lower().strip()
    
    if text_lower not in choices:
        bot.send_message(
            chat_id,
            "❌ Напиши: камень, ножницы или бумага",
        )
        return True
    
    bot_choice = random.choice(choices)
    
    if text_lower == bot_choice:
        result = f"🤝 Ничья! У меня {bot_choice}"
    elif (
        (text_lower == "камень" and bot_choice == "ножницы")
        or (text_lower == "ножницы" and bot_choice == "бумага")
        or (text_lower == "бумага" and bot_choice == "камень")
    ):
        result = f"🎉 Ты выиграл! У меня {bot_choice}"
    else:
        result = f"😈 Я выиграла! У меня {bot_choice}"
    
    bot.send_message(chat_id, result)
    del active_games[chat_id]
    return True

# ============================================================
# 5. ВИСЕЛИЦА
# ============================================================

def process_hangman(bot, chat_id, text, active_games):
    """Обработка игры 'Виселица'"""
    if chat_id not in active_games:
        return False
    
    game = active_games[chat_id]
    
    if not text or not text.strip():
        bot.send_message(chat_id, "Введи одну букву!")
        return True
    
    text_lower = text.lower().strip()
    
    # Проверяем — одна буква
    if len(text_lower) != 1 or not text_lower.isalpha():
        bot.send_message(chat_id, "❌ Введи ОДНУ букву!")
        return True
    
    guessed = game.get("guessed", [])
    word = game.get("word", "")
    
    if text_lower in guessed:
        bot.send_message(
            chat_id,
            f"⚠️ Ты уже называл(а) букву '{text_lower}'!",
        )
        return True
    
    guessed.append(text_lower)
    game["guessed"] = guessed
    
    if text_lower not in word:
        game["attempts"] = game.get("attempts", 6) - 1
        bot.send_message(
            chat_id,
            f"❌ Нет такой буквы! Осталось попыток: {game['attempts']}",
        )
    else:
        bot.send_message(chat_id, "✅ Есть такая буква!")
    
    # Формируем отображение
    display = " ".join(
        [c if c in guessed else "_" for c in word]
    )
    
    # Проверяем проигрыш
    if game.get("attempts", 0) <= 0:
        bot.send_message(
            chat_id,
            f"💀 Ты проиграл! Загаданное слово: {word}",
        )
        del active_games[chat_id]
        return True
    
    # Проверяем победу
    if "_" not in display:
        bot.send_message(
            chat_id,
            f"🎉 Ты победил! Слово: {word}",
        )
        del active_games[chat_id]
        return True
    
    bot.send_message(
        chat_id,
        f"📝 Слово: {display}\n"
        f"💪 Осталось попыток: {game['attempts']}",
    )
    return True

# ============================================================
# 6. КРЕСТИКИ-НОЛИКИ
# ============================================================

def format_ttt_board(board):
    """Форматировать доску крестиков-ноликов"""
    if not board or len(board) < 9:
        return "❌ Неверная доска"
    
    return (
        f"{board[0]} | {board[1]} | {board[2]}\n"
        "---------\n"
        f"{board[3]} | {board[4]} | {board[5]}\n"
        "---------\n"
        f"{board[6]} | {board[7]} | {board[8]}"
    )


def check_ttt_win(board):
    """Проверить победу"""
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Горизонтали
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Вертикали
        [0, 4, 8], [2, 4, 6],              # Диагонали
    ]
    
    for win in wins:
        if (board[win[0]] == board[win[1]] == board[win[2]]
                and board[win[0]] in ("X", "O")):
            return True
    
    return False


def process_tic_tac_toe(bot, chat_id, text, active_games):
    """Обработка игры 'Крестики-нолики'"""
    if chat_id not in active_games:
        return False
    
    game = active_games[chat_id]
    
    if not text or not text.strip():
        bot.send_message(chat_id, "Введи число от 1 до 9!")
        return True
    
    try:
        pos = int(text.strip()) - 1
    except ValueError:
        bot.send_message(chat_id, "❌ Введи число от 1 до 9!")
        return True
    
    if pos < 0 or pos > 8:
        bot.send_message(chat_id, "❌ Введи число от 1 до 9!")
        return True
    
    board = game.get("board", [])
    if len(board) < 9:
        bot.send_message(chat_id, "❌ Ошибка доски")
        del active_games[chat_id]
        return True
    
    if board[pos] in ("X", "O"):
        bot.send_message(chat_id, "❌ Это место уже занято!")
        return True
    
    # Ставим ход
    turn = game.get("turn", "X")
    board[pos] = turn
    game["board"] = board
    
    # Проверяем победу
    if check_ttt_win(board):
        bot.send_message(
            chat_id,
            f"🎉 {turn} победил!\n{format_ttt_board(board)}",
        )
        del active_games[chat_id]
        return True
    
    # Проверяем ничью
    if all(cell in ("X", "O") for cell in board):
        bot.send_message(
            chat_id,
            f"🤝 Ничья!\n{format_ttt_board(board)}",
        )
        del active_games[chat_id]
        return True
    
    # Меняем ход
    game["turn"] = "O" if turn == "X" else "X"
    bot.send_message(
        chat_id,
        f"{format_ttt_board(board)}\n🎯 Ход: {game['turn']}",
    )
    return True

# ============================================================
# 7. ВСПОМОГАТЕЛЬНЫЕ
# ============================================================

def is_game_active(chat_id, active_games=None):
    """Проверить, есть ли активная игра"""
    if active_games is None:
        active_games = _get_active_games()
    
    if active_games is None:
        return False
    
    return chat_id in active_games


def end_game(chat_id, active_games=None):
    """Завершить игру"""
    if active_games is None:
        active_games = _get_active_games()
    
    if active_games is None:
        return False
    
    if chat_id in active_games:
        del active_games[chat_id]
        return True
    
    return False


def get_game_type(chat_id, active_games=None):
    """Получить тип активной игры"""
    if active_games is None:
        active_games = _get_active_games()
    
    if active_games is None or chat_id not in active_games:
        return None
    
    return active_games[chat_id].get("type")

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print("🎮 Игровой движок загружен (PC)")
print(f"🎮 Базовых игр: {len(BASE_GAMES)}")
print(f"📝 Слов для виселицы: {len(HANGMAN_WORDS)}")