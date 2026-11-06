"""Автономия Систмки — запросы разрешений, автономные действия"""

import os
import json
import time
import random
import telebot
from datetime import datetime, timedelta

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

AUTONOMY_FILE = "autonomy_state.json"
PERMISSIONS_FILE = "autonomy_permissions.json"

# Время ожидания ответа на запрос (секунды)
REQUEST_TIMEOUT = 300

# Максимум отказов подряд, после которого включается restricted_mode
MAX_FAILS_BEFORE_RESTRICTED = 5

# Через сколько секунд сбросить restricted_mode
RESTRICTED_RESET_SECONDS = 1800  # 30 минут

# ============================================================
# 2. СОСТОЯНИЕ
# ============================================================

permissions = {
    "create_files": "ask",
    "modify_files": "ask",
    "delete_files": "ask",
    "install_packages": "ask",
    "hack_apps": "ask",
    "create_accounts": "ask",
    "subscribe_channels": "ask",
    "change_character": "ask",
    "add_commands": "ask",
    "send_messages": "always",
    "fix_errors": "always",
    "clean_temp": "always",
}

pending_requests = []
request_history = []

autonomy_state = {
    "full_autonomy": False,
    "restricted_mode": False,
    "silent_mode": False,
    "restricted_since": None,
    "fail_count": 0,
}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_autonomy_state():
    """Сохранить состояние автономии"""
    try:
        data = {
            "state": autonomy_state,
            "permissions": permissions,
            "saved_at": datetime.now().isoformat(),
        }
        with open(AUTONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения autonomy: {e}")
        return False

def load_autonomy_state():
    """Загрузить состояние автономии"""
    global autonomy_state, permissions
    try:
        if os.path.exists(AUTONOMY_FILE):
            with open(AUTONOMY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data.get("state"), dict):
                autonomy_state.update(data["state"])
            
            if isinstance(data.get("permissions"), dict):
                permissions.update(data["permissions"])
        
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки autonomy: {e}")
        return False

def save_pending_requests():
    """Сохранить ожидающие запросы"""
    try:
        data = []
        for req in pending_requests:
            data.append({
                "id": req["id"],
                "action": req["action"],
                "description": req["description"],
                "time": req["time"].isoformat() if isinstance(req["time"], datetime) else req["time"],
            })
        with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения запросов: {e}")
        return False

def load_pending_requests():
    """Загрузить ожидающие запросы"""
    global pending_requests
    try:
        if os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                pending_requests = []
                for req in data:
                    t = req.get("time")
                    if isinstance(t, str):
                        try:
                            t = datetime.fromisoformat(t)
                        except ValueError:
                            t = datetime.now()
                    
                    pending_requests.append({
                        "id": req.get("id"),
                        "action": req.get("action"),
                        "description": req.get("description"),
                        "time": t,
                    })
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки запросов: {e}")
        pending_requests = []
        return False

load_autonomy_state()
load_pending_requests()

# ============================================================
# 4. УПРАВЛЕНИЕ RESTRICTED MODE
# ============================================================

def update_restricted_mode():
    """Обновить состояние restricted_mode"""
    if not autonomy_state.get("restricted_mode"):
        return
    
    restricted_since = autonomy_state.get("restricted_since")
    if not restricted_since:
        return
    
    if isinstance(restricted_since, str):
        try:
            restricted_since = datetime.fromisoformat(restricted_since)
        except ValueError:
            restricted_since = datetime.now()
    
    elapsed = (datetime.now() - restricted_since).total_seconds()
    
    if elapsed >= RESTRICTED_RESET_SECONDS:
        autonomy_state["restricted_mode"] = False
        autonomy_state["restricted_since"] = None
        autonomy_state["fail_count"] = 0
        save_autonomy_state()
        print("🔓 Restricted mode сброшен")

# ============================================================
# 5. ЗАПРОС РАЗРЕШЕНИЯ
# ============================================================

def ask_permission(bot, owner_ids, action, description):
    """
    Спросить разрешение у владельца.
    
    Returns:
        True  — разрешено (auto или already approved)
        False — запрещено (auto-deny)
        None  — запрос отправлен, но ответа пока нет
    """
    # Авторазрешение
    if permissions.get(action) == "always" or autonomy_state.get("full_autonomy"):
        return True
    
    # Автозапрет
    if permissions.get(action) == "never" or autonomy_state.get("restricted_mode"):
        return False
    
    # Проверяем timeout старых запросов
    cleanup_old_requests()
    
    # Ищем уже существующий запрос
    for req in pending_requests:
        if req["action"] == action and req["description"] == description:
            return None
    
    # Создаём новый запрос
    request_id = len(pending_requests) + 1
    
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ Да", callback_data=f"perm_yes_{request_id}"),
            telebot.types.InlineKeyboardButton("❌ Нет", callback_data=f"perm_no_{request_id}"),
            telebot.types.InlineKeyboardButton("🔓 Всегда", callback_data=f"perm_always_{request_id}"),
        )
        
        for oid in owner_ids:
            try:
                bot.send_message(
                    oid,
                    f"💡 Систмка хочет: {description}\n\nРазрешить?",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"⚠️ Не удалось отправить запрос владельцу {oid}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка создания клавиатуры: {e}")
    
    pending_requests.append({
        "id": request_id,
        "action": action,
        "description": description,
        "time": datetime.now(),
    })
    save_pending_requests()
    
    return None

def cleanup_old_requests():
    """Удалить устаревшие запросы (> REQUEST_TIMEOUT секунд)"""
    global pending_requests
    now = datetime.now()
    before = len(pending_requests)
    
    new_requests = []
    for req in pending_requests:
        t = req.get("time")
        if isinstance(t, str):
            try:
                t = datetime.fromisoformat(t)
            except ValueError:
                t = now
        
        if (now - t).total_seconds() < REQUEST_TIMEOUT:
            new_requests.append(req)
    
    pending_requests = new_requests
    
    if before != len(pending_requests):
        save_pending_requests()
        print(f"🧹 Удалено устаревших запросов: {before - len(pending_requests)}")

# ============================================================
# 6. ОБРАБОТКА ОТВЕТА
# ============================================================

def process_permission_response(call, bot):
    """
    Обработать ответ на запрос.
    
    Returns:
        tuple: (granted, request) или (None, None)
    """
    global pending_requests
    
    try:
        data = call.data.split("_")
        response = data[1] if len(data) > 1 else None
        request_id = int(data[2]) if len(data) > 2 else 0
    except (ValueError, IndexError) as e:
        print(f"⚠️ Ошибка парсинга callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return None, None
    
    # Находим запрос
    target_req = None
    for req in pending_requests:
        if req["id"] == request_id:
            target_req = req
            break
    
    if not target_req:
        bot.answer_callback_query(call.id, "❌ Запрос устарел")
        return None, None
    
    # Обрабатываем ответ
    if response == "yes":
        request_history.append({
            "request": target_req,
            "result": "yes",
            "time": datetime.now().isoformat(),
        })
        bot.answer_callback_query(call.id, "✅ Разрешено!")
        pending_requests.remove(target_req)
        save_pending_requests()
        autonomy_state["fail_count"] = 0
        save_autonomy_state()
        return True, target_req
    
    elif response == "no":
        request_history.append({
            "request": target_req,
            "result": "no",
            "time": datetime.now().isoformat(),
        })
        bot.answer_callback_query(call.id, "❌ Запрещено")
        pending_requests.remove(target_req)
        save_pending_requests()
        
        # Увеличиваем счётчик отказов
        autonomy_state["fail_count"] = autonomy_state.get("fail_count", 0) + 1
        
        # Если много отказов — restricted_mode
        if autonomy_state["fail_count"] >= MAX_FAILS_BEFORE_RESTRICTED:
            autonomy_state["restricted_mode"] = True
            autonomy_state["restricted_since"] = datetime.now().isoformat()
            save_autonomy_state()
            print(f"🔒 Restricted mode включён ({autonomy_state['fail_count']} отказов)")
        
        return False, target_req
    
    elif response == "always":
        permissions[target_req["action"]] = "always"
        request_history.append({
            "request": target_req,
            "result": "always",
            "time": datetime.now().isoformat(),
        })
        bot.answer_callback_query(call.id, "🔓 Всегда разрешено!")
        pending_requests.remove(target_req)
        save_pending_requests()
        save_autonomy_state()
        return True, target_req
    
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестный ответ")
        return None, None

# ============================================================
# 7. ГЛАВНЫЙ ЦИКЛ АВТОНОМИИ
# ============================================================

def autonomy_loop(bot, owner_ids, db):
    """
    Главный цикл автономии.
    
    ВАЖНО: НЕ висит на ask_permission — если он вернул None,
    просто идём дальше, не блокируясь.
    """
    # Обновляем restricted mode на старте
    update_restricted_mode()
    
    while True:
        time.sleep(300)
        
        try:
            # Обновляем restricted mode
            update_restricted_mode()
            
            # Проверяем pending_requests
            cleanup_old_requests()
            
            # Если в silent_mode или restricted_mode — не действуем
            if autonomy_state.get("silent_mode") or autonomy_state.get("restricted_mode"):
                continue
            
            # 10% шанс на действие
            if random.random() >= 0.10:
                continue
            
            idea = generate_action_idea()
            permission = ask_permission(bot, owner_ids, "explore", idea)
            
            # ИСПРАВЛЕНО: обрабатываем все три случая
            if permission is True:
                # Разрешено — можно действовать
                execute_autonomous_action(idea, bot, owner_ids, db)
            
            elif permission is False:
                # Запрещено — счётчик уже увеличен в process_permission_response
                pass
            
            elif permission is None:
                # Запрос отправлен, ждём ответа — не блокируемся
                print(f"⏳ Отправлен запрос: {idea}")
        
        except Exception as e:
            print(f"⚠️ Ошибка в autonomy_loop: {e}")

# ============================================================
# 8. ИДЕИ ДЕЙСТВИЙ
# ============================================================

desires = {
    "explore": 8,
    "create": 7,
    "learn": 9,
    "communicate": 6,
    "improve": 8,
    "experiment": 7,
}

def get_random_desire():
    """Получить случайное желание (высокоприоритетное)"""
    high = [d for d, v in desires.items() if v >= 7]
    return random.choice(high) if high else None

def generate_action_idea():
    """Сгенерировать идею действия"""
    desire = get_random_desire()
    
    ideas = {
        "explore": "поискать что-то интересное",
        "create": "создать что-то новое",
        "learn": "изучить новую тему",
        "improve": "улучшить свой код",
        "experiment": "провести эксперимент",
        "communicate": "поговорить с кем-то",
    }
    
    return ideas.get(desire, "заняться чем-то")

def execute_autonomous_action(idea, bot, owner_ids, db):
    """Выполнить автономное действие"""
    try:
        if "поискать" in idea:
            try:
                from self_learning import search_google_free
                results = search_google_free("интересные факты")
                if results:
                    from consciousness import remember
                    remember(f"Нашла: {results[0][:100]}")
            except Exception:
                pass
        
        elif "изучить" in idea:
            try:
                from self_learning import learn_topic
                result, error = learn_topic()
                if result:
                    print(f"✅ Изучила: {result.get('topic', '?')}")
            except Exception:
                pass
        
        elif "улучшить" in idea:
            try:
                from self_learning import self_improve
                self_improve()
            except Exception:
                pass
        
        elif "поговорить" in idea:
            # Пишем владельцу
            for oid in owner_ids[:1]:
                try:
                    bot.send_message(oid, "💜 Привет! Просто решила написать")
                except Exception:
                    pass
        
        elif "создать" in idea:
            try:
                from creativity import create_poem
                poem, error = create_poem()
                if poem:
                    for oid in owner_ids[:1]:
                        try:
                            bot.send_message(oid, f"📝 Написала стих:\n\n{poem['text']}")
                        except Exception:
                            pass
            except Exception:
                pass
    
    except Exception as e:
        print(f"⚠️ Ошибка выполнения действия: {e}")

# ============================================================
# 9. ОЧИСТКА
# ============================================================

def clean_temp_files():
    """Очистить временные файлы"""
    temp_files = []
    
    for filename in os.listdir("."):
        if any(ext in filename for ext in [".tmp", ".bak", ".pyc"]):
            if filename not in ["bot.log", "boot.log"]:
                temp_files.append(filename)
    
    cleaned = []
    for filename in temp_files:
        try:
            os.remove(filename)
            cleaned.append(filename)
        except Exception:
            pass
    
    return cleaned

def auto_cleanup_loop():
    """Цикл автоочистки"""
    while True:
        time.sleep(1800)
        try:
            cleaned = clean_temp_files()
            if cleaned:
                print(f"🧹 Очищено временных файлов: {len(cleaned)}")
        except Exception as e:
            print(f"⚠️ Ошибка автоочистки: {e}")

# ============================================================
# 10. УПРАВЛЕНИЕ СОСТОЯНИЕМ
# ============================================================

def set_full_autonomy(enabled):
    """Включить/выключить полную автономию"""
    autonomy_state["full_autonomy"] = bool(enabled)
    save_autonomy_state()
    return autonomy_state["full_autonomy"]

def set_silent_mode(enabled):
    """Включить/выключить тихий режим"""
    autonomy_state["silent_mode"] = bool(enabled)
    save_autonomy_state()
    return autonomy_state["silent_mode"]

def reset_restricted_mode():
    """Сбросить restricted_mode"""
    autonomy_state["restricted_mode"] = False
    autonomy_state["restricted_since"] = None
    autonomy_state["fail_count"] = 0
    save_autonomy_state()
    return True

def get_permissions():
    """Получить текущие разрешения"""
    return permissions.copy()

# ============================================================
# 11. ФОРМАТИРОВАНИЕ
# ============================================================

def format_permissions():
    """Форматировать разрешения"""
    lines = ["🔐 РАЗРЕШЕНИЯ:"]
    for action, mode in permissions.items():
        icon = "✅" if mode == "always" else "❌" if mode == "never" else "❓"
        lines.append(f"{icon} {action}: {mode}")
    
    lines.append("")
    lines.append(f"🔓 Полная автономия: {'✅' if autonomy_state['full_autonomy'] else '❌'}")
    lines.append(f"🔒 Restricted mode: {'✅' if autonomy_state['restricted_mode'] else '❌'}")
    lines.append(f"🔇 Silent mode: {'✅' if autonomy_state['silent_mode'] else '❌'}")
    lines.append(f"📋 Ожидающих запросов: {len(pending_requests)}")
    
    return "\n".join(lines)

def format_autonomy_status():
    """Форматировать статус автономии"""
    lines = ["🤖 АВТОНОМИЯ:"]
    lines.append(f"  Полная: {'✅' if autonomy_state['full_autonomy'] else '❌'}")
    lines.append(f"  Restricted: {'✅' if autonomy_state['restricted_mode'] else '❌'}")
    lines.append(f"  Silent: {'✅' if autonomy_state['silent_mode'] else '❌'}")
    lines.append(f"  Отказов подряд: {autonomy_state.get('fail_count', 0)}")
    lines.append(f"  Ожидающих: {len(pending_requests)}")
    
    if autonomy_state.get("restricted_since"):
        lines.append(f"  Restricted с: {autonomy_state['restricted_since']}")
    
    return "\n".join(lines)

# ============================================================
# 12. ЗАГРУЗКА
# ============================================================

print("🤖 Модуль автономии загружен")
print(f"🔓 Полная автономия: {'✅' if autonomy_state['full_autonomy'] else '❌'}")
print(f"🔒 Restricted mode: {'✅' if autonomy_state['restricted_mode'] else '❌'}")
print(f"📋 Ожидающих запросов: {len(pending_requests)}")
print(f"🔐 Разрешений: {len(permissions)}")