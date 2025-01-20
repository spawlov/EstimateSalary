import asyncio
import logging
import os
from logging import Logger
from time import time

from dotenv import find_dotenv, load_dotenv

from handlers import get_stats_from_hh
from handlers.sj_handler import get_stats_from_sj

from icecream import ic


logging.basicConfig(level=logging.INFO)
logger: Logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv(find_dotenv())
    # logger.setLevel(logging.INFO)
    # log_handler = logging.FileHandler("main.log", encoding="utf-8")
    # log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    # logger.addHandler(log_handler)

    hh_base_url = os.environ["HH_BASE_URL"]
    sj_base_url = os.environ["SJ_BASE_URL"]
    sj_key: str = os.environ["SJ_KEY"]
    languages: list[str] = os.getenv("LANGS", "JavaScript, Java, Python").split(",")
    city: str | None = os.getenv("CITY", None)
    days_ago: int = int(os.getenv("DAYS", 7))

    logger.info("Starting process...")
    t0 = time()

    sj_result = await get_stats_from_sj(
        base_url=sj_base_url, secret_key=sj_key, languages=languages, city=city, days_ago=days_ago
    )

    ic(sj_result)

    hh_result = await get_stats_from_hh(base_url=hh_base_url, languages=languages, city=city, days_ago=days_ago)

    logger.info(f"Time to process: {time() - t0:.4f}sec.")

    ic(hh_result)


if __name__ == "__main__":
    # main()
    asyncio.run(main())
