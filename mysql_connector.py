import pymysql
from pymysql.err import MySQLError
from typing import Dict, Tuple
from dotenv import load_dotenv
import os
from app_logger import logger
from formatter import color_by_type, tabulate, format_film_results, display_film_results


load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")


def get_connection() -> pymysql.Connection:
    """
    Подключается к MySql(данные для подключения в .env)
    :returns: объект подключения к базе данных.
    :raise: если не удалось подключиться к базе.
    """
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        logger.info("Успешное подключение к MySQL")
        return connection
    except MySQLError as e:
        logger.error(f"Ошибка при подключении к MySQL: {e}", exc_info=True)
        raise


def print_genres(cursor) -> None:
    """
    Выводит список жанров с их ID и названиями, окрашенными в цвет.
    :param cursor: Объект курсора базы данных.
    :return: None 
    """
    cursor.execute("SELECT category_id, name FROM category;")
    rows = cursor.fetchall()
    colored_rows = []
    for row in rows:
        colored_rows.append({
            "ID": row["category_id"],
            "Жанр": color_by_type("genre_year", row["name"])
        })
    print(tabulate(colored_rows, headers="keys", tablefmt="psql"))


def get_search_keyword() -> str: 
    """
    Запрашивает у пользователя ключевое слово для поиска фильмов.
    :return: Введённое пользователем ключевое слово, либо None если оно пустое.
    """
    keyword = input("Введите ключевое слово для поиска в названии фильма: ").strip()
    if not keyword:
        print("Ключевое слово не может быть пустым.")
        return None
    return keyword


def execute_film_search(cursor, keyword: str, limit: int, offset: int) -> list[dict]:
    """
    Выполняет поиск фильмов по ключевому слову в базе данных.
    :param cursor: Объект курсора базы данных.
    :param keyword: Ключевое слово для поиска.
    :param limit: Количество фильмов на странице.
    :param offset: Смещение для постраничного вывода.
    :return: Список словарей с информацией о фильмах.
    """
    query = """
            SELECT f.title, \
                    f.release_year, \
                    c.name AS category
                    FROM film f
                            JOIN film_category fc ON f.film_id = fc.film_id
                            JOIN category c ON fc.category_id = c.category_id
                    WHERE f.title LIKE %s
                        LIMIT %s 
                    OFFSET %s; \
            """
    pattern = f"%{keyword}%"
    cursor.execute(query, (pattern, limit, offset))
    return cursor.fetchall()

def ask_for_next_page() -> bool:
    """
    Спрашивает у пользователя, хочет ли он продолжить просмотр следующей страницы.
    :return: True — если пользователь хочет продолжить, False — если вводит '0'.
    """
    response = input("Показать следующие 10 фильмов? (Enter — да, '0' — выход): ").strip().lower()
    return response != "0"


def search_by_title(cursor) -> tuple[int, dict]:
    """
    Основная логика поиска фильмов по названию с пагинацией.
    :param cursor: Объект курсора базы данных.
    :return: Кортеж: количество найденных фильмов и параметры поиска.
    """
    try:
        keyword = get_search_keyword()
        if not keyword:
            return 0, {}

        offset = 0
        limit = 10
        total_count = 0
        params = {"keyword": keyword}

        while True:
            rows = execute_film_search(cursor, keyword, limit, offset)

            if not rows:
                message = "Фильмы не найдены." if offset == 0 else "Больше фильмов нет."
                print(message)
                break

            formatted_rows = format_film_results(rows)
            display_film_results(formatted_rows)
            total_count += len(rows)

            if not ask_for_next_page():
                break
            offset += limit

        print(f"Найдено фильмов: {total_count}")
        logger.info(f"Поиск по названию выполнен: {params}")
        return total_count, params

    except Exception as e:
        logger.error("Ошибка в search_by_title", exc_info=True)
        print("Произошла ошибка при поиске по названию.")
        return 0, {}
    

def get_genre_id(cursor) -> int|None:
    """
    Запрашивает у пользователя ID жанра и проверяет его корректность.
    :param cursor: Объект курсора базы данных.
    :return: Целое число — ID жанра или None при ошибке.
    """
    print("Доступные жанры:")
    print_genres(cursor)

    genre_id_raw = input("Введите ID жанра: ").strip()
    if not genre_id_raw.isdigit():
        print("Ошибка: ID жанра должен быть числом.")
        return None

    return int(genre_id_raw)


def validate_genre_exists(cursor, genre_id: int) -> str|None:
    """
    Проверяет существование жанра с заданным ID.
    :param cursor: Объект курсора базы данных.
    :param genre_id: Введённый пользователем ID жанра.
    :return: Название жанра или None, если жанр не найден.
    """
    cursor.execute("SELECT name FROM category WHERE category_id = %s;", (genre_id,))
    genre_row = cursor.fetchone()

    if not genre_row:
        print(f"Жанр с ID {genre_id} не найден.")
        return None

    return genre_row["name"]


def get_year_range() -> tuple[int|None, int|None]:
    """
    Запрашивает у пользователя диапазон годов и проверяет его.
    :return: Кортеж из двух целых чисел (год от, год до), либо (None, None) при ошибке.
    """
    print("Фильмы представленны от 1990 до 2025.\nДля поиска по конкретному году введите год в обоих полях ")
    year_from_raw = input("Год от: ").strip()
    year_to_raw = input("Год до: ").strip()

    if not (year_from_raw.isdigit() and year_to_raw.isdigit()):
        print("Ошибка: год должен быть числом.")
        return None, None

    year_from = int(year_from_raw)
    year_to = int(year_to_raw)

    if year_from > year_to:
        print("Год 'от' не может быть больше года 'до'.")
        return None, None

    if not (1990 <= year_from <= 2025 and 1990 <= year_to <= 2025):
        print("Ошибка: год должен быть в диапазоне от 1990 до 2025.")
        return None, None

    return year_from, year_to


def execute_genre_year_search(cursor, genre_id: int, year_from: int, year_to: int, limit: int, offset: int) -> list[dict]:
    """
    Выполняет поиск фильмов по жанру и годам.
    :param cursor: Объект курсора базы данных.
    :param genre_id: ID выбранного жанра.
    :param year_from: Начальный год диапазона.
    :param year_to: Конечный год диапазона.
    :param limit: Количество фильмов на странице.
    :param offset: Смещение для постраничного вывода.
    :return: Список словарей с найденными фильмами.
    """
    query = """
            SELECT f.title, \
                    f.release_year, \
                    c.name AS category
            FROM film f
                JOIN film_category fc ON f.film_id = fc.film_id
                JOIN category c ON fc.category_id = c.category_id
            WHERE c.category_id = %s
            AND f.release_year BETWEEN %s AND %s
            LIMIT %s \
            OFFSET %s; \
            """
    cursor.execute(query, (genre_id, year_from, year_to, limit, offset))
    return cursor.fetchall()


def create_search_params(genre_id: int, genre_name: str, year_from: int, year_to: int) -> dict[str, object]: 
    """
    Формирует словарь параметров поиска.
    :param genre_id: ID жанра.
    :param genre_name: Название жанра.
    :param year_from: Начальный год.
    :param year_to: Конечный год.
    :return: Словарь с параметрами поиска.
    """
    return {
        "genre_id": genre_id,
        "genre_name": genre_name,
        "year_from": year_from,
        "year_to": year_to
    }

def search_by_genre_and_year(cursor) -> Tuple[int, Dict]:
    """
    Основная логика поиска фильмов по жанру и диапазону годов.
    :param cursor: Объект курсора базы данных.
    :return: Кортеж: количество найденных фильмов и параметры поиска
    """
    try:
        genre_id = get_genre_id(cursor)                    # Получение и валидация жанра
        if genre_id is None:
            return 0, {}

        genre_name = validate_genre_exists(cursor, genre_id)
        if genre_name is None:
            return 0, {}

        year_from, year_to = get_year_range()              # Получение и валидация диапазона лет
        if year_from is None or year_to is None:
            return 0, {}

        offset = 0                                         # Настройка параметров поиска
        limit = 10
        total_count = 0
        params = create_search_params(genre_id, genre_name, year_from, year_to)

        while True:                                         # Основной цикл поиска с пагинацией
            rows = execute_genre_year_search(cursor, genre_id, year_from, year_to, limit, offset)

            if not rows:
                message = "Фильмы не найдены." if offset == 0 else "Больше фильмов нет."
                print(message)
                break

            formatted_rows = format_film_results(rows)
            display_film_results(formatted_rows)
            total_count += len(rows)

            if not ask_for_next_page():
                break
            offset += limit

        print(f"Найдено фильмов: {total_count}")
        logger.info(f"Поиск по жанру и году выполнен: {params}")
        return total_count, params

    except Exception as e:
        logger.error("Ошибка в search_by_genre_and_year", exc_info=True)
        print("Произошла ошибка при поиске по жанру и году.")
        return 0, {}