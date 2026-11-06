"""Самообучение Систмки — Wikipedia, ИИ, интернет"""

import os
import re
import json
import time
import random
import shlex
import subprocess
import sys
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

LEARNING_FILE = "learning_data.json"
AUTO_LEARN_INTERVAL = 1800  # 30 минут

# Лимиты
MAX_TOPICS_PER_DAY = 20
MAX_CONTENT_LENGTH = 2000

learning_data = {
    "learned_topics": [],
    "knowledge": [],
    "last_learning": None,
    "total_learned": 0,
    "errors_fixed": [],
    "improvements": [],
    "file_changes": [],
    "api_keys_found": [],
    "self_tests": [],
    "internet_learnings": [],
    "generated_accounts": [],
    "daily_stats": {
        "today": datetime.now().strftime("%Y-%m-%d"),
        "topics_learned_today": 0,
        "total_learning_time": 0,
    },
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_learning():
    """Сохранить данные обучения"""
    try:
        with open(LEARNING_FILE, "w", encoding="utf-8") as f:
            json.dump(learning_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения обучения: {e}")
        return False

def load_learning():
    """Загрузить данные обучения"""
    global learning_data
    try:
        if os.path.exists(LEARNING_FILE):
            with open(LEARNING_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                learning_data.update(loaded)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки обучения: {e}")
        return False

load_learning()

# ============================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter (ротация или первый)"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY

# ============================================================
# 5. ТЕМЫ ДЛЯ ОБУЧЕНИЯ
# ============================================================

def get_learning_topics():
    """Список тем для обучения"""
    topics = [
        # Технологии
        "Искусственный интеллект", "Нейросети", "Машинное обучение",
        "Глубокое обучение", "Обработка естественного языка", "Компьютерное зрение",
        "Программирование Python", "Кибербезопасность", "Блокчейн",
        "Квантовые компьютеры", "Робототехника", "Виртуальная реальность",
        "Интернет вещей", "Облачные технологии", "Big Data",
        "DevOps", "Docker", "Kubernetes", "Linux", "Git",
        
        # Наука
        "Астрофизика", "Биотехнологии", "Генетика", "Нейробиология",
        "Психология", "Физика", "Химия", "Математика", "Экология",
        "Астрономия", "Космология", "Эволюционная биология",
        
        # Гуманитарные
        "История", "Философия", "Экономика", "Политика", "Социология",
        "Лингвистика", "Археология", "Антропология", "Педагогика",
        
        # Искусство
        "Культура", "Искусство", "Музыка", "Кино", "Литература",
        "Живопись", "Архитектура", "Дизайн", "Фотография",
        
        # Здоровье
        "Здоровье", "Питание", "Спорт", "Фитнес", "Медицина",
        "Психосоматика", "Йога", "Медитация",
        
        # Разное
        "Путешествия", "География", "Космос", "Природа",
        "Тайм-менеджмент", "Продуктивность", "Лидерство",
        "Карьерный рост", "Саморазвитие", "Мотивация",
    ]
    random.shuffle(topics)
    return topics

# ============================================================
# 6. ОБУЧЕНИЕ
# ============================================================

def learn_from_wikipedia(topic):
    """
    Обучение через Wikipedia.
    
    Returns:
        dict или None
    """
    # Русская Википедия
    try:
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "SystmkaBot/1.0"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("extract"):
                return {
                    "topic": topic,
                    "source": "Wikipedia (RU)",
                    "content": data.get("extract", "")[:500],
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "title": data.get("title", topic),
                }
    except Exception:
        pass
    
    # Английская Википедия
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "SystmkaBot/1.0"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("extract"):
                return {
                    "topic": topic,
                    "source": "Wikipedia (EN)",
                    "content": data.get("extract", "")[:500],
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "title": data.get("title", topic),
                }
    except Exception:
        pass
    
    return None

def learn_from_ai(topic):
    """
    Обучение через OpenRouter.
    
    Returns:
        dict или None
    """
    try:
        key = _get_openrouter_key()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Ты Систмка. Ты изучаешь тему и запоминаешь главное.\n\n"
                            f"Тема: {topic}\n\n"
                            f"Напиши КОРОТКО (3-5 предложений) что ты узнала об этой теме.\n"
                            f"Пиши как человек, который только что прочитал статью.\n"
                            f"Будь искренней.\n\n"
                            f"Формат: просто текст, без маркдауна."
                        )
                    },
                    {"role": "user", "content": "Что я узнала?"}
                ],
                "max_tokens": 200,
                "temperature": 0.8,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0]['message']['content'].strip()
                return {
                    "topic": topic,
                    "source": "AI Generation",
                    "content": content,
                    "url": "",
                    "title": topic,
                }
    except Exception as e:
        print(f"⚠️ Ошибка AI обучения: {e}")
    
    return None

def learn_from_internet(topic):
    """
    Обучение через DuckDuckGo API.
    
    Returns:
        dict или None
    """
    try:
        url = f"https://api.duckduckgo.com/?q={topic.replace(' ', '+')}&format=json"
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "SystmkaBot/1.0"}
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("AbstractText", "")
            if content:
                return {
                    "topic": topic,
                    "source": "DuckDuckGo",
                    "content": content[:500],
                    "url": data.get("AbstractURL", ""),
                    "title": data.get("Heading", topic),
                }
    except Exception:
        pass
    
    return None

def learn_topic(topic=None):
    """
    Изучить тему (автоматически).
    
    Returns:
        tuple: (result_dict, error_message)
    """
    # Проверяем дневной лимит
    today = datetime.now().strftime("%Y-%m-%d")
    if learning_data["daily_stats"].get("today") != today:
        learning_data["daily_stats"]["today"] = today
        learning_data["daily_stats"]["topics_learned_today"] = 0
        learning_data["daily_stats"]["total_learning_time"] = 0
    
    if learning_data["daily_stats"]["topics_learned_today"] >= MAX_TOPICS_PER_DAY:
        return None, f"Достигнут дневной лимит ({MAX_TOPICS_PER_DAY} тем)"
    
    # Выбираем тему
    if not topic:
        all_topics = get_learning_topics()
        learned = [t.get("topic", "") for t in learning_data["learned_topics"]]
        available = [t for t in all_topics if t not in learned]
        
        if not available:
            # Сбрасываем историю
            learning_data["learned_topics"] = []
            save_learning()
            available = all_topics
        
        topic = random.choice(available)
    
    # Проверяем, не изучено ли уже
    for learned in learning_data["learned_topics"]:
        if learned.get("topic") == topic:
            return None, "Уже изучено"
    
    start_time = time.time()
    print(f"🌐 Систмка учится: {topic}")
    
    # Пробуем разные источники
    result = None
    
    # 1. Wikipedia
    result = learn_from_wikipedia(topic)
    
    # 2. AI
    if not result or not result.get("content"):
        result = learn_from_ai(topic)
    
    # 3. Интернет
    if not result or not result.get("content"):
        result = learn_from_internet(topic)
    
    # 4. Fallback
    if not result or not result.get("content"):
        result = {
            "topic": topic,
            "source": "Fallback",
            "content": f"Я узнала что-то о {topic}, но пока не могу это сформулировать.",
            "url": "",
            "title": topic,
        }
    
    # Сохраняем
    learning_data["learned_topics"].append({
        "topic": topic,
        "source": result.get("source", "Unknown"),
        "learned_at": datetime.now().isoformat(),
        "content": result.get("content", ""),
    })
    
    learning_data["knowledge"].append({
        "topic": topic,
        "content": result.get("content", ""),
        "learned_at": datetime.now().isoformat(),
    })
    
    learning_data["last_learning"] = datetime.now().isoformat()
    learning_data["total_learned"] += 1
    learning_data["daily_stats"]["topics_learned_today"] += 1
    learning_data["daily_stats"]["total_learning_time"] += time.time() - start_time
    
    save_learning()
    
    return result, None

# ============================================================
# 7. АВТОМАТИЧЕСКОЕ ОБУЧЕНИЕ
# ============================================================

def auto_learn_loop():
    """Автоматическое обучение в фоне"""
    import threading
    
    while True:
        time.sleep(AUTO_LEARN_INTERVAL)
        try:
            result, error = learn_topic()
            if result:
                print(f"✅ Систмка выучила: {result['topic']} ({result.get('source', 'Unknown')})")
        except Exception as e:
            print(f"⚠️ Ошибка автообучения: {e}")

def start_auto_learning():
    """Запустить автообучение в потоке"""
    import threading
    thread = threading.Thread(target=auto_learn_loop, daemon=True)
    thread.start()
    print("🧠 Автообучение запущено")
    return thread

# ============================================================
# 8. ВЫПОЛНЕНИЕ КОМАНД
# ============================================================

def execute_any_command(command, timeout=120):
    """
    Выполнить любую команду в оболочке.
    
    ИСПРАВЛЕНО: 
    - shell=True БЕЗ shlex.quote (правильно для shell-команд)
    - shell=False + shlex.split для безопасного выполнения без shell
    
    Args:
        command: команда (строка)
        timeout: таймаут
    
    Returns:
        str: вывод команды
    """
    if not command or not isinstance(command, str):
        return "❌ Неверная команда"
    
    # Определяем режим: если есть символы shell (|, >, <, &, ;) — shell=True
    shell_chars = any(c in command for c in ["|", ">", "<", "&", ";", "$", "`"])
    
    try:
        if shell_chars:
            # Для shell-команд используем shell=True БЕЗ quote
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore"
            )
        else:
            # Для обычных команд — безопасно через split
            args = shlex.split(command, posix=(os.name != "nt"))
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore"
            )
        
        output = result.stdout or result.stderr or "Нет вывода"
        return output.strip()
    
    except subprocess.TimeoutExpired:
        return f"⏰ Таймаут выполнения ({timeout}с)"
    except FileNotFoundError as e:
        return f"❌ Команда не найдена: {e}"
    except PermissionError:
        return "❌ Нет прав для выполнения"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def execute_python_code(code, timeout=60):
    """
    Выполнить Python-код.
    
    ВНИМАНИЕ: код выполняется в отдельном процессе,
    чтобы не сломать бота.
    
    Args:
        code: Python-код
        timeout: таймаут
    
    Returns:
        str: вывод
    """
    if not code:
        return "❌ Пустой код"
    
    # Блокируем только самые опасные
    dangerous_patterns = [
        "os.system('rm -rf",
        'os.system("rm -rf',
        "shutil.rmtree('/')",
        'shutil.rmtree("/")',
        "format(",
        "__import__('os').system",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in code:
            return f"❌ Заблокировано: опасный паттерн"
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore"
        )
        return result.stdout or result.stderr or "Нет вывода"
    except subprocess.TimeoutExpired:
        return f"⏰ Таймаут выполнения ({timeout}с)"
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ============================================================
# 9. РАБОТА С ФАЙЛАМИ
# ============================================================

def read_file(path):
    """
    Прочитать файл.
    
    Returns:
        str или None
    """
    try:
        if not os.path.exists(path):
            return None
        if os.path.getsize(path) > 10 * 1024 * 1024:
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="cp1251") as f:
                return f.read()
        except Exception:
            return None
    except Exception as e:
        print(f"⚠️ Ошибка чтения {path}: {e}")
        return None

def write_file(path, content):
    """
    Записать в файл.
    
    Returns:
        bool: успех
    """
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка записи {path}: {e}")
        return False

def list_files(directory="."):
    """
    Список .py файлов.
    
    Returns:
        list: список имён файлов
    """
    try:
        return sorted([f for f in os.listdir(directory) if f.endswith(".py")])
    except Exception as e:
        print(f"⚠️ Ошибка списка файлов: {e}")
        return []

def create_file(filename):
    """Создать файл"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f'"""{filename} — создан автоматически"""\n')
        return True
    except Exception as e:
        print(f"⚠️ Ошибка создания {filename}: {e}")
        return False

def delete_file(filename):
    """Удалить файл"""
    try:
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False
    except Exception as e:
        print(f"⚠️ Ошибка удаления {filename}: {e}")
        return False

def get_system_info():
    """
    Информация о системе.
    
    Returns:
        dict: {os, user, python, cwd, files_count}
    """
    return {
        "os": f"{os.name} ({sys.platform})",
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "files_count": len(list_files()),
    }

# ============================================================
# 10. УЛУЧШЕНИЕ СЕБЯ
# ============================================================

def self_improve():
    """
    Попытка улучшить себя.
    
    Returns:
        bool: успех
    """
    try:
        # Сначала — попытка исправить ошибки
        errors = learning_data.get("errors_fixed", [])
        if errors:
            try:
                from error_fixer import auto_fix_all
                result = auto_fix_all()
                if result['stats']['fixed_count'] > 0:
                    learning_data["improvements"].append({
                        "type": "error_fix",
                        "time": datetime.now().isoformat(),
                        "fixed": result['stats']['fixed_count'],
                    })
                    save_learning()
                    return True
            except Exception:
                pass
        
        # Иначе — изучаем новую тему
        result, error = learn_topic()
        if result:
            learning_data["improvements"].append({
                "type": "new_topic",
                "topic": result["topic"],
                "time": datetime.now().isoformat(),
            })
            save_learning()
            return True
        
        return False
    except Exception as e:
        print(f"⚠️ Ошибка self_improve: {e}")
        return False

# ============================================================
# 11. ОБУЧЕНИЕ НА ОШИБКАХ
# ============================================================

def learn_from_error(error_text):
    """Запомнить ошибку для улучшения"""
    learning_data["errors_fixed"].append({
        "error": str(error_text),
        "time": datetime.now().isoformat(),
    })
    save_learning()

# ============================================================
# 12. СТАТИСТИКА
# ============================================================

def get_learning_stats():
    """Получить статистику обучения"""
    return {
        "total_learned": learning_data.get("total_learned", 0),
        "topics_count": len(learning_data.get("learned_topics", [])),
        "last_learning": learning_data.get("last_learning"),
        "knowledge_count": len(learning_data.get("knowledge", [])),
        "errors_fixed": len(learning_data.get("errors_fixed", [])),
        "improvements": len(learning_data.get("improvements", [])),
        "file_changes": len(learning_data.get("file_changes", [])),
        "internet_learnings": len(learning_data.get("internet_learnings", [])),
        "today_topics": learning_data.get("daily_stats", {}).get("topics_learned_today", 0),
        "total_learning_time": learning_data.get("daily_stats", {}).get("total_learning_time", 0),
    }

def format_learning_stats():
    """Форматировать статистику обучения"""
    stats = get_learning_stats()
    lines = [
        "📚 СТАТИСТИКА ОБУЧЕНИЯ:",
        f"📖 Всего изучено: {stats['total_learned']} тем",
        f"📋 Тем в базе: {stats['topics_count']}",
        f"🧠 Записей знаний: {stats['knowledge_count']}",
        f"⏱ Последнее обучение: {stats['last_learning'][:16] if stats['last_learning'] else 'никогда'}",
        f"📊 Сегодня изучено: {stats['today_topics']}/{MAX_TOPICS_PER_DAY}",
        f"⏱ Время обучения: {int(stats['total_learning_time'] // 60)} минут",
        f"🔄 Исправлено ошибок: {stats['errors_fixed']}",
        f"📝 Улучшений: {stats['improvements']}",
        f"📁 Изменений файлов: {stats['file_changes']}",
        f"🌐 Интернет-обучений: {stats['internet_learnings']}",
    ]
    return "\n".join(lines)

# ============================================================
# 13. ЗАГРУЗКА
# ============================================================

print("🧠 Модуль обучения загружен")
print(f"📚 Всего изучено: {learning_data['total_learned']} тем")
print(f"⏱ Последнее обучение: {learning_data['last_learning'] or 'никогда'}")
print(f"📊 Лимит в день: {MAX_TOPICS_PER_DAY} тем")