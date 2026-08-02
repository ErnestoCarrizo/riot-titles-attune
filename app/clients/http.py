import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

import httpx

from app.errors import ExternalTimeoutError, RiotRateLimitError, RiotUnavailableError

logger = logging.getLogger(__name__)


async def request_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    platform: str | None = None,
    source: str = "external",
    retries: int = 2,
) -> httpx.Response:
    for attempt in range(retries + 1):
        started = time.perf_counter()
        try:
            response = await client.request(method, url, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning("external_timeout source=%s platform=%s duration_ms=%d", source, platform, int((time.perf_counter() - started) * 1000))
            if attempt < retries:
                await asyncio.sleep(0.25 * (2**attempt))
                continue
            raise ExternalTimeoutError() from exc
        except httpx.RequestError as exc:
            logger.warning("external_request_error source=%s platform=%s duration_ms=%d", source, platform, int((time.perf_counter() - started) * 1000))
            if attempt < retries:
                await asyncio.sleep(0.25 * (2**attempt))
                continue
            raise RiotUnavailableError() from exc

        logger.info(
            "external_request source=%s platform=%s status=%d duration_ms=%d",
            source,
            platform,
            response.status_code,
            int((time.perf_counter() - started) * 1000),
        )
        if response.status_code == 429:
            if attempt < retries:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 5) if retry_after else 0.25 * (2**attempt)
                except ValueError:
                    delay = 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue
            raise RiotRateLimitError(response.headers.get("Retry-After"))
        if response.status_code >= 500 and attempt < retries:
            await asyncio.sleep(0.25 * (2**attempt))
            continue
        return response
    raise RiotUnavailableError()
