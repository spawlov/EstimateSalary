import asyncio
import logging
import os
from logging import Logger
from typing import Any

from dotenv import find_dotenv, load_dotenv

from handlers import get_stats_from_hh, get_stats_from_sj

from terminaltables import SingleTable


logging.basicConfig(level=logging.WARNING)
logger: Logger = logging.getLogger(__name__)


async def print_table(title: str, data: list[dict[str, Any]]) -> None:
    column_aligns = {
        1: "center",
        2: "center",
        3: "right",
    }
    terminal_table = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]
    for row in data:
        for language, lang_details in row.items():
            terminal_table.append(
                [
                    language,
                    lang_details["vacancies_found"],
                    lang_details["vacancies_processed"],
                    lang_details["average_salary"],
                ]
            )
    table = SingleTable(terminal_table, title)
    table.justify_columns.update(column_aligns)
    print(table.table)  # noqa


async def main() -> None:
    load_dotenv(find_dotenv())

    hh_base_url = os.environ["HH_BASE_URL"]
    sj_base_url = os.environ["SJ_BASE_URL"]
    sj_key: str = os.environ["SJ_KEY"]
    languages: list[str] = os.getenv("LANGS", "JavaScript, Java, Python").split(",")
    city: str | None = os.getenv("CITY", None)
    days_ago: int = int(os.getenv("DAYS", 7))

    sj_results = await get_stats_from_sj(sj_base_url, sj_key, languages, city, days_ago)
    await print_table(f" SuperJob. {city}, {days_ago} дней ", sj_results)

    hh_result = await get_stats_from_hh(hh_base_url, languages, city, days_ago)
    await print_table(f" HeadHunter. {city}, {days_ago} дней ", hh_result)


if __name__ == "__main__":
    asyncio.run(main())
