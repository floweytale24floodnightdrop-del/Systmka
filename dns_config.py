"""DNS через DoH (динамический поиск через ИИ + перебор) — обход блокировки DNS в РФ"""

import socket
import requests
import dns.message
import dns.query
import threading
import time
import json
import re

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DOH_TIMEOUT = 3
DNS_CACHE_TTL = 3600
AI_CACHE_TTL = 86400  # 24 часа — ИИ-список кэшируется

# Файл кэша ИИ-списка
AI_DOH_CACHE_FILE = "doh_servers_cache.json"

# ============================================================
# 2. ВСТРОЕННЫЙ СПИСОК (FALLBACK)
# ============================================================

BUILTIN_DOH_SERVERS = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/dns-query",
    "https://dns.quad9.net/dns-query",
    "https://dns.adguard-dns.com/dns-query",
    "https://dns.nextdns.io/dns-query",
    "https://doh.opendns.com/dns-query",
    "https://dns.mullvad.net/dns-query",
    "https://doh.libredns.gr/dns-query",
    "https://dns.snopyta.org/dns-query",
    "https://dns.njal.la/dns-query",
    "https://anycast.uncensoreddns.org/dns-query",
    "https://dns.digitale-gesellschaft.ch/dns-query",
    "https://doh.dns.sb/dns-query",
    "https://doh.applied-privacy.net/query",
    "https://doh.cz.nic.cz/dns-query",
    "https://dnswarden.com/dns-query",
    "https://doh-blahdns.de/dns-query",
    "https://doh.tiar.app/dns-query",
    # РФ (могут работать)
    "https://dns.yandex.ru/dns-query",
    "https://dns.mail.ru/dns-query",
    "https://dns.rt.ru/dns-query",
    "https://dns.mts.ru/dns-query",
    "https://dns.beeline.ru/dns-query",
    "https://dns.megafon.ru/dns-query",
]

# ============================================================
# 3. КЭШ
# ============================================================

_dns_cache = {}
_dns_cache_lock = threading.Lock()

_working_doh = None
_working_doh_lock = threading.Lock()

_ai_doh_list = None
_ai_doh_lock = threading.Lock()

# ============================================================
# 4. ПОИСК DOH ЧЕРЕЗ ИИ
# ============================================================

def _get_openrouter_key():
    """Получить ключ OpenRouter"""
    try:
        from config import OPENROUTER_KEY, OPENROUTER_KEYS
        if OPENROUTER_KEYS:
            return OPENROUTER_KEYS[0]
        return OPENROUTER_KEY
    except ImportError:
        return None

def _load_ai_cache():
    """Загрузить ИИ-кэш из файла"""
    global _ai_doh_list
    
    try:
        import os
        if os.path.exists(AI_DOH_CACHE_FILE):
            with open(AI_DOH_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Проверяем TTL
            cached_at = data.get("cached_at", 0)
            if time.time() - cached_at < AI_CACHE_TTL:
                _ai_doh_list = data.get("servers", [])
                print(f"📦 ИИ-кэш DoH: {len(_ai_doh_list)} серверов (из файла)")
                return _ai_doh_list
    except Exception:
        pass
    
    return None

def _save_ai_cache(servers):
    """Сохранить ИИ-кэш в файл"""
    try:
        with open(AI_DOH_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "servers": servers,
                "cached_at": time.time(),
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения ИИ-кэша: {e}")
        return False

def _find_doh_via_ai():
    """
    Найти DoH-серверы через ИИ (OpenRouter).
    
    Returns:
        list: список URL
    """
    global _ai_doh_list
    
    with _ai_doh_lock:
        # Кэш в памяти
        if _ai_doh_list:
            return _ai_doh_list
        
        # Кэш в файле
        cached = _load_ai_cache()
        if cached:
            _ai_doh_list = cached
            return _ai_doh_list
        
        # Запрос к ИИ
        key = _get_openrouter_key()
        if not key:
            print("⚠️ Нет ключа OpenRouter — использую встроенный список")
            _ai_doh_list = BUILTIN_DOH_SERVERS.copy()
            return _ai_doh_list
        
        print("🤖 Спрашиваю ИИ о рабочих DoH-серверах...")
        
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
                                "Ты эксперт по сетям. Дай список РАБОЧИХ "
                                "DoH-серверов (DNS over HTTPS), которые "
                                "доступны в РОССИИ в 2026 году.\n\n"
                                "Формат ответа — ТОЛЬКО JSON-массив URL:\n"
                                '["https://...", "https://...", ...]\n\n'
                                "Требования:\n"
                                "1. Только РАБОЧИЕ серверы (не заблокированные в РФ)\n"
                                "2. Популярные (Cloudflare, Google, Quad9, AdGuard, и т.д.)\n"
                                "3. Российские (Yandex, Mail.ru, МТС, и т.д.)\n"
                                "4. Минимум 20 серверов\n"
                                "5. Только URL, без пояснений"
                            ),
                        },
                        {
                            "role": "user",
                            "content": "Дай список рабочих DoH-серверов для РФ (2026):",
                        },
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    content = data['choices'][0]['message']['content']
                    
                    # Парсим JSON
                    content = content.strip()
                    if content.startswith("```"):
                        lines = content.split("\n")
                        content = "\n".join(lines[1:])
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Ищем JSON-массив
                    first = content.find("[")
                    last = content.rfind("]")
                    if first != -1 and last != -1:
                        content = content[first:last + 1]
                    
                    servers = json.loads(content)
                    
                    if isinstance(servers, list) and servers:
                        # Валидируем
                        valid = [
                            s for s in servers
                            if isinstance(s, str)
                            and s.startswith("https://")
                            and "dns-query" in s or "query" in s or "/dns" in s
                        ]
                        
                        if valid:
                            print(f"✅ ИИ вернул {len(valid)} DoH-серверов")
                            _ai_doh_list = valid
                            _save_ai_cache(valid)
                            return _ai_doh_list
        except Exception as e:
            print(f"⚠️ Ошибка ИИ-запроса: {e}")
        
        # Fallback
        print("⚠️ ИИ не ответил — использую встроенный список")
        _ai_doh_list = BUILTIN_DOH_SERVERS.copy()
        return _ai_doh_list

# ============================================================
# 5. РЕЗОЛВ ЧЕРЕЗ ОДИН DOH
# ============================================================

def _resolve_via_single_doh(domain, doh_url):
    """Резолвить через ОДИН DoH-сервер"""
    try:
        query = dns.message.make_query(domain, "A")
        query_data = query.to_wire()
        
        response = requests.post(
            doh_url,
            data=query_data,
            headers={
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
            },
            timeout=DOH_TIMEOUT,
            verify=False,
        )
        
        if response.status_code == 200:
            dns_response = dns.message.from_wire(response.content)
            for answer in dns_response.answer:
                for item in answer:
                    if item.rdtype == 1:
                        return str(item)
    except Exception:
        pass
    
    return None

# ============================================================
# 6. ПОИСК РАБОЧЕГО DOH
# ============================================================

def _find_working_doh():
    """Найти рабочий DoH-сервер"""
    global _working_doh
    
    with _working_doh_lock:
        if _working_doh:
            return _working_doh
        
        # Список от ИИ
        ai_servers = _find_doh_via_ai()
        
        # Объединяем: ИИ + встроенный
        all_servers = list(dict.fromkeys(ai_servers + BUILTIN_DOH_SERVERS))
        
        print(f"🔍 Ищу рабочий DoH (кандидатов: {len(all_servers)})...")
        
        test_domain = "www.google.com"
        
        for i, doh_url in enumerate(all_servers, 1):
            ip = _resolve_via_single_doh(test_domain, doh_url)
            
            if ip:
                print(f"✅ Рабочий DoH: {doh_url} ({i}/{len(all_servers)})")
                _working_doh = doh_url
                return _working_doh
            
            if i % 10 == 0:
                print(f"   ⏳ Проверено: {i}/{len(all_servers)}")
        
        print(f"❌ Не найден рабочий DoH")
        return None

# ============================================================
# 7. РЕЗОЛВ ЧЕРЕЗ DOH
# ============================================================

def resolve_via_doh(domain):
    """Резолвить домен через DoH"""
    if not domain:
        return None
    
    # Кэш
    with _dns_cache_lock:
        if domain in _dns_cache:
            cached = _dns_cache[domain]
            if time.time() - cached["time"] < DNS_CACHE_TTL:
                return cached["ip"]
    
    # Рабочий DoH
    doh_url = _find_working_doh()
    
    if doh_url:
        ip = _resolve_via_single_doh(domain, doh_url)
        if ip:
            with _dns_cache_lock:
                _dns_cache[domain] = {"ip": ip, "time": time.time()}
            return ip
    
    return None

# ============================================================
# 8. MONKEY-PATCH socket.getaddrinfo
# ============================================================

_original_getaddrinfo = socket.getaddrinfo


def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Патченный getaddrinfo — сначала DoH, потом обычный DNS"""
    if host and not host.replace(".", "").isdigit():
        ip = resolve_via_doh(host)
        if ip:
            return _original_getaddrinfo(ip, port, family, type, proto, flags)
    
    return _original_getaddrinfo(host, port, family, type, proto, flags)


def patch_dns():
    """Активировать monkey-patch"""
    socket.getaddrinfo = _patched_getaddrinfo
    print("🌐 DNS через DoH (ИИ + перебор) активирован")

# ============================================================
# 9. ПРОВЕРКА
# ============================================================

def check_youtube():
    ip = resolve_via_doh("www.youtube.com")
    if ip:
        print(f"✅ YouTube резолвится: {ip}")
        return True
    print("❌ YouTube не резолвится")
    return False


def check_telegram():
    ip = resolve_via_doh("api.telegram.org")
    if ip:
        print(f"✅ Telegram резолвится: {ip}")
        return True
    print("❌ Telegram не резолвится")
    return False

# ============================================================
# 10. ЗАГРУЗКА
# ============================================================

print("🌐 dns_config загружен (ИИ + перебор)")
print(f"📋 Встроенных DoH: {len(BUILTIN_DOH_SERVERS)}")
print(f"⏱ Таймаут: {DOH_TIMEOUT}с")

# Проверка
check_telegram()
check_youtube()

# Активируем patch
patch_dns()