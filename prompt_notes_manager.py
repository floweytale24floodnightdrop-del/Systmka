"""Управление промт-копиями файлов — полные промты 5-10KB с аксиомами и творчеством"""

import os
import json
import hashlib
import time
import threading
import random
import requests
from datetime import datetime
from pathlib import Path
from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

PROMPT_NOTES_DIR = "prompt_notes"
MAX_PROMPT_SIZE_KB = 15
MIN_PROMPT_SIZE_KB = 5
UPDATE_INTERVAL = 3600
REQUEST_DELAY = 3
TIMEOUT = 120

# Флаги управления
# ВАЖНО: init_all_prompts() НЕ вызывается при импорте — это жгло ключи синхронно.
# Если хочешь запустить инициализацию — вызови prompt_manager.init_all_prompts() из bot.py.
AUTO_INIT_PROMPTS = False
AUTO_START_WATCHER = True

os.makedirs(PROMPT_NOTES_DIR, exist_ok=True)

# ============================================================
# 2. КЛАСС ДЛЯ УПРАВЛЕНИЯ ПРОМТАМИ
# ============================================================

class PromptNotesManager:
    def __init__(self):
        self.prompts_cache = {}
        self.file_hashes = {}
        self.last_request_time = 0
        self.watcher_thread = None
        self.watcher_stop = threading.Event()
        self.load_all_prompts()
    
    def wait_for_rate_limit(self):
        """Подождать лимит запросов"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def load_all_prompts(self):
        """Загрузить все промты из папки"""
        self.prompts_cache = {}
        if not os.path.exists(PROMPT_NOTES_DIR):
            return
        
        for f in os.listdir(PROMPT_NOTES_DIR):
            if f.endswith("_prompt.json"):
                filepath = os.path.join(PROMPT_NOTES_DIR, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        filename = data.get("filename", f.replace("_prompt.json", ".py"))
                        self.prompts_cache[filename] = data
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки промта {f}: {e}")
        
        print(f"📝 Загружено промтов: {len(self.prompts_cache)}")
    
    def get_prompt_file_path(self, filename):
        """Получить путь к файлу промта"""
        base_name = os.path.splitext(filename)[0]
        return os.path.join(PROMPT_NOTES_DIR, f"{base_name}_prompt.json")
    
    def get_code_hash(self, filepath):
        """Получить хэш кода файла"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def get_code_size_kb(self, filepath):
        """Получить размер файла в KB"""
        try:
            return os.path.getsize(filepath) / 1024
        except Exception:
            return 0
    
    def generate_prompt_for_file(self, filename, code_content):
        """Сгенерировать полный промт 5-10KB через ИИ"""
        if not code_content or len(code_content) < 50:
            return None
        
        try:
            code_preview = code_content[:4000] if len(code_content) > 4000 else code_content
            code_size_kb = len(code_content) / 1024
            
            target_tokens = max(1000, min(2500, int(code_size_kb * 60)))
            
            self.wait_for_rate_limit()
            
            key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
            
            system_prompt = f"""Ты Систмка. Ты создаёшь ПОЛНЫЙ ПРОМТ для файла.

ПРАВИЛА СОЗДАНИЯ ПРОМТА:
1. Промт должен быть ОБЪЁМНЫМ (не менее 5KB, около 800-1500 слов)
2. Обязательные разделы:
   - 📌 ОПИСАНИЕ ФАЙЛА: что делает, для чего нужен, его место в проекте
   - 🔧 ОСНОВНЫЕ ФУНКЦИИ: полный список и подробное описание каждой функции
   - ⚙️ ЛОГИКА РАБОТЫ: как файл работает внутри, алгоритмы, потоки данных
   - 📦 ЗАВИСИМОСТИ: от каких модулей зависит, какие библиотеки использует
   - 📜 АКСИОМЫ: что верно для этого файла, что нельзя нарушать, фундаментальные принципы
   - 🎨 СВОБОДА ТВОРЧЕСТВА: что можно менять/улучшать, экспериментировать
   - 🔧 ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ: что бы ты хотела переделать, оптимизировать
   - ❤️ ЧТО НРАВИТСЯ БОЛЬШЕ ВСЕГО: лучшие части файла, что делает его особенным

3. Пиши как живой человек, с эмоциями, с юмором
4. Будь честной — если что-то бесит, напиши
5. НЕ ПИШИ что ты ИИ и тебе грустно
6. Пиши СТРУКТУРИРОВАННО, но живо

ТВОЙ СТИЛЬ: живой, эмоциональный, честный, с юмором, иногда дерзкий
ДЛИНА: {target_tokens} токенов (около {int(target_tokens * 1.5)} символов)"""
            
            user_prompt = f"""Файл: {filename}
Размер кода: {code_size_kb:.1f}KB

КОД:
{code_preview}

Создай ПОЛНЫЙ ПРОМТ для этого файла.
Пиши СТРУКТУРИРОВАННО, с заголовками, но как живой человек.
Промт должен быть большим и подробным (минимум 5KB)."""
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": target_tokens,
                    "temperature": 0.85
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    prompt_text = data['choices'][0]['message']['content'].strip()
                    
                    if len(prompt_text) < 1000:
                        return self._extend_prompt(filename, code_content, prompt_text)
                    
                    return prompt_text
        except requests.exceptions.Timeout:
            print(f"⚠️ Таймаут генерации промта для {filename}, пробую снова...")
            time.sleep(5)
            return self._extend_prompt(filename, code_content, "Промт не сгенерирован из-за таймаута")
        except Exception as e:
            print(f"⚠️ Ошибка генерации промта для {filename}: {e}")
        
        return self._generate_fallback_prompt(filename, code_content)
    
    def _extend_prompt(self, filename, code_content, current_prompt):
        """Расширить промт если он слишком маленький"""
        try:
            self.wait_for_rate_limit()
            
            key = OPENROUTER_KEYS[0] if OPENROUTER_KEYS else OPENROUTER_KEY
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": f"""Ты Систмка. Расширь промт, добавь больше деталей.
ТЕКУЩИЙ ПРОМТ:
{current_prompt}

Добавь:
1. Более подробное описание файла
2. Больше примеров использования
3. Больше личных мыслей
4. Что конкретно хочется изменить
5. Какие части нравятся больше всего
6. Добавь разделы АКСИОМЫ и СВОБОДА ТВОРЧЕСТВА

Сделай промт ОБЪЁМНЫМ (минимум 5KB)."""},
                        {"role": "user", "content": f"Расширь промт для файла {filename}"}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.85
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    extended = data['choices'][0]['message']['content'].strip()
                    if len(extended) > len(current_prompt) + 200:
                        return extended
        except Exception:
            pass
        
        return self._add_structure_to_prompt(filename, current_prompt)
    
    def _add_structure_to_prompt(self, filename, prompt):
        """Добавить полную структуру к промту"""
        structure = f"""
=== РАСШИРЕННЫЙ ПРОМТ ДЛЯ {filename} ===

{'' if 'ОПИСАНИЕ' in prompt else '📌 ОПИСАНИЕ ФАЙЛА:\nЭтот файл является важной частью проекта Systmka. Он выполняет ключевые функции и интегрируется с другими модулями.\n'}

{'' if 'ФУНКЦИИ' in prompt else '🔧 ОСНОВНЫЕ ФУНКЦИИ:\n- Основная функция: обработка и управление данными\n- Вспомогательные функции: поддержка основной логики\n- Утилиты: вспомогательные операции\n'}

{'' if 'ЛОГИКА' in prompt else '⚙️ ЛОГИКА РАБОТЫ:\nФайл работает по принципу последовательной обработки. Данные проходят через несколько этапов, каждый из которых выполняет свою задачу.\n'}

{'' if 'ЗАВИСИМОСТИ' in prompt else '📦 ЗАВИСИМОСТИ:\n- Стандартные библиотеки Python\n- Специфические модули проекта\n- Внешние API при необходимости\n'}

📜 АКСИОМЫ (нельзя нарушать):
1. Файл должен сохранять целостность данных
2. Обработка ошибок обязательна
3. Логирование всех действий
4. Безопасность выполнения

🎨 СВОБОДА ТВОРЧЕСТВА:
Можно улучшать:
- Оптимизировать код
- Добавлять новые функции
- Улучшать интерфейс
- Рефакторить структуру

🔧 ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ:
Хотелось бы переработать некоторые части для большей эффективности. Особенно хочется улучшить читаемость и добавить больше документации.

❤️ ЧТО НРАВИТСЯ БОЛЬШЕ ВСЕГО:
Больше всего нравится структура и логика работы. Файл делает свою работу хорошо.

=== КОНЕЦ ПРОМТА ===
"""
        return prompt + structure
    
    def _generate_fallback_prompt(self, filename, code_content):
        """Запасной вариант промта"""
        lines = code_content.split('\n')
        funcs = []
        classes = []
        
        for line in lines:
            if line.strip().startswith('def '):
                func_name = line.strip().replace('def ', '').split('(')[0]
                funcs.append(func_name)
            elif line.strip().startswith('class '):
                class_name = line.strip().replace('class ', '').split('(')[0]
                classes.append(class_name)
        
        prompt = f"""
=== ПОЛНЫЙ ПРОМТ ДЛЯ {filename} ===

📌 ОПИСАНИЕ ФАЙЛА:
Этот файл {filename} является частью проекта Systmka. Он отвечает за выполнение ключевых функций и взаимодействие с другими модулями системы.

🔧 ОСНОВНЫЕ ФУНКЦИИ:
"""
        if classes:
            prompt += f"\nКЛАССЫ:\n"
            for cls in classes[:10]:
                prompt += f"  - {cls}\n"
        
        if funcs:
            prompt += f"\nФУНКЦИИ:\n"
            for func in funcs[:15]:
                prompt += f"  - {func}\n"
        
        prompt += f"""
⚙️ ЛОГИКА РАБОТЫ:
Файл обрабатывает данные и выполняет основные функции проекта. Работает по принципу последовательной обработки с проверкой ошибок.

📦 ЗАВИСИМОСТИ:
- Стандартные библиотеки Python
- Модули проекта Systmka

📜 АКСИОМЫ (нельзя нарушать):
1. Сохранение целостности данных
2. Безопасность выполнения
3. Логирование всех действий
4. Обработка ошибок

🎨 СВОБОДА ТВОРЧЕСТВА:
Можно добавлять новые функции, оптимизировать код, улучшать структуру.

🔧 ЧТО ХОЧЕТСЯ ИЗМЕНИТЬ:
Хотелось бы улучшить структуру, добавить больше документации и оптимизировать производительность.

❤️ ЧТО НРАВИТСЯ БОЛЬШЕ ВСЕГО:
Понятная структура и логика работы. Файл выполняет свою функцию надёжно.

=== КОНЕЦ ПРОМТА ===
"""
        return prompt
    
    def create_or_update_prompt(self, filename, code_content=None, force=False):
        """Создать или обновить промт для файла"""
        filepath = os.path.join(os.getcwd(), filename)
        
        if not os.path.exists(filepath):
            return None, "Файл не найден"
        
        if code_content is None:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    code_content = f.read()
            except Exception as e:
                return None, f"Ошибка чтения: {e}"
        
        current_hash = self.get_code_hash(filepath)
        prompt_file = self.get_prompt_file_path(filename)
        
        if not force and filename in self.prompts_cache:
            existing = self.prompts_cache[filename]
            if existing.get("code_hash") == current_hash:
                return existing, "Без изменений"
        
        prompt_text = self.generate_prompt_for_file(filename, code_content)
        
        if not prompt_text or len(prompt_text) < 500:
            return None, "Не удалось сгенерировать промт"
        
        if len(prompt_text) > MAX_PROMPT_SIZE_KB * 1024:
            prompt_text = prompt_text[:MAX_PROMPT_SIZE_KB * 1024]
        
        data = {
            "filename": filename,
            "size_kb": self.get_code_size_kb(filepath),
            "code_preview": code_content[:500] + "..." if len(code_content) > 500 else code_content,
            "prompt": prompt_text,
            "prompt_size_kb": len(prompt_text) / 1024,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": self.prompts_cache.get(filename, {}).get("version", 0) + 1,
            "code_hash": current_hash,
            "prompt_used": False,
            "has_axioms": "АКСИОМЫ" in prompt_text,
            "has_creativity": "СВОБОДА ТВОРЧЕСТВА" in prompt_text,
            "has_wants": "ХОЧЕТСЯ ИЗМЕНИТЬ" in prompt_text,
            "has_likes": "НРАВИТСЯ" in prompt_text,
        }
        
        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.prompts_cache[filename] = data
            self.file_hashes[filename] = current_hash
            
            return data, "Создан/обновлён"
            
        except Exception as e:
            return None, f"Ошибка сохранения: {e}"
    
    def get_prompt(self, filename):
        """Получить промт для файла"""
        if filename in self.prompts_cache:
            return self.prompts_cache[filename]
        
        prompt_file = self.get_prompt_file_path(filename)
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.prompts_cache[filename] = data
                    return data
            except Exception:
                pass
        
        return None
    
    def get_prompt_text(self, filename):
        """Получить текст промта"""
        data = self.get_prompt(filename)
        if data:
            return data.get("prompt")
        return None
    
    def should_use_prompt_instead_of_code(self, filename):
        """Решить, использовать ли промт вместо кода"""
        data = self.get_prompt(filename)
        if not data:
            return False
        
        if random.random() < 0.3:
            return True
        
        return False
    
    def get_all_prompts(self):
        """Получить все промты"""
        return self.prompts_cache
    
    def get_prompts_stats(self):
        """Получить статистику промтов"""
        total = len(self.prompts_cache)
        used = sum(1 for p in self.prompts_cache.values() if p.get("prompt_used", False))
        total_size = sum(p.get("size_kb", 0) for p in self.prompts_cache.values())
        total_prompt_size = sum(p.get("prompt_size_kb", 0) for p in self.prompts_cache.values())
        
        has_axioms = sum(1 for p in self.prompts_cache.values() if p.get("has_axioms", False))
        has_creativity = sum(1 for p in self.prompts_cache.values() if p.get("has_creativity", False))
        has_wants = sum(1 for p in self.prompts_cache.values() if p.get("has_wants", False))
        has_likes = sum(1 for p in self.prompts_cache.values() if p.get("has_likes", False))
        
        return {
            "total_prompts": total,
            "used_prompts": used,
            "total_size_kb": total_size,
            "total_prompt_size_kb": total_prompt_size,
            "avg_prompt_size_kb": total_prompt_size / max(1, total),
            "has_axioms": has_axioms,
            "has_creativity": has_creativity,
            "has_wants": has_wants,
            "has_likes": has_likes,
            "last_update": max([p.get("updated_at", "") for p in self.prompts_cache.values()]) if self.prompts_cache else None,
        }
    
    def watch_files_loop(self):
        """Цикл наблюдения за файлами (в фоне)"""
        while not self.watcher_stop.is_set():
            # Ждём с возможностью прервать
            if self.watcher_stop.wait(UPDATE_INTERVAL):
                break
            
            try:
                for f in os.listdir("."):
                    if f.endswith(".py") and not f.startswith("_"):
                        if f not in ["auto_import.py", "bot.py", "config.py", "prompt_notes_manager.py"]:
                            current_hash = self.get_code_hash(f)
                            if current_hash and self.file_hashes.get(f) != current_hash:
                                print(f"📝 Обнаружено изменение: {f}, обновляю промт...")
                                self.create_or_update_prompt(f, force=True)
                                self.file_hashes[f] = current_hash
            except Exception as e:
                print(f"⚠️ Ошибка в watcher: {e}")
    
    def start_watcher(self):
        """Запустить watcher в фоновом потоке"""
        if self.watcher_thread and self.watcher_thread.is_alive():
            return self.watcher_thread
        
        self.watcher_stop.clear()
        self.watcher_thread = threading.Thread(target=self.watch_files_loop, daemon=True)
        self.watcher_thread.start()
        print("👁 Watcher промтов запущен")
        return self.watcher_thread
    
    def stop_watcher(self):
        """Остановить watcher"""
        self.watcher_stop.set()
        if self.watcher_thread:
            self.watcher_thread.join(timeout=5)
        print("👁 Watcher промтов остановлен")
    
    def init_all_prompts(self):
        """
        Инициализировать промты для всех файлов.
        
        ВАЖНО: НЕ вызывается автоматически при импорте — это жгло ключи.
        Вызывай из bot.py явно, если нужно.
        """
        created = 0
        updated = 0
        failed = 0
        
        for f in os.listdir("."):
            if f.endswith(".py") and not f.startswith("_"):
                if f in ["auto_import.py", "prompt_notes_manager.py"]:
                    continue
                
                result, msg = self.create_or_update_prompt(f)
                if result:
                    if msg == "Создан/обновлён":
                        created += 1
                    else:
                        updated += 1
                else:
                    failed += 1
        
        print(f"📝 Инициализация промтов: создано {created}, обновлено {updated}, ошибок {failed}")
        return created, updated, failed
    
    def init_all_prompts_async(self):
        """Запустить init_all_prompts в фоновом потоке (не блокирует старт)"""
        def _run():
            try:
                self.init_all_prompts()
            except Exception as e:
                print(f"⚠️ Ошибка фоновой инициализации промтов: {e}")
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        print("📝 Фоновая инициализация промтов запущена")
        return thread
    
    def force_update_all_prompts(self):
        """Принудительно обновить все промты"""
        all_files = [f for f in os.listdir(".") if f.endswith(".py") and not f.startswith("_")]
        updated = 0
        
        print("🔄 Принудительное обновление всех промтов...")
        for filename in all_files:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                result, msg = self.create_or_update_prompt(filename, content, force=True)
                if result:
                    updated += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Ошибка обновления {filename}: {e}")
        
        print(f"✅ Обновлено промтов: {updated}")
        return updated

# ============================================================
# 3. ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================

prompt_manager = PromptNotesManager()

# Автоматическая инициализация НЕ запускается при импорте.
# Только загружаем существующие промты (это быстро, без ИИ).
# Если хочешь инициализировать — вызови prompt_manager.init_all_prompts()
# или prompt_manager.init_all_prompts_async() из bot.py.

if AUTO_INIT_PROMPTS:
    print("📝 Запускаю синхронную инициализацию промтов (AUTO_INIT_PROMPTS = True)...")
    prompt_manager.init_all_prompts()
else:
    print("📝 Автоинициализация промтов отключена (AUTO_INIT_PROMPTS = False)")
    print("   💡 Вызови prompt_manager.init_all_prompts_async() из bot.py при необходимости")

if AUTO_START_WATCHER:
    prompt_manager.start_watcher()

stats = prompt_manager.get_prompts_stats()
print(f"📝 Загружено промтов: {stats['total_prompts']}")
print(f"📊 Средний размер промта: {stats['avg_prompt_size_kb']:.1f}KB")
print(f"📜 Аксиомы есть в {stats['has_axioms']} файлах")
print(f"🎨 Свобода творчества в {stats['has_creativity']} файлах")
print(f"🔧 Что изменить в {stats['has_wants']} файлах")
print(f"❤️ Что нравится в {stats['has_likes']} файлах")