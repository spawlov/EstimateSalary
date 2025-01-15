import asyncio
import itertools
import logging
from datetime import datetime, timedelta
from time import time
from typing import Any

import httpx

from icecream import ic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def predict_rub_salary(salary_from: int, salary_to: int) -> int:
    if salary_from and salary_to:
        return round((salary_from + salary_to) / 2)
    if salary_from:
        return round(salary_from * 1.2)
    if salary_to:
        return round(salary_to * 0.8)
    if not salary_from and not salary_to:
        return 0


async def get_vacancies_from_hh(
    language: str,
    days_ago: int,
):
    today = datetime.now()
    date_days_ago = today - timedelta(days=days_ago)
    url = "https://api.hh.ru/vacancies/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    }

    params = {
        "text": language,
        "area": 1,
        "per_page": 100,
        "date_from": date_days_ago.strftime("%Y-%m-%d"),
        "date_to": today.strftime("%Y-%m-%d"),
    }

    vacancy_list = []
    payload = {}
    for page in itertools.count(1):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        vacancy_list += payload["items"]
        if page == payload["pages"]:
            break
        params["page"] = page
    payload["items"] = vacancy_list
    return language, payload


async def get_stats_from_hh(languages: list[str], days_ago: int = 7) -> list[dict[str, Any]]:
    result = []
    tasks = [get_vacancies_from_hh(language, days_ago) for language in languages]
    statistics = await asyncio.gather(*tasks)
    for statistic in statistics:
        language, response = statistic
        vacancies = [vacancy for vacancy in response["items"] if vacancy["salary"]]
        vacancies = [vacancy for vacancy in vacancies if vacancy["salary"]["currency"] == "RUR"]
        average_salary = int(
            sum(
                [
                    await predict_rub_salary(
                        vacancy["salary"]["from"],
                        vacancy["salary"]["to"],
                    )
                    for vacancy in vacancies
                ]
            )
            / len(vacancies)
        )
        result.append(
            {
                language: {
                    "vacancies_found": response["found"],
                    "vacancies_processed": len(vacancies),
                    "average_salary": f"{average_salary:,}₽",
                },
            }
        )
    return result


async def main() -> None:
    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler("main.log", encoding="utf-8")
    log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(log_handler)

    languages = [
        "JavaScript",
        "Java",
        "Python",
        "Ruby",
        "PHP",
        "C++",
        "C#",
        "C",
        "Go",
    ]
    logger.info("Starting process for HH...")
    t0 = time()
    ic(await get_stats_from_hh(languages, 1))
    logger.info(f"Time to process HH: {time() - t0:.4f}sec.")


if __name__ == "__main__":
    asyncio.run(main())
