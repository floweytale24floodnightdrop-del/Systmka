"""РП команды — полная версия"""

import json
import os
import random
import re
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

RP_COMMANDS_FILE = "rp_commands_data.json"
RP_REQUESTS_FILE = "rp_requests_data.json"

# ============================================================
# 2. ДАННЫЕ
# ============================================================

custom_rp_commands = {}
rp_requests = {}

# ============================================================
# 3. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def save_rp_commands():
    try:
        with open(RP_COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_rp_commands, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_rp_commands():
    global custom_rp_commands
    try:
        if os.path.exists(RP_COMMANDS_FILE):
            with open(RP_COMMANDS_FILE, "r", encoding="utf-8") as f:
                custom_rp_commands = json.load(f)
        return True
    except:
        custom_rp_commands = {}
        return False

def save_rp_requests():
    try:
        data = {}
        for req_id, req in rp_requests.items():
            data[str(req_id)] = {
                "from_user": req["from_user"],
                "to_user": req["to_user"],
                "action": req["action"],
                "action_text": req.get("action_text", ""),
                "status": req["status"],
                "anonymous": req.get("anonymous", False),
                "created_at": req["created_at"].isoformat() if isinstance(req.get("created_at"), datetime) else req.get("created_at"),
                "chat_id": req.get("chat_id"),
                "message_id": req.get("message_id"),
            }
        with open(RP_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_rp_requests():
    global rp_requests
    try:
        if os.path.exists(RP_REQUESTS_FILE):
            with open(RP_REQUESTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for req_id, req in data.items():
                    rp_requests[req_id] = {
                        "from_user": req["from_user"],
                        "to_user": req["to_user"],
                        "action": req["action"],
                        "action_text": req.get("action_text", ""),
                        "status": req["status"],
                        "anonymous": req.get("anonymous", False),
                        "created_at": datetime.fromisoformat(req["created_at"]) if isinstance(req.get("created_at"), str) else datetime.now(),
                        "chat_id": req.get("chat_id"),
                        "message_id": req.get("message_id"),
                    }
        return True
    except:
        rp_requests = {}
        return False

load_rp_commands()
load_rp_requests()

# ============================================================
# 4. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def get_all_rp_commands():
    """Получить все РП команды (стандартные + кастомные)"""
    default_commands = {
        "кусь": "<Ты> кусьнул(а) <Пользователь>",
        "чмок": "<Ты> чмокнул(а) <Пользователь>",
        "обнять": "<Ты> обнял(а) <Пользователь>",
        "поцеловать": "<Ты> поцеловал(а) <Пользователь>",
        "ударить": "<Ты> ударил(а) <Пользователь>",
        "погладить": "<Ты> погладил(а) <Пользователь>",
        "укусить": "<Ты> укусил(а) <Пользователь>",
        "засосать": "<Ты> засосал(а) <Пользователь>",
        "выебать": "<Ты> выебал(а) <Пользователь>",
        "трахнуть": "<Ты> трахнул(а) <Пользователь>",
        "отшлепать": "<Ты> отшлепал(а) <Пользователь>",
        "прижать": "<Ты> прижал(а) <Пользователь> к стене",
        "лизнуть": "<Ты> лизнул(а) <Пользователь>",
        "убить": "<Ты> убил(а) <Пользователь>",
        "воскресить": "<Ты> воскресил(а) <Пользователь>",
        "вылечить": "<Ты> вылечил(а) <Пользователь>",
        "обнять крепко": "<Ты> крепко обнял(а) <Пользователь>",
        "поцеловать в шею": "<Ты> поцеловал(а) <Пользователь> в шею",
        "поцеловать в губы": "<Ты> поцеловал(а) <Пользователь> в губы",
        "взять за руку": "<Ты> взял(а) <Пользователь> за руку",
        "прижать к себе": "<Ты> прижал(а) <Пользователь> к себе",
        "повалить": "<Ты> повалил(а) <Пользователь>",
        "защекотать": "<Ты> защекотал(а) <Пользователь>",
    }
    all_commands = default_commands.copy()
    for trigger, data in custom_rp_commands.items():
        all_commands[trigger] = data.get("action", "")
    return all_commands

def get_rp_command(trigger, user_id=None):
    """Получить РП команду по триггеру (для пользователя)"""
    all_commands = get_all_rp_commands()
    trigger_lower = trigger.lower()
    
    # Проверяем кастомные команды
    if trigger_lower in custom_rp_commands:
        if user_id is None or custom_rp_commands[trigger_lower].get("creator_id") == user_id:
            return custom_rp_commands[trigger_lower]["action"]
    
    # Проверяем стандартные команды
    if trigger_lower in all_commands:
        return all_commands[trigger_lower]
    
    return None

def add_custom_rp_command(trigger, action, creator_id, creator_name):
    trigger_lower = trigger.lower()
    custom_rp_commands[trigger_lower] = {
        "action": action,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "created_at": datetime.now().isoformat(),
    }
    save_rp_commands()
    return True

def remove_custom_rp_command(trigger, user_id):
    trigger_lower = trigger.lower()
    if trigger_lower in custom_rp_commands:
        if custom_rp_commands[trigger_lower]["creator_id"] == user_id:
            del custom_rp_commands[trigger_lower]
            save_rp_commands()
            return True
    return False

def get_user_rp_commands(user_id):
    user_commands = {}
    for trigger, data in custom_rp_commands.items():
        if data["creator_id"] == user_id:
            user_commands[trigger] = data["action"]
    return user_commands

# ============================================================
# 5. ЗАПРОСЫ В ЛС
# ============================================================

def create_rp_request(from_user_id, to_user_id, action, action_text, anonymous=False, chat_id=None):
    request_id = str(len(rp_requests) + 1)
    
    for req_id, req in rp_requests.items():
        if req["from_user"] == from_user_id and req["to_user"] == to_user_id and req["status"] == "pending":
            return None, "У вас уже есть активный запрос"
    
    rp_requests[request_id] = {
        "from_user": from_user_id,
        "to_user": to_user_id,
        "action": action,
        "action_text": action_text,
        "status": "pending",
        "anonymous": anonymous,
        "created_at": datetime.now(),
        "chat_id": chat_id,
        "message_id": None,
    }
    save_rp_requests()
    return request_id, None

def accept_rp_request(request_id, user_id):
    req_id = str(request_id)
    if req_id not in rp_requests:
        return False, "Запрос не найден"
    
    req = rp_requests[req_id]
    if req["to_user"] != user_id:
        return False, "Вы не получатель"
    
    if req["status"] != "pending":
        return False, f"Запрос уже {req['status']}"
    
    req["status"] = "accepted"
    save_rp_requests()
    return True, None

def decline_rp_request(request_id, user_id):
    req_id = str(request_id)
    if req_id not in rp_requests:
        return False, "Запрос не найден"
    
    req = rp_requests[req_id]
    if req["to_user"] != user_id:
        return False, "Вы не получатель"
    
    if req["status"] != "pending":
        return False, f"Запрос уже {req['status']}"
    
    req["status"] = "declined"
    save_rp_requests()
    return True, None

def get_pending_requests(user_id):
    pending = []
    for req_id, req in rp_requests.items():
        if req["to_user"] == user_id and req["status"] == "pending":
            pending.append({
                "id": req_id,
                "from_user": req["from_user"],
                "action": req["action"],
                "action_text": req.get("action_text", ""),
                "anonymous": req.get("anonymous", False),
                "created_at": req["created_at"],
            })
    return pending

# ============================================================
# 6. ОБРАБОТКА РП КОМАНДЫ В ЛС
# ============================================================

def handle_rp_command_with_request(bot, message, trigger, target_user, action_text, anonymous=False):
    from_user = message.from_user
    
    if not target_user:
        return False, "❌ Укажи пользователя: @юз или ответь на сообщение"
    
    if target_user.id == from_user.id:
        return False, "❌ Нельзя использовать РП-команду на себя"
    
    if message.chat.type != "private":
        return False, "❌ Эта команда работает только в ЛС с Систмкой"
    
    request_id, error = create_rp_request(
        from_user.id, 
        target_user.id, 
        trigger, 
        action_text,
        anonymous,
        message.chat.id
    )
    
    if error:
        return False, f"❌ {error}"
    
    try:
        import telebot
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ Принять", callback_data=f"rp_accept_{request_id}"),
            telebot.types.InlineKeyboardButton("❌ Отклонить", callback_data=f"rp_decline_{request_id}")
        )
        
        if anonymous:
            request_text = f"👤 Кто-то хочет тайно {trigger} тебя!\n\nДействие: {action_text}"
        else:
            request_text = f"👋 | {from_user.first_name} хочет {trigger} тебя!\n\nДействие: {action_text}"
        
        sent_msg = bot.send_message(
            target_user.id,
            request_text,
            reply_markup=keyboard
        )
        
        rp_requests[request_id]["message_id"] = sent_msg.message_id
        save_rp_requests()
        
        return True, f"✅ Запрос отправлен {target_user.first_name} в ЛС!"
        
    except Exception as e:
        return False, f"❌ Не удалось отправить запрос: {e}"

# ============================================================
# 7. ОБРАБОТКА ОТВЕТА НА ЗАПРОС
# ============================================================

def process_rp_response(bot, call, request_id, accept=True):
    import telebot
    user_id = call.from_user.id
    req = rp_requests.get(str(request_id))
    
    if not req:
        bot.answer_callback_query(call.id, "❌ Запрос не найден")
        return
    
    if req["to_user"] != user_id:
        bot.answer_callback_query(call.id, "❌ Вы не получатель")
        return
    
    if req["status"] != "pending":
        bot.answer_callback_query(call.id, f"❌ Запрос уже {req['status']}")
        return
    
    if accept:
        success, error = accept_rp_request(request_id, user_id)
        if success:
            try:
                from_user = bot.get_chat(req["from_user"])
                action_text = req.get("action_text", req["action"])
                
                if req.get("anonymous", False):
                    result_text = f"👤 Кто-то тайно {action_text} тебя!"
                    notify_text = f"✅ Твой тайный запрос принят!\n\n{action_text}"
                else:
                    result_text = f"{from_user.first_name} {action_text} тебя!"
                    notify_text = f"✅ {user_id} принял(а) твой запрос!\n\n{action_text}"
                
                bot.send_message(user_id, result_text)
                try:
                    bot.send_message(req["from_user"], notify_text)
                except:
                    pass
                
                bot.edit_message_text(
                    f"✅ Запрос принят!\n\n{result_text}",
                    call.message.chat.id,
                    call.message.message_id
                )
                bot.answer_callback_query(call.id, "✅ Принято!")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        else:
            bot.answer_callback_query(call.id, f"❌ {error}")
    else:
        success, error = decline_rp_request(request_id, user_id)
        if success:
            try:
                bot.send_message(req["from_user"], f"❌ Пользователь отклонил твой запрос")
            except:
                pass
            
            bot.edit_message_text(
                "❌ Запрос отклонён",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id, "❌ Отклонено")
        else:
            bot.answer_callback_query(call.id, f"❌ {error}")

# ============================================================
# 8. ЗАГРУЗКА
# ============================================================

print(f"🎭 Загружено РП команд: {len(custom_rp_commands)}")
print(f"📋 Ожидающих запросов: {len([r for r in rp_requests.values() if r['status'] == 'pending'])}")