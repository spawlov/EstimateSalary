import itertools
import logging
from datetime import datetime, timedelta
from time import time
from typing import Any

import httpx

from icecream import ic

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


def predict_rub_salary(salary_from: int, salary_to: int) -> int:
    if salary_from and salary_to:
        return round((salary_from + salary_to) / 2)
    if salary_from:
        return round(salary_from * 1.2)
    if salary_to:
        return round(salary_to * 0.8)
    if not salary_from and not salary_to:
        return 0


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
        "text": language,
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
    return language, payload


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


def main() -> None:
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
    ic(get_stats_from_hh(languages, days_ago=7))
    logger.info(f"Time to process HH: {time() - t0:.4f}sec.")


if __name__ == "__main__":
    main()
