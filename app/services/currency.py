from __future__ import annotations
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Dict
import httpx

from app.core.config import settings
from app.middlewares.error_handler import AppError
from app.core.logging import log

SUPPORTED = set(settings.SUPPORTED_CURRENCIES)


@dataclass
class CacheEntry:
    as_of: datetime
    rates: Dict[str, Decimal]  # target -> rate


class CurrencyService:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get_rate(self, base: str, target: str) -> Decimal:
        base = base.upper()
        target = target.upper()

        log.debug("currency.get_rate.request", base=base, target=target)

        if base not in SUPPORTED or target not in SUPPORTED:

            log.warning(
                "currency.unsupported",
                base=base,
                target=target,
                supported=list(SUPPORTED),
            )

            raise AppError(
                "CURRENCY_UNSUPPORTED",
                f"Only {sorted(SUPPORTED)} are supported",
                status_code=400,
            )
        if base == target:
            log.debug("currency.same_base_target", currency=base)
            return Decimal("1")

        async with self._lock:
            entry = self._cache.get(base)
            now = datetime.now(timezone.utc)
            if (
                entry
                and (now - entry.as_of).total_seconds() <= settings.CACHE_TTL_SECONDS
            ):
                rate = entry.rates.get(target)
                if rate:
                    log.info(
                        "currency.cache.hit", base=base, target=target, rate=str(rate)
                    )
                    return rate
                else:
                    log.debug("currency.cache.miss_target", base=base, target=target)

        # Fetch fresh
        try:
            url = settings.CURRENCY_API_BASE_URL
            params = {
                "base_currency": base,
                "currencies": target,
                "apikey": settings.CURRENCY_API_KEY,
            }
            rate: Decimal | None = None
            backoffs = [1, 2, 3][: settings.HTTP_RETRIES]
            for attempt, wait in enumerate(backoffs, start=1):

                log.info(
                    "currency.fetch.attempt",
                    attempt=attempt,
                    base=base,
                    target=target,
                    url=url,
                )

                resp = await self._client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # currencyapi.com typical payload: { "data": { "BRL": { "code": "BRL", "value": 5.25 } } }
                    value = data.get("data", {}).get(target, {}).get("value")
                    if value is None:
                        log.error(
                            "currency.fetch.malformed_response",
                            base=base,
                            target=target,
                            response=data,
                        )
                        raise AppError(
                            "UPSTREAM_MALFORMED",
                            "Rate not found in provider response",
                            status_code=502,
                        )
                    rate = Decimal(str(value)).quantize(
                        Decimal("1e-10"), rounding=ROUND_HALF_EVEN
                    )
                    log.info(
                        "currency.fetch.success",
                        base=base,
                        target=target,
                        rate=str(rate),
                    )
                    break
                elif 400 <= resp.status_code < 500:
                    # Provider client error — treat as failed dependency
                    log.error(
                        "currency.fetch.client_error",
                        base=base,
                        target=target,
                        status=resp.status_code,
                        body=resp.text,
                    )
                    raise AppError(
                        "UPSTREAM_4XX",
                        f"Provider error {resp.status_code}",
                        status_code=502,
                    )

                log.warning("currency.fetch.retrying", attempt=attempt, wait=wait)
                await asyncio.sleep(wait)
            if rate is None:
                log.error("currency.fetch.failed", base=base, target=target)
                raise AppError(
                    "UPSTREAM_UNAVAILABLE", "Failed to fetch rates", status_code=504
                )
            # Update cache
            async with self._lock:
                entry = self._cache.get(base)
                if (
                    entry
                    and (datetime.now(timezone.utc) - entry.as_of).total_seconds()
                    <= settings.CACHE_TTL_SECONDS
                ):
                    entry.rates[target] = rate
                else:
                    self._cache[base] = CacheEntry(
                        as_of=datetime.now(timezone.utc), rates={target: rate}
                    )
                    log.debug(
                        "currency.cache.updated",
                        base=base,
                        target=target,
                        rate=str(rate),
                    )

            return rate
        except AppError as e:
            log.error("currency.fetch.error", base=base, target=target, error=str(e))
            # Try stale-if-error
            async with self._lock:
                entry = self._cache.get(base)
            if (
                entry
                and (datetime.now(timezone.utc) - entry.as_of).total_seconds()
                <= settings.STALE_IF_ERROR_SECONDS
            ):
                stale_rate = entry.rates.get(target)
                if stale_rate:
                    log.warning(
                        "currency.stale_fallback",
                        base=base,
                        target=target,
                        rate=str(stale_rate),
                    )
                    return stale_rate
            raise

    @staticmethod
    def quantize_for_display(value: Decimal, currency: str) -> Decimal:
        # Store snapshot at 10 decimals; display as per currency (JPY=0, others=2)
        places = 0 if currency.upper() == "JPY" else 2
        q = Decimal(1).scaleb(-places)  # e.g., Decimal('0.01')
        return value.quantize(q, rounding=ROUND_HALF_EVEN)


currency_service = CurrencyService()
