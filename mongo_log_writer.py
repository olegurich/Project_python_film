from pymongo import MongoClient
from datetime import datetime
import os
from app_logger import logger


mongo_url = os.getenv("MONGO_URL")
mongo_db_name = os.getenv("MONGO_DB")
mongo_collection_name = os.getenv("MONGO_COLLECTION")
client = MongoClient(mongo_url)


def connect_mongo():
    """
    Устанавливает подключение к MongoDB и возвращает коллекцию.
    :return: Коллекция MongoDB, если подключение успешно. Иначе — None.
    """
    try:
        db = client[mongo_db_name]
        collection = db[mongo_collection_name]
        logger.info("Успешное подключение к MongoDB")
        return collection
    except Exception as e:
        logger.error(f"Ошибка подключения к MongoDB: {e}", exc_info=True)
        return None
    
def log_search(data: dict) -> int:
    """
    Записывает данные поиска в MongoDB с текущей датой и временем.
    :param data: Словарь с данными для логирования.
    :return: 1 — если лог успешно записан, 0 — при ошибке.
    """
    collection = connect_mongo()
    if collection is None:
        logger.error("Невозможно записать лог: нет подключения к MongoDB")
        return 0
    try:
        data["createdAt"] = datetime.now()
        collection.insert_one(data)                           # Метод из библиотеки pymongo, чтобы  вставить один документ в MongoDB
        return 1
    except Exception as e:
        logger.error(f"Ошибка записи лога в MongoDB: {e}", exc_info=True)
        return 0


def close_mongo_client(client):
    """
    Закрывает соединение с MongoDB, если клиент открыт.
    :param client: Объект клиента MongoDB, который нужно закрыть.
    :return: None
    """
    try:
        if client:
            client.close()
            logger.info("Mongo DB соединение закрыто")

    except Exception as e:
        logger.error(f"Ошибка при закрытии MongoDB: {e}", exc_info=True)
