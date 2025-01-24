import asyncio
import itertools
from datetime import datetime, timedelta
from typing import Any

import httpx

from .handler_utils import predict_rub_salary


def find_city(areas: Any, city_name: str) -> int:
    for area in areas:
        if area["name"].lower() == city_name.lower():
            return area["id"]
        if "areas" in area:
            city_id = find_city(area["areas"], city_name)
            if city_id:
                return city_id
    return 0


async def get_hh_city_id(city_name: str) -> int:
    base_url = "https://api.hh.ru/"
    async with httpx.AsyncClient(base_url=base_url) as client:
        response = await client.get(url="areas/", timeout=30)
    response.raise_for_status()
    areas = response.json()
    return find_city(areas, city_name)


async def get_vacancies_from_hh(
    hh_key: str,
    language: str,
    city_id: int,
    days_ago: int,
) -> tuple[str, dict[str, list]]:
    today = datetime.now()
    date_days_ago = today - timedelta(days=days_ago)

    base_url = "https://api.hh.ru/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36",
        "Authorization": f"Bearer {hh_key}",
    }
    params = {
        "text": language.strip(),
        "per_page": 100,
        "date_from": date_days_ago.strftime("%Y-%m-%d"),
        "date_to": today.strftime("%Y-%m-%d"),
        "page": 0,
    }
    if city_id:
        params["area"] = city_id

    vacancies = []
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        for page in itertools.count(1):
            params["page"] = page
            response = await client.get(url="vacancies/", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            vacancies += payload["items"]
            if page >= payload["pages"] - 1:
                break
            params["page"] = page
    payload["items"] = vacancies
    return language.strip(), payload


async def get_stats_from_hh(
    hh_key: str,
    languages: list[str],
    city: str | None = None,
    days_ago: int = 7,
) -> list[dict[str, Any]]:
    city_id = await get_hh_city_id(city) if city else 0
    tasks = [get_vacancies_from_hh(hh_key, language, city_id, days_ago) for language in languages]
    statistics = await asyncio.gather(*tasks)

    statistic = []
    for language, response in statistics:
        average_salary = 0
        vacancies = [vacancy for vacancy in response["items"] if vacancy["salary"]]
        vacancies = [vacancy for vacancy in vacancies if vacancy["salary"]["currency"] == "RUR"]

        if len(vacancies):
            salaries = [
                await predict_rub_salary(vacancy["salary"]["from"], vacancy["salary"]["to"]) for vacancy in vacancies
            ]
            average_salary = int(sum(salaries) / len(vacancies))

        statistic.append(
            {
                language: {
                    "vacancies_found": response["found"],
                    "vacancies_processed": len(vacancies),
                    "average_salary": f"{average_salary:,}₽",
                },
            }
        )

    return statistic
