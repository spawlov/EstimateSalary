import asyncio
import logging
import os
from logging import Logger
from time import time
from typing import Any

from dotenv import find_dotenv, load_dotenv
from terminaltables import SingleTable

from handlers import get_stats_from_hh, get_stats_from_sj

logger: Logger = logging.getLogger(__name__)


def print_table(title: str, statistic: list[dict[str, Any]]) -> None:
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

    for row in statistic:
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
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("concurrent").setLevel(logging.WARNING)
    logging.getLogger("dotenv").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    load_dotenv(find_dotenv())

    sj_key: str = os.environ["SJ_KEY"]
    languages: list[str] = os.getenv("LANGS", "JavaScript, Java, Python").split(",")
    city: str | None = os.getenv("CITY", None)
    days_ago: int = int(os.getenv("DAYS", 30))

    logger.info("SuperJob process started...")
    time_start = time()
    sj_results = await get_stats_from_sj(sj_key, languages, city, days_ago)
    time_end = time()
    print_table(f" SuperJob. {city}, {days_ago} дней ", sj_results)
    logger.info(f"SuperJob process is completed in {time_end - time_start} sec.")

    logger.info("HeadHunter process started...")
    time_start = time()
    hh_result = await get_stats_from_hh(languages, city, days_ago)
    time_end = time()
    print_table(f" HeadHunter. {city}, {days_ago} дней ", hh_result)
    logger.info(f"HeadHunter process is completed in {time_end - time_start} sec.")


if __name__ == "__main__":
    asyncio.run(main())
