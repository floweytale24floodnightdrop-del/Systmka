"""
app.py — Flask + бот + автосообщение + пингер для Render.
"""

import os
import threading
import time
from flask import Flask

from bot import bot, OWNER_IDS
from keep_alive import start_pinger


# ============================================================
# 1. FLASK
# ============================================================

app = Flask(__name__)


@app.route("/")
def index():
    return "Systmka is running", 200


@app.route("/health")
def health():
    """Health-check для Render и пингера."""
    return "OK", 200


# ============================================================
# 2. АВТОСООБЩЕНИЕ (КАЖДЫЕ 5 МИНУТ)
# ============================================================

AUTO_MESSAGE = "💟Автоматическое сообщение, не обращайте внимания💟"
AUTO_INTERVAL = 300


def auto_message_loop():
    """Отправлять автосообщение каждые 5 минут."""
    time.sleep(60)
    
    while True:
        try:
            for oid in OWNER_IDS:
                try:
                    bot.send_message(oid, AUTO_MESSAGE)
                    print(f"💟 Автосообщение → {oid}")
                except Exception as e:
                    print(f"⚠️ Не смогла отправить {oid}: {e}")
        except Exception as e:
            print(f"⚠️ Ошибка автосообщения: {e}")
        
        time.sleep(AUTO_INTERVAL)


# ============================================================
# 3. ЗАПУСК БОТА
# ============================================================

def start_bot():
    """Запустить бота в потоке."""
    print("🤖 Запуск бота...")
    bot.polling(none_stop=True, interval=3, timeout=60)


# ============================================================
# 4. ГЛАВНЫЙ ЗАПУСК
# ============================================================

if __name__ == "__main__":
    # Автосообщение
    threading.Thread(target=auto_message_loop, daemon=True).start()
    
    # Бот
    threading.Thread(target=start_bot, daemon=True).start()
    
    # Пингер
    start_pinger()
    
    # Flask
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Flask запускается на порту {port}")
    app.run(host="0.0.0.0", port=port, threaded=True)