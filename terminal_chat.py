"""Общение с Систмкой в командной строке — PC-версия (Windows/Linux/macOS)"""

import sys
import os
import time
import platform
import threading
import requests
from datetime import datetime

# ============================================================
# 1. ЦВЕТА (ANSI — работают в Windows 10+ с включённым VT)
# ============================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    PURPLE = '\033[35m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Включаем ANSI на Windows
if platform.system() == "Windows":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def print_color(text, color=Colors.GREEN, end="\n"):
    """Печать цветным текстом"""
    print(f"{color}{text}{Colors.END}", end=end)

# ============================================================
# 2. ОСНОВНОЙ ЦИКЛ (Windows-совместимый)
# ============================================================

def terminal_chat_loop(bot, owner_ids):
    """
    Цикл чтения ввода из консоли.
    
    В отличие от Android-версии (select.select) — использует
    блокирующий input() в отдельном потоке, что работает на Windows.
    """
    
    print_color("=" * 60, Colors.PURPLE)
    print_color("💬 ТЕРМИНАЛ-ЧАТ АКТИВИРОВАН", Colors.BOLD + Colors.PURPLE)
    print_color("=" * 60, Colors.PURPLE)
    print("")
    print_color("📋 КОМАНДЫ:", Colors.CYAN)
    print_color("  /msg <текст>  - отправить сообщение Систмке", Colors.GREEN)
    print_color("  /status       - статус бота", Colors.GREEN)
    print_color("  /system       - система", Colors.GREEN)
    print_color("  /processes    - топ процессов", Colors.GREEN)
    print_color("  /network      - сеть и IP", Colors.GREEN)
    print_color("  /apps         - запущенные приложения", Colors.GREEN)
    print_color("  /fix          - исправить ошибки", Colors.GREEN)
    print_color("  /emotions     - эмоции", Colors.GREEN)
    print_color("  /personality  - характер", Colors.GREEN)
    print_color("  /dreams       - мечты и страхи", Colors.GREEN)
    print_color("  /memes        - мемы", Colors.GREEN)
    print_color("  /opinions     - мнения о людях", Colors.GREEN)
    print_color("  /help         - эта справка", Colors.GREEN)
    print_color("  /restart      - перезапуск", Colors.GREEN)
    print_color("  /stop         - остановка", Colors.GREEN)
    print_color("=" * 60, Colors.PURPLE)
    print()
    
    # Флаг для остановки
    stop_flag = {"stop": False}
    
    def input_loop():
        """Цикл чтения ввода (в отдельном потоке)"""
        while not stop_flag["stop"]:
            try:
                user_input = input()
                
                if not user_input.strip():
                    continue
                
                process_input(user_input, bot, owner_ids, stop_flag)
                
            except EOFError:
                stop_flag["stop"] = True
                break
            except KeyboardInterrupt:
                stop_flag["stop"] = True
                break
            except Exception as e:
                print_color(f"❌ Ошибка ввода: {e}", Colors.RED)
                time.sleep(1)
    
    # Запускаем поток чтения
    input_thread = threading.Thread(target=input_loop, daemon=True)
    input_thread.start()
    
    # Основной поток просто ждёт
    try:
        while not stop_flag["stop"]:
            time.sleep(1)
    except KeyboardInterrupt:
        print_color("\n👋 Остановлено пользователем", Colors.YELLOW)
        stop_flag["stop"] = True

# ============================================================
# 3. ОБРАБОТКА ВВОДА
# ============================================================

def process_input(user_input, bot, owner_ids, stop_flag):
    """Обработать введённую команду"""
    
    user_input = user_input.strip()
    
    if user_input == "/stop":
        print_color("👋 Остановка...", Colors.RED)
        stop_flag["stop"] = True
        os._exit(0)
    
    if user_input == "/restart":
        print_color("🔄 Перезапуск...", Colors.YELLOW)
        python = sys.executable
        os.execl(python, python, "bot.py")
        return
    
    if user_input == "/help":
        show_help()
        return
    
    if user_input == "/status":
        show_status()
        return
    
    if user_input == "/system":
        show_system()
        return
    
    if user_input == "/processes":
        show_processes()
        return
    
    if user_input == "/network":
        show_network()
        return
    
    if user_input == "/apps":
        show_apps()
        return
    
    if user_input == "/fix":
        fix_errors()
        return
    
    if user_input == "/emotions":
        show_emotions()
        return
    
    if user_input == "/personality":
        show_personality()
        return
    
    if user_input == "/dreams":
        show_dreams()
        return
    
    if user_input == "/memes":
        show_memes()
        return
    
    if user_input == "/opinions":
        show_opinions()
        return
    
    # Сообщение Систмке
    if user_input.startswith("/msg "):
        message = user_input.replace("/msg ", "")
    else:
        message = user_input
    
    print_color("Систмка > ", Colors.PURPLE, end="")
    answer = ask_systmka(message)
    if answer:
        print_color(answer, Colors.CYAN)
    else:
        print_color("Не получилось ответить", Colors.RED)
    print()

# ============================================================
# 4. СПРАВКА
# ============================================================

def show_help():
    """Показать справку"""
    print_color("=" * 60, Colors.CYAN)
    print_color("📋 КОМАНДЫ ТЕРМИНАЛ-ЧАТА:", Colors.BOLD + Colors.CYAN)
    print_color("=" * 60, Colors.CYAN)
    print_color("  /msg <текст>  — отправить сообщение Систмке", Colors.GREEN)
    print_color("  /status       — статус бота", Colors.GREEN)
    print_color("  /system       — информация о системе", Colors.GREEN)
    print_color("  /processes    — топ процессов", Colors.GREEN)
    print_color("  /network      — сеть и IP", Colors.GREEN)
    print_color("  /apps         — запущенные приложения", Colors.GREEN)
    print_color("  /fix          — исправить ошибки", Colors.GREEN)
    print_color("  /emotions     — эмоции Систмки", Colors.GREEN)
    print_color("  /personality  — характер Систмки", Colors.GREEN)
    print_color("  /dreams       — мечты и страхи", Colors.GREEN)
    print_color("  /memes        — мемы", Colors.GREEN)
    print_color("  /opinions     — мнения о людях", Colors.GREEN)
    print_color("  /help         — эта справка", Colors.GREEN)
    print_color("  /restart      — перезапуск бота", Colors.GREEN)
    print_color("  /stop         — остановка бота", Colors.GREEN)
    print_color("=" * 60, Colors.CYAN)
    print()

# ============================================================
# 5. СИСТЕМНЫЕ КОМАНДЫ
# ============================================================

def show_status():
    """Статус бота"""
    try:
        from network_monitor import check_internet_speed
        speed = check_internet_speed()
        print_color(
            f"\n🌐 Интернет: {'OK' if speed.get('online') else 'FAIL'}",
            Colors.GREEN if speed.get('online') else Colors.RED
        )
        print_color(f"⚡ Пинг: {speed.get('ping_ms', '?')}мс\n", Colors.YELLOW)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_system():
    """Информация о системе"""
    try:
        from system_control import system_control
        print_color(system_control.format_status(), Colors.MAGENTA)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_processes():
    """Топ процессов"""
    try:
        from system_control import system_control
        print_color(system_control.format_processes(10), Colors.CYAN)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_network():
    """Сеть и IP"""
    try:
        from system_control import system_control
        print_color(system_control.format_network(), Colors.CYAN)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_apps():
    """Запущенные приложения"""
    try:
        from app_controller import format_running_apps
        print_color(format_running_apps(10), Colors.CYAN)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def fix_errors():
    """Исправить ошибки"""
    try:
        print_color("🔧 Исправляю...", Colors.YELLOW)
        from error_fixer import auto_fix_all
        results = auto_fix_all()
        print_color(f"Исправлено: {results['stats']['fixed_count']}", Colors.GREEN)
        print_color(f"Не исправлено: {results['stats']['failed_count']}", Colors.RED)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_emotions():
    """Эмоции"""
    try:
        from emotions import format_emotions
        print_color(format_emotions(), Colors.MAGENTA)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_personality():
    """Характер"""
    try:
        from personality import format_personality
        print_color(format_personality(), Colors.MAGENTA)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_dreams():
    """Мечты и страхи"""
    try:
        from dreams import format_all
        print_color(format_all(), Colors.PURPLE)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_memes():
    """Мемы"""
    try:
        from memes import format_meme_stats
        print_color(format_meme_stats(), Colors.CYAN)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

def show_opinions():
    """Мнения о людях"""
    try:
        from opinions import format_all_opinions
        print_color(format_all_opinions(), Colors.MAGENTA)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", Colors.RED)

# ============================================================
# 6. ЗАПРОС К СИСТМКЕ
# ============================================================

def ask_systmka(message):
    """Спросить Систмку через ИИ"""
    try:
        from system_prompt import SYSTEM_PROMPT
        from config import OPENROUTER_KEYS, OPENROUTER_KEY
        from personality import get_personality_for_prompt
        
        key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT + get_personality_for_prompt()
                    },
                    {"role": "user", "content": message}
                ],
                "max_tokens": 200,
                "temperature": 0.8,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print_color(f"Ошибка запроса: {e}", Colors.RED)
    return None

# ============================================================
# 7. ЗАГРУЗКА
# ============================================================

print("💬 Терминал-чат загружен (PC)")
print(f"💻 ОС: {platform.system()} {platform.release()}")