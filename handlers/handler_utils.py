import json
import logging
import os
from contextlib import ContextDecorator
from time import time
from types import TracebackType
from typing import Any, Type

import aiofiles
import httpx

logger = logging.getLogger(__name__)


async def fetch_and_store_credentials(
    url: str,
    headers: dict[str, str],
    params: dict[str, str],
    filename: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, params=params)
    response.raise_for_status()
    credentials: dict[str, Any] = response.json()
    credentials["expires_in"] += int(time())
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(credentials))
        os.chmod(filename, 0o600)
    return credentials


async def create_hh_credentials(hh_uri: str, hh_id: str, hh_code: str, hh_secret: str) -> None:
    url = "https://hh.ru/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = {
        "redirect_uri": hh_uri,
        "client_id": hh_id,
        "client_secret": hh_secret,
        "code": hh_code,
        "grant_type": "authorization_code",
    }
    _ = await fetch_and_store_credentials(url, headers, params, ".hh_credentials.json")


async def refresh_hh_token(refresh_token: str) -> dict[str, Any]:
    logger.info("Refresh API-token for Head Hunter...")
    url = "https://hh.ru/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    credentials: dict[str, Any] = await fetch_and_store_credentials(url, headers, params, ".hh_credentials.json")
    logger.info("Token success updated")
    return credentials


async def get_hh_token() -> tuple[str, int]:
    async with aiofiles.open(".hh_credentials.json", "r", encoding="utf-8") as file:
        credentials = json.loads(await file.read())
    if credentials["expires_in"] < int(time()):
        credentials = await refresh_hh_token(credentials["refresh_token"])
    return credentials["access_token"], credentials["expires_in"]


def predict_rub_salary(salary_from: int, salary_to: int) -> int:
    if salary_from and salary_to:
        return round((salary_from + salary_to) / 2)
    if salary_from:
        return round(salary_from * 1.2)
    if salary_to:
        return round(salary_to * 0.8)
    if not salary_from and not salary_to:
        return 0


class Timer(ContextDecorator):

    def __init__(self, name: str | None = None, log: logging.Logger | None = None):
        self.name = name
        self.logger = log or logging.getLogger()
        self._start_time: float = 0
        self._end_time: float = 0
        self._elapsed_time: float = 0

    def __enter__(self) -> "Timer":
        self._start_time = time()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        result = False
        self._end_time = time()
        self._elapsed_time = self._end_time - self._start_time

        timer_name = f" '{self.name}'" if self.name else ""
        self.logger.info("Elapsed time%s: %.4f sec.", timer_name, self._elapsed_time)

        return result  # Исключения не перехватываются

    @property
    def elapsed(self) -> float | None:
        return self._elapsed_time

    def get_elapsed(self) -> float | None:
        return self._elapsed_time

    def reset(self) -> None:
        self._start_time = 0
        self._end_time = 0
        self._elapsed_time = 0

    @property
    def is_running(self) -> bool:
        return self._start_time is not None and self._elapsed_time is None

    def __str__(self) -> str:
        if self._elapsed_time != 0:
            return f"Timer({self.name or ''}): {self._elapsed_time:.4f}s"
        elif self.is_running:
            return f"Timer({self.name or ''}): running"
        else:
            return f"Timer({self.name or ''}): not started"
