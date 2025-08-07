
from mongo_log_writer import connect_mongo
from formatter import print_top_queries, print_last_queries
from app_logger import logger


def show_stats() -> None:
    """
    Основная функция для вывода статистики.
    Показывает:
    - Топ-5 самых популярных запросов.
    - Последние 5 запросов.
    :return: None
    """
    try:
        logs = fetch_logs()
        top5 = get_top_queries(logs)
        print_top_queries(top5)
        

        last5 = get_last_queries(logs)
        print_last_queries(last5)

    except Exception as e:
        logger.error("Ошибка в функции show_stats", exc_info=True)
        print("Произошла ошибка при выводе статистики.")


def fetch_logs() -> list[dict]: 
    """
    Получает логи из MongoDB. Возвращает логи из MongoDB виде списка словарей.
    :return: Список словарей с логами. Если ошибка — возвращает пустой список.
    """
    collection = connect_mongo()
    if collection is None:
        logger.error("Не удалось получить коллекцию из MongoDB")
        return []
    logs = list(collection.find({}, {"_id": 0}).sort("createdAt", -1))
    logger.debug(f"Получено записей из MongoDB: {len(logs)}")
    return logs


# === Топ 5 популярных запросов ===

def get_top_queries(logs: list[dict]) -> list[tuple]:         
    """
    Получает топ-5 самых популярных запросов из списка логов.
    :param logs: Список логов (каждый лог — словарь).
    :return: Список кортежей вида ((тип, текст запроса), количество повторений).
    """
    counter = {}                                              
    for log in logs:
        t, q = extract_type_and_query(log)                     # Извлекаем из лога тип запроса (t, например "keyword" или "genre_year") и (q, например "Horror (2020-2023)").
        if t and q:                                            # Если тип, и строка запроса не пустые — учитываем.
            key = (t, q)                                       # Формируем ключ: кортеж из типа и текста запроса
            counter[key] = counter.get(key, 0) + 1             # Увеличиваем счётчик для этого конкретного запроса (Если его ещё нет — берём 0 и прибавляем 1.)
    top5 = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:5]
                                                                # Сортируем все запросы по количеству (по значению счётчика) в убывающем порядке и берём первые пять — топ-5 самых частых.
    return top5                                                 # Возвращаем список кортежей: [((тип, запрос), количество), ...] — 5 самых популярных.

# === Последние 5 запросов ===

def get_last_queries(logs: list[dict]) -> list[tuple]:
    """
    Получает последние 5 запросов из списка логов.
    :param logs: Список логов.
    :return: Список кортежей вида (тип, строка запроса, количество результатов).
    """
    return [
        (
            log.get("type", ""),
            extract_query_value(log),
            log.get("results", "")
        ) for log in logs[:5]
    ]

# === Вспомогательные функции ===

def extract_type_and_query(log: dict) -> tuple[str, str|None, int]:     
    """
    Извлекает тип запроса и текст запроса из записи лога.
    :param log: Словарь с данными одного лога.
    :return: Кортеж из двух значений — тип запроса и строка запроса (или None, если пусто).
    """
    t = log.get("type", "").strip()                    # Берёт значение по ключу "type" из лога. Если его нет — возвращает пустую строку.
    if not t:                                          # Проверяет, пустой ли тип
        return 0

    if t == "keyword":                                 # Если тип запроса — поиск по ключевому слову
        q = log.get("keyword", "").strip()              # Берёт само ключевое слово из лога (например, "love")

    elif t == "genre_year":                             # Если тип запроса жанр и диапазон годов.
        genre_name = log.get("genre_name", "").strip()  # Берёт название жанра из лога
        y_from = str(log.get("year_from", "")).strip()  #Берёт год начала диапазона
        y_to = str(log.get("year_to", "")).strip()      # Берёт год начала диапазона
        q = f"{genre_name} ({y_from}-{y_to})"             # Формирует строку вида "Horror (2020-2023)"
    else:
        q = log.get("query", "").strip()                # берёт из словаря log значение по ключу "query". Если такого ключа нет, возвращает пустую строку ""
    return (t, q if q else None)                        # возвращает кортеж из двух элементов: 1-тип запроса t (например, "keyword"), 
                                                        # 2-либо строка запроса, либо None, если она была пустой.

def extract_query_value(log: dict) -> str:
    """
    Возвращает строковое представление самого запроса, пригодное для показа в таблице 'последних запросов' (без типа)
    :param log: Словарь с данными одного лога.
    :return: Строка, описывающая сам запрос (например, "Horror (2020-2023)" или "love").
    """ 
    t = log.get("type", "")                            # Берём тип запроса из лога. Если его нет — получаем пустую строку.
    if t == "keyword":                                 # Если это поиск по ключевому слову
        return log.get("keyword", "")                  # возвращаем само слово (например, "love"). Если его нет — пустую строку.
    elif t == "genre_year":                            # Если это поиск по жанру и году
        genre_name = log.get("genre_name", "").strip()  # Берём название жанра
        return f"{genre_name} ({log.get('year_from', '')}-{log.get('year_to', '')})" # Формируем строку вида "Horror (2020-2023)": жанр и диапазон.
    else:
        return log.get("query", "")                    # Для всех других типов запросов  возвращаем значение из поля query.                         
