import asyncio
import itertools
from datetime import datetime, timedelta
from typing import Any

import httpx

from .handler_utils import predict_rub_salary


async def get_hh_city_id(base_url: str, city_name: str) -> int:
    async with httpx.AsyncClient(base_url=base_url) as client:
        response = await client.get(url="areas/", timeout=30)
    areas = response.json()

    def find_city(areas: Any, city_name: str) -> int:
        for area in areas:
            if area["name"].lower() == city_name.lower():
                return area["id"]
            if "areas" in area:
                city_id = find_city(area["areas"], city_name)
                if city_id:
                    return city_id
        return 0

    return find_city(areas, city_name)


async def get_vacancies_from_hh(
    base_url: str,
    language: str,
    city_id: int,
    days_ago: int,
) -> tuple[str, dict[str, list]]:
    print("HeadHunter in the process...", end="\r")  # noqa

    today = datetime.now()
    date_days_ago = today - timedelta(days=days_ago)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
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

    vacancy_list = []
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        for page in itertools.count(1):
            params["page"] = page
            response = await client.get(url="vacancies/", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            vacancy_list += payload["items"]
            if page >= payload["pages"] - 1:
                break
            params["page"] = page
            await asyncio.sleep(3)
    payload["items"] = vacancy_list
    return language.strip(), payload


async def get_stats_from_hh(
    base_url: str,
    languages: list[str],
    city: str | None = None,
    days_ago: int = 7,
) -> list[dict[str, Any]]:
    city_id = await get_hh_city_id(base_url, city) if city else 0
    tasks = [get_vacancies_from_hh(base_url, language, city_id, days_ago) for language in languages]
    statistics = await asyncio.gather(*tasks)

    result = []
    for statistic in statistics:
        language, response = statistic
        vacancies = [vacancy for vacancy in response["items"] if vacancy["salary"]]
        vacancies = [vacancy for vacancy in vacancies if vacancy["salary"]["currency"] == "RUR"]
        average_salary = (
            int(
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
            if len(vacancies)
            else 0
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
