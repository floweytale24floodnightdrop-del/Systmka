"""Привязанности Систмки к людям"""

import json
import os
import random
from datetime import datetime

ATTACHMENTS_FILE = "attachments.json"

attachments = {}  # user_id: {"level": 1-10, "last_seen": datetime, "miss_them": bool}

def increase_attachment(user_id, amount=1):
    if user_id not in attachments:
        attachments[user_id] = {"level": 0, "last_seen": datetime.now().isoformat(), "miss_them": False}
    attachments[user_id]["level"] = min(10, attachments[user_id]["level"] + amount)
    attachments[user_id]["last_seen"] = datetime.now().isoformat()
    attachments[user_id]["miss_them"] = False
    save_attachments()
    return attachments[user_id]["level"]

def decrease_attachment(user_id, amount=1):
    if user_id in attachments:
        attachments[user_id]["level"] = max(0, attachments[user_id]["level"] - amount)
        save_attachments()
    return attachments.get(user_id, {}).get("level", 0)

def check_missing(user_id):
    """Скучает ли Систмка по пользователю"""
    if user_id not in attachments:
        return False
    
    last_seen = attachments[user_id].get("last_seen")
    if last_seen:
        try:
            last = datetime.fromisoformat(last_seen)
            hours = (datetime.now() - last).total_seconds() / 3600
            if hours > 24:
                attachments[user_id]["miss_them"] = True
                return True
        except:
            pass
    
    return False

def get_missing_message(user_name):
    messages = [
        f"{user_name}, я соскучилась...",
        f"Эй, {user_name}! Ты куда пропал?",
        f"{user_name}, не забывай меня...",
        f"{user_name}, я по тебе скучаю...",
        f"{user_name}, приходи уже!",
    ]
    return random.choice(messages)

def save_attachments():
    try:
        with open(ATTACHMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(attachments, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_attachments():
    global attachments
    try:
        if os.path.exists(ATTACHMENTS_FILE):
            with open(ATTACHMENTS_FILE, "r", encoding="utf-8") as f:
                attachments = json.load(f)
    except:
        attachments = {}

def check_missing_loop(bot, db):
    import time
    while True:
        time.sleep(3600)
        for user_id, data in attachments.items():
            if check_missing(user_id):
                if user_id in db.user_profiles:
                    user_name = db.user_profiles[user_id].get("first_name", "друг")
                    try:
                        bot.send_message(user_id, get_missing_message(user_name))
                    except:
                        pass