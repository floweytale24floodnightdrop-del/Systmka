"""Обработчик команды 💟Отладка — запросы владельца, создание файлов, логи"""

import os
import re
import json
import time
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OWNER_IDS, OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

DEBUG_LOGS_DIR = "debug_logs"
DEBUG_HISTORY_FILE = "debug_history.json"

# Максимальная длина запроса
MAX_REQUEST_LENGTH = 5000

# Максимальный размер файла (KB)
MAX_FILE_SIZE_KB = 500

os.makedirs(DEBUG_LOGS_DIR, exist_ok=True)

# ============================================================
# 3. ДАННЫЕ
# ============================================================

debug_history = {
    "requests": [],
    "stats": {
        "total_requests": 0,
        "files_created": 0,
        "last_request": None,
    },
}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_debug_history():
    """Сохранить историю отладки"""
    try:
        with open(DEBUG_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(debug_history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории отладки: {e}")
        return False


def load_debug_history():
    """Загрузить историю отладки"""
    global debug_history
    try:
        if os.path.exists(DEBUG_HISTORY_FILE):
            with open(DEBUG_HISTORY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            if isinstance(loaded, dict):
                if isinstance(loaded.get("requests"), list):
                    debug_history["requests"] = loaded["requests"]
                
                if isinstance(loaded.get("stats"), dict):
                    debug_history["stats"].update(loaded["stats"])
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON отладки: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории отладки: {e}")
        return False


load_debug_history()

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    return OPENROUTER_KEY


def _safe_filename(name):
    """Привести имя файла к безопасному виду"""
    if not name:
        return None
    
    # Убираем опасные символы
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r'\.\.', "_", name)
    name = name.strip(". ")
    
    if len(name) > 100:
        name = name[:100]
    
    return name if name else None

# ============================================================
# 6. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def handle_debug_command(bot, message, text, chat_id, user):
    """
    Обработка команды 💟Отладка.
    
    Returns:
        bool: True если команда обработана
    """
    # Проверка прав
    if user.id not in OWNER_IDS:
        bot.reply_to(message, "❌ Только владелец может использовать команду отладки!")
        return True
    
    # Парсим команду
    parts = text.split('\n', 1)
    command = parts[0].strip() if parts else "💟Отладка"
    request_text = parts[1].strip() if len(parts) > 1 else ""
    
    if len(request_text) > MAX_REQUEST_LENGTH:
        request_text = request_text[:MAX_REQUEST_LENGTH]
    
    # Без запроса — показываем статус
    if not request_text:
        status = get_debug_status()
        bot.reply_to(message, status)
        return True
    
    # Обрабатываем запрос
    response = process_debug_request(request_text, user.id, chat_id)
    
    # Сохраняем в историю
    debug_history["requests"].append({
        "timestamp": datetime.now().isoformat(),
        "user_id": user.id,
        "request": request_text[:200],
        "response": str(response)[:200] if response else "",
        "file_created": (
            response.get("file_created", False)
            if isinstance(response, dict)
            else False
        ),
    })
    debug_history["stats"]["total_requests"] += 1
    debug_history["stats"]["last_request"] = datetime.now().isoformat()
    
    # Ограничиваем историю
    if len(debug_history["requests"]) > 200:
        debug_history["requests"] = debug_history["requests"][-200:]
    
    save_debug_history()
    
    # Отправляем ответ
    if isinstance(response, dict):
        if response.get("file_created"):
            bot.reply_to(
                message,
                f"✅ {response.get('message', 'Файл создан')}\n"
                f"📁 {response.get('filename', '')}"
            )
        else:
            bot.reply_to(message, response.get("message", "✅ Готово"))
    else:
        bot.reply_to(message, str(response)[:4000])
    
    return True

# ============================================================
# 7. ОБРАБОТКА ЗАПРОСА
# ============================================================

def process_debug_request(request_text, user_id, chat_id):
    """
    Обработать запрос отладки.
    
    Returns:
        dict или str
    """
    if not request_text:
        return "❌ Пустой запрос"
    
    request_lower = request_text.lower()
    
    # === Создание файла ===
    if any(word in request_lower for word in [
        "создай файл", "создать файл", "новый файл", "файл для",
    ]):
        return create_debug_file(request_text, user_id)
    
    # === Список групп ===
    if any(word in request_lower for word in [
        "групп", "чатов", "презентация", "список групп", "все группы",
    ]):
        return list_all_chats()
    
    # === Статистика ===
    if any(word in request_lower for word in [
        "статистика", "статус", "инфо", "информация",
    ]):
        return get_debug_status()
    
    # === Выполнение кода ===
    if any(word in request_lower for word in [
        "выполни код", "запусти код",
    ]):
        return execute_debug_code(request_text)
    
    # === Поиск в интернете ===
    if any(word in request_lower for word in [
        "поищи", "найди", "поиск", "гугл", "google",
    ]):
        return search_debug_internet(request_text)
    
    # === Анализ системы ===
    if any(word in request_lower for word in [
        "система", "системная", "проект", "файлы",
    ]):
        return analyze_system_debug(request_text)
    
    # === Общий запрос — через ИИ ===
    return process_with_ai(request_text)

# ============================================================
# 8. СОЗДАНИЕ ФАЙЛА
# ============================================================

def create_debug_file(request_text, user_id):
    """Создать файл с логом запроса"""
    # Извлекаем имя файла
    filename_match = re.search(
        r'(?:файл\s+)?["\']?([a-zA-Z0-9_\-\.]+)["\']?',
        request_text,
    )
    
    if not filename_match:
        filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    else:
        filename = _safe_filename(filename_match.group(1))
        if not filename:
            filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Расширение по умолчанию
        if not any(filename.endswith(ext) for ext in (".txt", ".md", ".py", ".json")):
            filename += ".txt"
    
    # Извлекаем содержимое
    content_match = re.search(
        r'(?:содержимым?:|текст?:|контент?:)\s*(.+?)(?:\n\n|$)',
        request_text,
        re.DOTALL,
    )
    
    if content_match:
        content = content_match.group(1).strip()
    else:
        content = generate_debug_content(request_text)
    
    if not content:
        content = "Пустой файл"
    
    # Ограничиваем размер
    max_size = MAX_FILE_SIZE_KB * 1024
    if len(content) > max_size:
        content = content[:max_size] + "\n\n... (обрезано)"
    
    # Формируем полное содержимое
    full_content = (
        f"=== ДЕБАГ-ФАЙЛ ===\n"
        f"Создан: {datetime.now().isoformat()}\n"
        f"Пользователь: {user_id}\n"
        f"Запрос: {request_text[:200]}\n\n"
        f"--- СОДЕРЖАНИЕ ---\n"
        f"{content}\n\n"
        f"--- КОНЕЦ ФАЙЛА ---\n"
    )
    
    # Сохраняем
    file_path = os.path.join(DEBUG_LOGS_DIR, filename)
    
    # Защита от path traversal
    real_path = os.path.realpath(file_path)
    logs_dir = os.path.realpath(DEBUG_LOGS_DIR)
    if not real_path.startswith(logs_dir):
        return {
            "file_created": False,
            "message": "❌ Недопустимый путь",
        }
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        debug_history["stats"]["files_created"] += 1
        save_debug_history()
        
        return {
            "file_created": True,
            "filename": filename,
            "message": f"Файл {filename} создан в {DEBUG_LOGS_DIR}/",
        }
    except Exception as e:
        return {
            "file_created": False,
            "message": f"❌ Ошибка создания файла: {e}",
        }

# ============================================================
# 9. ГЕНЕРАЦИЯ СОДЕРЖИМОГО
# ============================================================

def generate_debug_content(request_text):
    """Сгенерировать содержимое файла через ИИ"""
    key = _get_openrouter_key()
    if not key:
        return f"Запрос: {request_text}\n\n(ИИ недоступен)"
    
    try:
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
                        "content": (
                            "Ты Систмка. Ты создаёшь содержимое для файла "
                            "по запросу пользователя.\n"
                            "Пиши подробно, структурированно, с заголовками "
                            "и разделами.\n"
                            "Используй markdown если нужно.\n"
                            "Длина: 500-2000 слов."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Создай содержимое файла по запросу: {request_text}",
                    },
                ],
                "max_tokens": 1500,
                "temperature": 0.7,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка генерации содержимого: {e}")
    
    return f"Запрос: {request_text}\n\nСодержание не удалось сгенерировать."

# ============================================================
# 10. СПИСОК ГРУПП
# ============================================================

def list_all_chats():
    """Создать презентацию всех групп"""
    try:
        import database as db
        
        lines = ["📊 ПРЕЗЕНТАЦИЯ ГРУПП", "=" * 50, ""]
        
        if db.all_chats:
            lines.append(f"📋 Всего чатов: {len(db.all_chats)}")
            lines.append("")
            
            for chat_id, info in db.all_chats.items():
                title = info.get('title', 'Без названия')
                chat_type = info.get('type', 'unknown')
                member_count = info.get('member_count', 0)
                last_active = info.get('last_active', '?')
                
                lines.append(f"📌 {title}")
                lines.append(f"   ID: {chat_id}")
                lines.append(f"   Тип: {chat_type}")
                lines.append(f"   Участников: {member_count}")
                if last_active and last_active != '?':
                    lines.append(f"   Активен: {str(last_active)[:16]}")
                lines.append("")
        else:
            lines.append("❌ Нет активных чатов")
        
        lines.append("=" * 50)
        lines.append(f"🕐 Создано: {datetime.now().isoformat()}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Ошибка получения списка групп: {e}"

# ============================================================
# 11. ВЫПОЛНЕНИЕ КОДА
# ============================================================

def execute_debug_code(request_text):
    """Выполнить код из запроса"""
    try:
        from learning_core import execute_python_code
        
        # Извлекаем код
        code_match = re.search(
            r'(?:код[:\s]+|выполни\s+)(.+?)$',
            request_text,
            re.DOTALL | re.IGNORECASE,
        )
        
        if not code_match:
            return "❌ Не найден код для выполнения"
        
        code = code_match.group(1).strip()
        
        if not code:
            return "❌ Пустой код"
        
        result = execute_python_code(code, timeout=30)
        return f"📤 Результат:\n{result[:2000]}" if result else "✅ Выполнено"
    except Exception as e:
        return f"❌ Ошибка выполнения: {e}"

# ============================================================
# 12. ПОИСК В ИНТЕРНЕТЕ
# ============================================================

def search_debug_internet(request_text):
    """Поиск в интернете"""
    try:
        from self_learning import search_google_free
        
        query = re.sub(
            r'^(поищи|найди|поиск|гугл|google)\s*',
            '',
            request_text,
            flags=re.IGNORECASE,
        ).strip()
        
        if not query:
            return "❌ Пустой поисковый запрос"
        
        results = search_google_free(query)
        
        if results:
            lines = [f"🔍 РЕЗУЛЬТАТЫ ПОИСКА '{query}':"]
            for i, r in enumerate(results[:10], 1):
                lines.append(f"{i}. {r[:200]}")
            return "\n".join(lines)
        
        return f"❌ Ничего не найдено по '{query}'"
    except Exception as e:
        return f"❌ Ошибка поиска: {e}"

# ============================================================
# 13. АНАЛИЗ СИСТЕМЫ
# ============================================================

def analyze_system_debug(request_text):
    """Анализ системы"""
    try:
        from file_analyzer import format_file_stats, find_errors_in_files
        
        stats_text = format_file_stats()
        errors = find_errors_in_files()
        
        if errors:
            stats_text += f"\n\n❌ Найдено ошибок: {len(errors)}"
            for err in errors[:5]:
                stats_text += f"\n  • {err.get('file', '?')}: {err.get('error', '')[:80]}"
        
        return stats_text
    except Exception as e:
        return f"❌ Ошибка анализа: {e}"

# ============================================================
# 14. ОБРАБОТКА ЧЕРЕЗ ИИ
# ============================================================

def process_with_ai(request_text):
    """Обработать запрос через ИИ"""
    key = _get_openrouter_key()
    if not key:
        return f"🤖 Запрос: {request_text}\n\n(ИИ недоступен)"
    
    try:
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
                        "content": (
                            "Ты Систмка. Ты помогаешь с отладкой системы.\n"
                            "Отвечай подробно, структурированно.\n"
                            "Если запрос требует действий — опиши что нужно сделать.\n"
                            "Если запрос требует анализа — проанализируй.\n"
                            "Пиши как живой человек, без ИИ-шных фраз."
                        ),
                    },
                    {"role": "user", "content": request_text},
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка обработки через ИИ: {e}")
    
    return f"🤖 Запрос обработан:\n\n{request_text}\n\n(Ответ не удалось сгенерировать)"

# ============================================================
# 15. СТАТУС
# ============================================================

def get_debug_status():
    """Получить статус системы отладки"""
    lines = [
        "🔧 СТАТУС ОТЛАДКИ",
        "=" * 40,
        f"📊 Всего запросов: {debug_history['stats']['total_requests']}",
        f"📁 Создано файлов: {debug_history['stats']['files_created']}",
        f"🕐 Последний: {debug_history['stats']['last_request'] or 'никогда'}",
        f"📂 Папка логов: {DEBUG_LOGS_DIR}/",
        "",
        "📋 ПОСЛЕДНИЕ ЗАПРОСЫ:",
    ]
    
    for req in debug_history['requests'][-5:]:
        ts = req.get('timestamp', '?')[:16]
        r = req.get('request', '')[:50]
        lines.append(f"  • {ts}: {r}...")
    
    lines.append("=" * 40)
    lines.append("💡 Использование: 💟Отладка [запрос]")
    lines.append("   Примеры:")
    lines.append("   💟Отладка Создай файл для презентации групп")
    lines.append("   💟Отладка Покажи статистику")
    lines.append("   💟Отладка Поищи информацию про Python")
    
    return "\n".join(lines)

# ============================================================
# 16. ЗАГРУЗКА
# ============================================================

print("🔧 Модуль отладки загружен (PC)")
print(f"📊 Всего запросов: {debug_history['stats']['total_requests']}")
print(f"📁 Создано файлов: {debug_history['stats']['files_created']}")
print(f"📂 Папка логов: {DEBUG_LOGS_DIR}/")