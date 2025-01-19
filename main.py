import asyncio
import logging
import os
from logging import Logger
from time import time

from dotenv import find_dotenv, load_dotenv

from handlers import get_stats_from_hh

import httpx

from icecream import ic


logging.basicConfig(level=logging.INFO)
logger: Logger = logging.getLogger(__name__)


async def get_vacancies_from_sj(secret_key: str, language: str, city: str) -> None:
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36",
        "X-Api-App-Id": secret_key,
    }
    # catalog_index = 33
    # vacs_per_page = 100
    params = {
        "town": city,
        # "catalogues": catalog_index,
        # 'count': vacs_per_page,
        "keyword": language,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers, params=params, timeout=30)

    response.raise_for_status()
    payload = response.json()
    # ic(payload)
    for vacancy in payload["objects"]:
        if vacancy["payment_from"] or vacancy["payment_from"]:
            logger.info(f"{vacancy["profession"]}, {vacancy["payment_from"]}, {vacancy["payment_to"]}")
    # profession
    # , {vacancy["address"]}

    # vacs_processed, salary_sum = 0, 0

    # for page in itertools.count(start=0):
    #     params['page'] = page
    #     response = requests.get(
    #         url='https://api.superjob.ru/2.0/vacancies/',
    #         headers=header,
    #         params=params
    #     )
    #     response.raise_for_status()
    #     vacancies = response.json()


async def main() -> None:
    load_dotenv(find_dotenv())
    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler("main.log", encoding="utf-8")
    log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(log_handler)

    hh_base_url = os.environ["HH_BASE_URL"]
    sj_key: str = os.environ["SJ_KEY"]
    languages: list[str] = os.getenv("LANGS", "JavaScript, Java, Python").split(",")
    city: str | None = os.getenv("CITY", None)
    days_ago: int = int(os.getenv("DAYS", 7))

    logger.info("Starting process for HH...")
    t0 = time()
    await get_vacancies_from_sj(sj_key, "Python", "Москва")
    ic(await get_stats_from_hh(base_url=hh_base_url, languages=languages, city=city, days_ago=days_ago))
    logger.info(f"Time to process HH: {time() - t0:.4f}sec.")


if __name__ == "__main__":
    # main()
    asyncio.run(main())
