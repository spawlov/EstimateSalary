import json
import os
from time import time
from typing import Any

import aiofiles
import httpx


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
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, params=params)
    response.raise_for_status()
    credentials = response.json()
    credentials["expires_in"] += int(time())
    async with aiofiles.open(".hh_credentials.json", "w", encoding="utf-8") as file:
        await file.write(json.dumps(credentials))
        os.chmod(".hh_credentials.json", 0o600)


async def refresh_hh_token(refresh_token: str) -> dict[str, Any]:
    url = "https://hh.ru/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, params=params)
    response.raise_for_status()
    credentials = response.json()
    credentials["expires_in"] += int(time())
    async with aiofiles.open(".hh_credentials.json", "w", encoding="utf-8") as file:
        await file.write(json.dumps(credentials))
        os.chmod(".hh_credentials.json", 0o600)
    return credentials


async def get_hh_token() -> tuple[str, int]:
    async with aiofiles.open(".hh_credentials.json", "r", encoding="utf-8") as file:
        credentials = json.loads(await file.read())
    if credentials["expires_in"] < int(time()):
        credentials = await refresh_hh_token(credentials["refresh_token"])
    return credentials["access_token"], credentials["expires_in"]


async def predict_rub_salary(salary_from: int, salary_to: int) -> int:
    if salary_from and salary_to:
        return round((salary_from + salary_to) / 2)
    if salary_from:
        return round(salary_from * 1.2)
    if salary_to:
        return round(salary_to * 0.8)
    if not salary_from and not salary_to:
        return 0
