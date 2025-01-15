import itertools
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from .handler_utils import predict_rub_salary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_hh_city_id(city_name: str) -> int:
    with httpx.Client() as client:
        response = client.get("https://api.hh.ru/areas")

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


def get_vacancies_from_hh(
    language: str,
    city_id: int,
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
        "text": language.strip(),
        "per_page": 100,
        "date_from": date_days_ago.strftime("%Y-%m-%d"),
        "date_to": today.strftime("%Y-%m-%d"),
    }
    if city_id:
        params["area"] = city_id

    vacancy_list = []
    payload = {}
    for page in itertools.count(1):
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        vacancy_list += payload["items"]
        if page == payload["pages"]:
            break
        params["page"] = page
    payload["items"] = vacancy_list
    return language.strip(), payload


def get_stats_from_hh(languages: list[str], city: str | None = None, days_ago: int = 7) -> list[dict[str, Any]]:
    city_id = get_hh_city_id(city) if city else 0
    result = []
    statistics = [get_vacancies_from_hh(language, city_id, days_ago) for language in languages]
    for statistic in statistics:
        language, response = statistic
        vacancies = [vacancy for vacancy in response["items"] if vacancy["salary"]]
        vacancies = [vacancy for vacancy in vacancies if vacancy["salary"]["currency"] == "RUR"]
        average_salary = (
            int(
                sum(
                    [
                        predict_rub_salary(
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
