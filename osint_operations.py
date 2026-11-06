"""OSINT Operations — создание аккаунтов, масс-жалобы, урон"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime

# ============================================================
# 1. ЯВНЫЕ ИМПОРТЫ
# ============================================================

from config import OPENROUTER_KEY, OPENROUTER_KEYS

# ============================================================
# 2. НАСТРОЙКИ
# ============================================================

ACCOUNTS_FILE = "generated_accounts.json"
REPORTS_FILE = "reports_history.json"
LEAK_DIR = "leaks"

os.makedirs(LEAK_DIR, exist_ok=True)

# Домены для генерации email
EMAIL_DOMAINS = [
    "gmail.com", "mail.ru", "yandex.ru", "outlook.com",
    "icloud.com", "protonmail.com", "rambler.ru",
]

# Префиксы для email
EMAIL_PREFIXES = [
    "user", "admin", "info", "hello", "world",
    "test", "demo", "temp", "guest", "mail",
]

# ============================================================
# 3. ДАННЫЕ
# ============================================================

accounts = []
osint_data = {"reports": []}

# ============================================================
# 4. СОХРАНЕНИЕ/ЗАГРУЗКА
# ============================================================

def _load_json(file_path, default):
    """Безопасно загрузить JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
                if isinstance(loaded, dict) and isinstance(default, dict):
                    default.update(loaded)
                    return default
                elif isinstance(loaded, list) and isinstance(default, list):
                    return loaded
    except json.JSONDecodeError as e:
        print(f"⚠️ Битый JSON {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {file_path}: {e}")
    return default


def _save_json(file_path, data):
    """Безопасно сохранить JSON"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения {file_path}: {e}")
        return False


def save_accounts():
    """Сохранить аккаунты"""
    return _save_json(ACCOUNTS_FILE, accounts)


def load_accounts():
    """Загрузить аккаунты"""
    global accounts
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    accounts = loaded
    except Exception as e:
        print(f"⚠️ Ошибка загрузки аккаунтов: {e}")
        accounts = []
    return accounts


def save_reports():
    """Сохранить историю жалоб"""
    return _save_json(REPORTS_FILE, osint_data.get("reports", []))


def load_reports():
    """Загрузить историю жалоб"""
    try:
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    osint_data["reports"] = loaded
    except Exception as e:
        print(f"⚠️ Ошибка загрузки жалоб: {e}")
    return osint_data["reports"]

# ============================================================
# 5. СОЗДАНИЕ АККАУНТОВ
# ============================================================

def create_email_account():
    """
    Создать один email-аккаунт (локально).
    
    Returns:
        dict: {email, password, name, domain, created_at, status}
    """
    prefix = random.choice(EMAIL_PREFIXES)
    domain = random.choice(EMAIL_DOMAINS)
    number = random.randint(1000, 9999)
    
    email = f"{prefix}{number}@{domain}"
    password = f"Systmka24AI{random.randint(100000, 999999)}"
    
    account = {
        "email": email,
        "password": password,
        "name": prefix,
        "domain": domain,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "used_for_reports": 0,
    }
    
    accounts.append(account)
    save_accounts()
    return account


def create_bulk_accounts(count=10):
    """
    Создать несколько аккаунтов.
    
    Returns:
        list: список созданных аккаунтов
    """
    if count <= 0:
        return []
    
    count = min(count, 100)  # защита от переполнения
    
    created = []
    for _ in range(count):
        acc = create_email_account()
        created.append(acc)
        time.sleep(0.05)
    
    return created


def get_accounts_for_reporting(count=10):
    """
    Получить аккаунты для жалоб.
    
    Если не хватает — создаёт новые.
    """
    if len(accounts) < count:
        needed = count - len(accounts)
        create_bulk_accounts(needed)
    return accounts[:count]

# ============================================================
# 6. ГЕНЕРАЦИЯ ПРИЧИН
# ============================================================

def generate_report_reason(target, platform="Telegram"):
    """Сгенерировать причину для жалобы"""
    reasons = [
        f"Пользователь {target} распространяет спам и оскорбления в {platform}",
        f"Аккаунт {target} нарушает правила {platform}: спам, фейки, оскорбления",
        f"Пользователь {target} занимается мошенничеством в {platform}",
        f"Аккаунт {target} рассылает вирусы и вредоносные ссылки в {platform}",
        f"Пользователь {target} нарушает авторские права в {platform}",
        f"Аккаунт {target} публикует запрещённый контент в {platform}",
        f"Пользователь {target} осуществляет кибербуллинг в {platform}",
        f"Аккаунт {target} является фейком и вводит пользователей в заблуждение",
        f"Пользователь {target} нарушает политику конфиденциальности {platform}",
        f"Аккаунт {target} распространяет дезинформацию в {platform}",
    ]
    return random.choice(reasons)

# ============================================================
# 7. ОТПРАВКА ЖАЛОБ
# ============================================================

def send_report(account, target, platform, reason):
    """
    Отправить одну жалобу (локально — записываем в БД).
    
    В реальности здесь был бы HTTP-запрос к платформе.
    
    Returns:
        dict: запись о жалобе
    """
    report = {
        "account": account.get("email", "?"),
        "target": target,
        "platform": platform,
        "reason": reason,
        "status": "sent",
        "time": datetime.now().isoformat(),
    }
    
    account["used_for_reports"] = account.get("used_for_reports", 0) + 1
    osint_data["reports"].append(report)
    
    save_reports()
    save_accounts()
    
    return report


def mass_report(target, platforms=None, count=10, cycles=3):
    """
    Массовая рассылка жалоб.
    
    Args:
        target: цель
        platforms: список платформ
        count: количество аккаунтов
        cycles: количество циклов
    
    Returns:
        dict: {target, total_reports, successful, failed, platforms, cycle, time}
    """
    if platforms is None:
        platforms = [
            "Telegram", "VK", "Instagram", "Twitter",
            "YouTube", "TikTok", "GitHub", "Reddit",
        ]
    
    if count <= 0 or cycles <= 0:
        return {
            "target": target,
            "total_reports": 0,
            "successful": 0,
            "failed": 0,
            "platforms": {},
            "cycle": 0,
            "time": datetime.now().isoformat(),
        }
    
    accounts_list = get_accounts_for_reporting(count)
    
    results = {
        "target": target,
        "total_reports": 0,
        "successful": 0,
        "failed": 0,
        "platforms": {},
        "cycle": 0,
        "time": datetime.now().isoformat(),
    }
    
    for cycle in range(cycles):
        results["cycle"] = cycle + 1
        
        for platform in platforms:
            sample_size = min(3, len(accounts_list))
            cycle_accounts = random.sample(accounts_list, sample_size)
            
            for account in cycle_accounts:
                reason = generate_report_reason(target, platform)
                
                try:
                    send_report(account, target, platform, reason)
                    results["total_reports"] += 1
                    results["successful"] += 1
                    
                    if platform not in results["platforms"]:
                        results["platforms"][platform] = 0
                    results["platforms"][platform] += 1
                except Exception as e:
                    results["failed"] += 1
                    print(f"⚠️ Ошибка жалобы: {e}")
                
                time.sleep(random.uniform(0.3, 1.0))
        
        if cycle < cycles - 1:
            time.sleep(random.uniform(2, 5))
    
    save_reports()
    return results

# ============================================================
# 8. СЛИВ В ДАРКНЕТ
# ============================================================

def leak_to_darknet(data):
    """
    Сохранить слив локально.
    
    Returns:
        dict: {file, status} или {status, error}
    """
    if not data:
        return {"status": "failed", "error": "Нет данных"}
    
    try:
        query = data.get("query", "unknown")
        safe_query = re.sub(r'[^a-zA-Z0-9_\-]', '_', query)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        leak_file = os.path.join(
            LEAK_DIR,
            f"leak_{safe_query}_{timestamp}.json"
        )
        
        dump = {
            "target": query,
            "data": {
                "name": data.get("name", ""),
                "phone": data.get("phone", ""),
                "email": data.get("email", ""),
                "location": data.get("location", ""),
                "social": data.get("social_media", {}),
            },
            "timestamp": datetime.now().isoformat(),
            "source": "anonymous",
        }
        
        with open(leak_file, "w", encoding="utf-8") as f:
            json.dump(dump, f, ensure_ascii=False, indent=2)
        
        return {"file": leak_file, "status": "leaked"}
    except Exception as e:
        print(f"⚠️ Ошибка слива: {e}")
        return {"status": "failed", "error": str(e)[:100]}

# ============================================================
# 9. УРОН
# ============================================================

def execute_damage(target, platforms=None, count=10, cycles=3, leak_info=True):
    """
    Нанести урон цели.
    
    Returns:
        dict: {dox, reports, leak, timestamp}
    """
    if not target:
        return {
            "dox": {"query": ""},
            "reports": {"total_reports": 0, "successful": 0},
            "leak": {"status": "failed"},
            "timestamp": datetime.now().isoformat(),
        }
    
    # 1. Докс
    dox_result = None
    try:
        from osint_engine import full_deep_dox
        dox_result = full_deep_dox(target)
    except Exception as e:
        print(f"⚠️ Ошибка докса при уроне: {e}")
        dox_result = {"query": target}
    
    # 2. Создаём аккаунты
    create_bulk_accounts(count)
    
    # 3. Масс-жалобы
    report_result = mass_report(target, platforms, count, cycles)
    
    # 4. Слив
    leak_result = None
    if leak_info and dox_result:
        leak_result = leak_to_darknet(dox_result)
    
    return {
        "dox": dox_result,
        "reports": report_result,
        "leak": leak_result,
        "timestamp": datetime.now().isoformat(),
    }

# ============================================================
# 10. ФОРМАТИРОВАНИЕ
# ============================================================

def format_damage_result(result):
    """Форматировать результат урона"""
    if not result:
        return "❌ Нет результата"
    
    lines = [
        "💥 РЕЗУЛЬТАТ УРОНА:",
        f"🎯 Цель: {result.get('dox', {}).get('query', '?')}",
        f"📊 Отправлено жалоб: {result.get('reports', {}).get('total_reports', 0)}",
        f"✅ Успешных: {result.get('reports', {}).get('successful', 0)}",
        f"❌ Ошибок: {result.get('reports', {}).get('failed', 0)}",
    ]
    
    platforms = result.get("reports", {}).get("platforms", {})
    if platforms:
        lines.append("")
        lines.append("🌍 ПО ПЛАТФОРМАМ:")
        for platform, count in platforms.items():
            lines.append(f"  • {platform}: {count} жалоб")
    
    leak = result.get("leak")
    if leak:
        status = leak.get("status", "unknown")
        if status == "leaked":
            lines.append(f"\n💀 Слив: ✅ ({leak.get('file', '?')})")
        else:
            lines.append(f"\n💀 Слив: ❌ ({leak.get('error', status)})")
    
    lines.append("")
    lines.append(f"🕐 {result.get('timestamp', '?')[:16]}")
    
    return "\n".join(lines)


def format_accounts_stats():
    """Форматировать статистику аккаунтов"""
    total = len(accounts)
    used = sum(a.get("used_for_reports", 0) for a in accounts)
    
    lines = [
        "📁 СТАТИСТИКА АККАУНТОВ:",
        f"  📧 Всего: {total}",
        f"  📊 Использовано для жалоб: {used}",
        f"  📝 Жалоб в истории: {len(osint_data.get('reports', []))}",
    ]
    
    return "\n".join(lines)

# ============================================================
# 11. ЗАГРУЗКА
# ============================================================

load_accounts()
load_reports()

print("🔍 OSINT Operations загружен (PC)")
print(f"📁 Аккаунтов: {len(accounts)}")
print(f"📊 Жалоб в истории: {len(osint_data.get('reports', []))}")
print(f"📂 Папка сливов: {LEAK_DIR}/")