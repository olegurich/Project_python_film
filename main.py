from mysql_connector import get_connection, search_by_title, search_by_genre_and_year
from mongo_log_writer import log_search, close_mongo_client, client
from log_stats import show_stats  
from app_logger import logger


def main() -> None:
    """
       Главная функция приложения.
       Отвечает за:
       - Подключение к базе данных MySQL.
       - Отображение главного меню.
       - Обработку пользовательского ввода.
       - Запуск поиска фильмов по названию или по жанру и году.
       - Отображение статистики запросов.
       - Логирование действий и закрытие соединений (MySQL и MongoDB).
       """

    print("Добро пожаловать в систему поиска фильмов!")

    # MySQL: открываем одно соединение и один курсор
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                while True:
                    print("\n=== МЕНЮ ===")
                    print("1. Поиск по названию")
                    print("2. Поиск по жанру и диапазону годов ")
                    print("3. Статистика запросов")
                    print("0. Выход")

                    choice = input("Сделайте ваш выбор и нажмите 'Enter': ").strip()

                    if choice == "1":
                        try:
                            result_count, params = search_by_title(cursor)
                            log_search({"type": "keyword", **(params or {}), "results": result_count})
                        except Exception:
                            logger.error("Ошибка при поиске по названию", exc_info=True)
                            print("Ошибка при выполнении поиска.")

                    elif choice == "2":
                        try:
                            result_count, params = search_by_genre_and_year(cursor)
                            log_search({"type": "genre_year", **(params or {}), "results": result_count})
                        except Exception:
                            logger.error("Ошибка при поиске по жанру и году", exc_info=True)
                            print("Ошибка при выполнении поиска.")

                    elif choice == "3":
                        try:
                            show_stats()
                        except Exception:
                            logger.error("Ошибка при показе статистики", exc_info=True)
                            print("Ошибка при выводе статистики.")

                    elif choice == "0":
                        print("Выход из программы. До свидания!")
                        break


                    else:
                        print("Неверный выбор. Попробуйте снова.")
        logger.info("MySQL соединение закрыто")
    except Exception as e:
        logger.error("Ошибка подключения к MySQL или при работе с ней", exc_info=True)
        print(f"Ошибка подключения или внутреняя ошибка: {e}")

    # Закрываем MongoDB
    if client:
        try:
            close_mongo_client(client)
        except Exception:
            logger.error("Ошибка при закрытии MongoDB", exc_info=True)

if __name__ == "__main__":
    main()