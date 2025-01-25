import asyncio
import itertools
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

from handlers.handler_utils import predict_rub_salary


async def get_vacancies_from_sj(
    secret_key: str,
    language: str,
    days_ago: int,
    city: str | None = None,
) -> tuple[str, dict[str, list]]:
    today = int(time.time())
    date_days_ago = int((datetime.now() - timedelta(days=days_ago)).timestamp())
    catalog = 33  # https://api.superjob.ru/2.0/catalogues/
    results_per_page = 100

    base_url = "https://api.superjob.ru/2.0/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36",
        "X-Api-App-Id": secret_key,
    }
    params = {
        "date_published_from": date_days_ago,
        "date_published_to": today,
        "catalogues": catalog,
        "count": results_per_page,
        "keyword": language.strip(),
    }
    if city:
        params["town"] = city

    vacancies = []
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        for page in itertools.count(0):
            params["page"] = page
            response = await client.get(url="vacancies/", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            vacancies += payload["objects"]
            if not payload["more"]:
                break
    payload["objects"] = vacancies
    return language.strip(), payload


async def get_stats_from_sj(
    secret_key: str,
    languages: list[str],
    city: str | None = None,
    days_ago: int = 7,
) -> list[dict[str, Any]]:
    tasks = [get_vacancies_from_sj(secret_key, language, days_ago, city) for language in languages]
    statistics = await asyncio.gather(*tasks)

    statistic = []
    for language, response in statistics:
        average_salary = 0
        vacancies = [
            vacancy
            for vacancy in response["objects"]
            if vacancy["currency"] == "rub" and vacancy["payment_from"] or vacancy["payment_to"]
        ]

        if len(vacancies):
            salaries = [
                await predict_rub_salary(vacancy["payment_from"], vacancy["payment_to"]) for vacancy in vacancies
            ]
            average_salary = int(sum(salaries) / len(vacancies))

        statistic.append(
            {
                language: {
                    "vacancies_found": response["total"],
                    "vacancies_processed": len(vacancies),
                    "average_salary": f"{average_salary:,}₽",
                },
            },
        )

    return statistic
