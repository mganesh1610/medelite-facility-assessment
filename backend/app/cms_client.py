from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from fastapi import HTTPException

from .cache import TTLCache
from .settings import settings


class CmsDataset:
    PROVIDER_INFO = "4pq5-n9py"
    CLAIMS_MEASURES = "ijh5-nb2v"
    STATE_US_AVERAGES = "xcdc-v8bm"


class CmsClient:
    base_url = "https://data.cms.gov/provider-data/api/1/datastore/query"

    def __init__(self) -> None:
        self.cache = TTLCache(settings.cms_cache_ttl_seconds)

    async def fetch_provider(self, ccn: str) -> tuple[dict[str, Any] | None, int]:
        rows, request_count = await self._query(
            CmsDataset.PROVIDER_INFO,
            [("cms_certification_number_ccn", "=", ccn)],
            limit=1,
        )
        return (rows[0] if rows else None, request_count)

    async def fetch_claims_metrics(self, ccn: str) -> tuple[list[dict[str, Any]], int]:
        rows, request_count = await self._query(
            CmsDataset.CLAIMS_MEASURES,
            [("cms_certification_number_ccn", "=", ccn)],
            limit=20,
        )
        wanted = {"521", "522", "551", "552"}
        return [row for row in rows if row.get("measure_code") in wanted], request_count

    async def fetch_state_average(self, state: str) -> tuple[dict[str, Any] | None, int]:
        rows, request_count = await self._query(
            CmsDataset.STATE_US_AVERAGES,
            [("state_or_nation", "=", state)],
            limit=1,
        )
        return (rows[0] if rows else None, request_count)

    async def fetch_national_average(self) -> tuple[dict[str, Any] | None, int]:
        rows, request_count = await self._query(
            CmsDataset.STATE_US_AVERAGES,
            [("state_or_nation", "=", "NATION")],
            limit=1,
        )
        return (rows[0] if rows else None, request_count)

    async def _query(
        self,
        dataset_id: str,
        conditions: list[tuple[str, str, str]],
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        params: dict[str, str | int] = {"limit": limit}
        for index, (field, operator, value) in enumerate(conditions):
            params[f"conditions[{index}][property]"] = field
            params[f"conditions[{index}][operator]"] = operator
            params[f"conditions[{index}][value]"] = value

        cache_key = f"{dataset_id}:{params}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, 0

        url = f"{self.base_url}/{dataset_id}/0"
        last_error: Exception | None = None
        request_count = 0
        async with httpx.AsyncClient(timeout=settings.cms_timeout_seconds) as client:
            for attempt in range(4):
                try:
                    request_count += 1
                    response = await client.get(url, params=params)
                    if response.status_code in {429, 500, 502, 503, 504}:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    response.raise_for_status()
                    payload = response.json()
                    rows = payload.get("results", [])
                    self.cache.set(cache_key, rows)
                    return rows, request_count
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc
                    await asyncio.sleep(0.5 * (2**attempt))

        raise HTTPException(
            status_code=502,
            detail=f"CMS Provider Data API request failed after retries: {last_error}",
        )


async def timed_assessment_fetch(ccn: str, client: CmsClient) -> tuple[int, int, dict[str, Any] | None, list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    start = time.perf_counter()
    provider, provider_count = await client.fetch_provider(ccn)
    if not provider:
        return int((time.perf_counter() - start) * 1000), provider_count, None, [], None, None

    state = provider.get("state", "")
    claims_task = client.fetch_claims_metrics(ccn)
    state_task = client.fetch_state_average(state) if state else asyncio.sleep(0, result=(None, 0))
    national_task = client.fetch_national_average()
    (claims, claims_count), (state_avg, state_count), (national_avg, national_count) = await asyncio.gather(claims_task, state_task, national_task)
    latency = int((time.perf_counter() - start) * 1000)
    total_count = provider_count + claims_count + state_count + national_count
    return latency, total_count, provider, claims, state_avg, national_avg
