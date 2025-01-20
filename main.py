import asyncio
import logging
import os
from logging import Logger

from dotenv import find_dotenv, load_dotenv

from handlers import get_stats_from_hh
from handlers.sj_handler import get_stats_from_sj

logging.basicConfig(level=logging.WARNING)
logger: Logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv(find_dotenv())

    hh_base_url = os.environ["HH_BASE_URL"]
    sj_base_url = os.environ["SJ_BASE_URL"]
    sj_key: str = os.environ["SJ_KEY"]
    languages: list[str] = os.getenv("LANGS", "JavaScript, Java, Python").split(",")
    city: str | None = os.getenv("CITY", None)
    days_ago: int = int(os.getenv("DAYS", 7))

    sj_result = await get_stats_from_sj(  # noqa
        base_url=sj_base_url, secret_key=sj_key, languages=languages, city=city, days_ago=days_ago
    )

    hh_result = await get_stats_from_hh(base_url=hh_base_url, languages=languages, city=city, days_ago=days_ago)  # noqa


if __name__ == "__main__":
    asyncio.run(main())
