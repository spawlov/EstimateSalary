import asyncio
import itertools
import time
from datetime import datetime, timedelta
from typing import Any

from handlers.handler_utils import predict_rub_salary

import httpx


async def get_vacancies_from_sj(
    base_url: str,
    secret_key: str,
    language: str,
    days_ago: int,
    city: str | None = None,
) -> tuple[str, dict[str, list]]:
    print("SuperJob in the process...", end="\r")  # noqa

    today = int(time.time())
    date_days_ago = int((datetime.now() - timedelta(days=days_ago)).timestamp())

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36",
        "X-Api-App-Id": secret_key,
    }
    params = {
        "date_published_from": date_days_ago,
        "date_published_to": today,
        "catalogues": 33,
        "count": 100,
        "keyword": language.strip(),
    }
    if city:
        params["town"] = city

    vacancy_list = []
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        for page in itertools.count(0):
            params["page"] = page
            response = await client.get(url="vacancies/", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            vacancy_list += payload["objects"]
            if not payload["more"]:
                break
    payload["objects"] = vacancy_list
    return language.strip(), payload


async def get_stats_from_sj(
    base_url: str,
    secret_key: str,
    languages: list[str],
    city: str | None = None,
    days_ago: int = 7,
) -> list[dict[str, Any]]:
    tasks = [get_vacancies_from_sj(base_url, secret_key, language, days_ago, city) for language in languages]
    statistics = await asyncio.gather(*tasks)

    result = []
    for statistic in statistics:
        language, response = statistic
        vacancies = [
            vacancy
            for vacancy in response["objects"]
            if vacancy["currency"] == "rub" and vacancy["payment_from"] or vacancy["payment_to"]
        ]
        average_salary = (
            int(
                sum(
                    [
                        await predict_rub_salary(
                            vacancy["payment_from"],
                            vacancy["payment_to"],
                        )
                        for vacancy in vacancies
                    ]
                )
                / len(vacancies)
            )
            if len(vacancies)
            else 0
        )
        result.append(
            {
                language: {
                    "vacancies_found": response["total"],
                    "vacancies_processed": len(vacancies),
                    "average_salary": f"{average_salary:,}₽",
                }
            }
        )
    return result
