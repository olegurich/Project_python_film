from tabulate import tabulate
from colorama import init, Fore, Style


init(autoreset=True)  # Чтобы цвет сбрасывался автоматически после каждой строки

def color_by_type(t:str, value:str) -> str:
    """
    Окрашивает текст в зависимости от типа запроса.
    :param t: Тип запроса ("keyword", "genre_year" или другой).
    :param value: Текст, который нужно окрасить.
    :return: Окрашенная строка.
    """
    if t == "keyword":
        return Fore.GREEN + value + Style.RESET_ALL
    elif t == "genre_year":
        return Fore.BLUE + value + Style.RESET_ALL
    else:
        return Fore.RED + value + Style.RESET_ALL

def format_table(rows:str, headers=None) -> str:
    """
    Форматирует список строк в табличный вид с помощью tabulate.
    :param rows: Строки таблицы.
    :param headers: Заголовки столбцов.
    :return: Строка с отформатированной таблицей. При ошибке — пустая строка.
    """
    try:
        return tabulate(rows, headers=headers, tablefmt="grid")
    except Exception as e:
        print(f"Ошибка при форматировании таблицы: {e}")
        return ""

def format_film_results(rows: list[dict]) -> list[dict]:
    """
    Форматирует результаты поиска для отображения.
    :param rows: Список словарей с данными фильмов (title, release_year, category).
    :return: Список словарей с окрашенными и отформатированными значениями.
    """
    colored = []
    for row in rows:
        colored.append({
            "Название": color_by_type("keyword", row["title"]),
            "Год": str(row["release_year"]),
            "Жанр": color_by_type("genre_year", row["category"])
        })
    return colored

def display_film_results(formatted_rows) -> None:
    """
    Отображает отформатированные результаты поиска фильмов в виде таблицы.
    :param formatted_rows: Список словарей, подготовленных для отображения.
    :return: None
    """
    print(tabulate(formatted_rows, headers="keys", tablefmt="psql"))

def print_top_queries(top5: list[tuple]):
    """
    Выводит таблицу с 5 самыми популярными запросами пользователей.
    :param top5: Список кортежей вида ((тип запроса, текст запроса), количество).
    :return: None
    """
    print(Fore.YELLOW + Style.BRIGHT + "\n=== Топ 5 популярных запросов ===")
    colored = [(color_by_type(t, t), color_by_type(t, q), c) for ((t, q), c) in top5]
    print(format_table(colored, headers=["Тип запроса", "Запрос", "Кол-во запросов"]))

def print_last_queries(last5: list[tuple]):
    """
    Выводит таблицу с последними 5 запросами с подсветкой.
    :param last5: Список кортежей вида (тип запроса, текст запроса, количество найденных фильмов).
    :return: None
    """
    print(Fore.MAGENTA + Style.BRIGHT + "\n=== Последние 5 запросов ===")
    colored = [(color_by_type(t, t), color_by_type(t, q), str(r)) for (t, q, r) in last5]
    print(format_table(colored, headers=["Тип запроса", "Запрос", "Найдено фильмов"]))



