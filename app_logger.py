import logging
from datetime import datetime

def log_error(error: Exception, func_name: str):
    """
    Логирует ошибку с указанием функции и времени.
    :param error: Объект исключения.
    :param func_name: Название функции, в которой произошла ошибка.
    :return: None
    """
    logger.error(f"[{datetime.now()}] Ошибка в функции {func_name}: {error}")

# Удаляем старые обработчики, если они есть
if logging.root.handlers:
    logging.root.removeHandler(logging.root.handlers[0])

# Настраиваем логгер с простым читаемым форматом
logging.basicConfig(
    filename="app.log",
    format="%(asctime)s - %(levelname)s: %(message)s", 
    level=logging.DEBUG,  
    encoding='utf-8'
)

# Отключаем подробный лог MongoDB
logging.getLogger("pymongo").setLevel(logging.WARNING)

# Создаём объект логгера для использования в коде
logger = logging.getLogger(__name__)