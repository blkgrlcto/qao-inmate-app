"""CourtListener API v4 client for federal PACER/RECAP docket search."""
import asyncio
import time
from typing import Any

import httpx

from app.core.config import get_settings


class RateLimiter:
    """Simple token bucket style rate limiter."""

    def __init__(self, rps: float):
        self.min_interval = 1.0 / rps if rps > 0 else 0
        self.last_call = 0.0

    async def acquire(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_call = time.monotonic()


async def search_pacer_dockets(
    query: str,
    cursor: str | None = None,
    page_size: int = 20,
) -> dict[str, Any]:
    """
    Search federal dockets via CourtListener v4.
    type=r returns federal dockets with nested recap_documents (up to 3).
    """
    settings = get_settings()
    rate_limiter = RateLimiter(settings.COURTLISTENER_RATE_LIMIT_RPS)

    base = settings.COURTLISTENER_BASE_URL.rstrip("/")
    url = f"{base}/api/rest/v4/search/"

    params: dict[str, str | int] = {
        "type": "r",
        "q": query,
        "page_size": min(page_size, 100),
    }
    if cursor:
        params["cursor"] = cursor

    headers: dict[str, str] = {}
    if settings.COURTLISTENER_API_TOKEN:
        headers["Authorization"] = f"Token {settings.COURTLISTENER_API_TOKEN}"

    transport = httpx.AsyncHTTPTransport(retries=3)
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
        await rate_limiter.acquire()
        response = await client.get(url, params=params, headers=headers or None)
        response.raise_for_status()
        return response.json()
