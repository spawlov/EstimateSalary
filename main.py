import logging
import os
from time import time

from dotenv import find_dotenv, load_dotenv

from handlers import get_stats_from_hh

from icecream import ic


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv(find_dotenv())
    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler("main.log", encoding="utf-8")
    log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(log_handler)

    languages = os.getenv("LANGS", "JavaScript, Java, Python").split(",")

    city = os.getenv("CITY", None)

    days_ago = int(os.getenv("DAYS", 7))

    logger.info("Starting process for HH...")
    t0 = time()
    ic(get_stats_from_hh(languages=languages, city=city, days_ago=days_ago))
    logger.info(f"Time to process HH: {time() - t0:.4f}sec.")


if __name__ == "__main__":
    main()
