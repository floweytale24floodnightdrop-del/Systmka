"""Learning Core — автообучение, выполнение команд, работа с файлами"""

import os
import sys
import subprocess
import shlex
import threading
import time
from datetime import datetime
from self_learning import learn_topic, save_learning, learning_data

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

AUTO_LEARN_INTERVAL = 1800

# ============================================================
# 2. АВТОМАТИЧЕСКОЕ ОБУЧЕНИЕ
# ============================================================

def auto_learn_loop():
    """Автоматическое обучение в фоне"""
    while True:
        time.sleep(AUTO_LEARN_INTERVAL)
        try:
            result, error = learn_topic()
            if result:
                print(f"✅ Систмка выучила: {result['topic']}")
            else:
                print(f"⚠️ Не удалось выучить тему: {error}")
        except Exception as e:
            print(f"⚠️ Ошибка автообучения: {e}")

def start_auto_learning():
    """Запустить автообучение в потоке"""
    thread = threading.Thread(target=auto_learn_loop, daemon=True)
    thread.start()
    print("🧠 Автообучение запущено")
    return thread

# ============================================================
# 3. БЕЗОПАСНОЕ ВЫПОЛНЕНИЕ
# ============================================================

def execute_any_command(command):
    """Выполнить любую команду в оболочке"""
    try:
        safe_command = shlex.quote(command) if isinstance(command, str) else command
        result = subprocess.run(
            safe_command if isinstance(safe_command, str) else command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.stdout or result.stderr or "Нет вывода"
    except:
        return "Ошибка выполнения"

def execute_python_code(code):
    """Выполнить Python код (с ограничениями)"""
    try:
        dangerous = ["os.system", "subprocess", "eval(", "exec(", "__import__"]
        for danger in dangerous:
            if danger in code:
                return "❌ Код содержит опасные операции"
        
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout or result.stderr or "Нет вывода"
    except:
        return "Ошибка выполнения"

# ============================================================
# 4. РАБОТА С ФАЙЛАМИ
# ============================================================

def read_file(path):
    """Прочитать файл"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None

def write_file(path, content):
    """Записать в файл"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except:
        return False

def list_files():
    """Список .py файлов"""
    return [f for f in os.listdir(".") if f.endswith(".py")]

def create_file(filename):
    """Создать файл"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f'"""{filename} — создан автоматически"""\n')
        return True
    except:
        return False

def delete_file(filename):
    """Удалить файл"""
    try:
        os.remove(filename)
        return True
    except:
        return False

def get_system_info():
    """Информация о системе"""
    return {
        "os": execute_any_command("uname -a"),
        "user": execute_any_command("whoami"),
        "python": execute_any_command("python --version"),
        "storage": execute_any_command("df -h"),
    }

# ============================================================
# 5. УЛУЧШЕНИЕ СЕБЯ
# ============================================================

def self_improve():
    """Попытка улучшить себя"""
    try:
        # Анализируем ошибки
        errors = learning_data.get("errors_fixed", [])
        if errors:
            last_error = errors[-1].get("error", "")
            if last_error:
                # Пытаемся исправить
                from error_fixer import auto_fix_all
                result = auto_fix_all()
                if result['stats']['fixed_count'] > 0:
                    learning_data["improvements"].append({
                        "type": "error_fix",
                        "time": datetime.now().isoformat(),
                        "fixed": result['stats']['fixed_count']
                    })
                    save_learning()
                    return True
        
        # Изучаем новую тему
        result, error = learn_topic()
        if result:
            learning_data["improvements"].append({
                "type": "new_topic",
                "topic": result["topic"],
                "time": datetime.now().isoformat()
            })
            save_learning()
            return True
        
        return False
    except:
        return False

print("🧠 Learning Core загружен")
print(f"📚 Автообучение: {'запущено' if start_auto_learning() else 'ошибка'}")