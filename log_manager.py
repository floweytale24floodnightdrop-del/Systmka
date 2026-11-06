"""Умный логгер — не дублирует одинаковые ошибки"""

import os
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

DEFAULT_LOG_FILE = "bot.log"
MAX_DUPLICATES = 3
MAX_LOG_SIZE_MB = 10

# ============================================================
# 2. КЛАСС ЛОГГЕРА
# ============================================================

class SmartLogger:
    """Умный логгер с дедупликацией"""
    
    def __init__(self, log_file=DEFAULT_LOG_FILE, max_duplicates=MAX_DUPLICATES):
        self.log_file = log_file
        self.max_duplicates = max_duplicates
        self.last_message = None
        self.message_start_time = None
        self.message_count = 0
    
    def _write(self, text):
        """Записать строку в лог"""
        try:
            # Проверяем размер файла
            self._check_rotate()
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"⚠️ Ошибка записи в лог: {e}")
    
    def _check_rotate(self):
        """Проверить и ротировать лог, если слишком большой"""
        try:
            if not os.path.exists(self.log_file):
                return
            
            size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
            
            if size_mb < MAX_LOG_SIZE_MB:
                return
            
            # Обрезаем до 1000 последних строк
            with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.writelines(lines[-1000:])
        except Exception:
            pass
    
    def log(self, message, level="INFO"):
        """Логировать сообщение с дедупликацией"""
        if not message:
            return
        
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Дубликат
        if message == self.last_message:
            self.message_count += 1
            
            if self.message_count > self.max_duplicates:
                return
            
            formatted = (
                f"[{timestamp}] (продолжается с {self.message_start_time}) "
                f"{message} (x{self.message_count})"
            )
        else:
            # Новое сообщение — записываем итог предыдущего
            if self.last_message and self.message_count > self.max_duplicates:
                self._write(
                    f"[{timestamp}] (завершено: "
                    f"{self.message_start_time} - {timestamp}) "
                    f"{self.last_message} (всего x{self.message_count})"
                )
            
            self.last_message = message
            self.message_start_time = timestamp
            self.message_count = 1
            
            formatted = f"[{timestamp}] {message}"
        
        self._write(formatted)
    
    def error(self, error, source="unknown"):
        """Логировать ошибку"""
        self.log(f"❌ ({source}): {error}", "ERROR")
    
    def info(self, message):
        """Логировать информацию"""
        self.log(f"ℹ️ {message}", "INFO")
    
    def warning(self, message):
        """Логировать предупреждение"""
        self.log(f"⚠️ {message}", "WARN")
    
    def debug(self, message):
        """Логировать отладку"""
        self.log(f"🔍 {message}", "DEBUG")
    
    def get_stats(self):
        """Получить статистику лога"""
        try:
            if not os.path.exists(self.log_file):
                return {"exists": False}
            
            size_bytes = os.path.getsize(self.log_file)
            
            with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            return {
                "exists": True,
                "size_kb": round(size_bytes / 1024, 2),
                "lines": len(lines),
                "file": self.log_file,
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}

# ============================================================
# 3. ГЛОБАЛЬНЫЙ ЛОГГЕР
# ============================================================

smart_logger = SmartLogger()

# ============================================================
# 4. ЗАГРУЗКА
# ============================================================

stats = smart_logger.get_stats()

print("📋 Умный логгер загружен (PC)")
if stats.get("exists"):
    print(f"📁 Файл: {stats['file']}")
    print(f"💾 Размер: {stats['size_kb']}KB ({stats['lines']} строк)")
else:
    print(f"📁 Файл: {DEFAULT_LOG_FILE} (ещё не создан)")