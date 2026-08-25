from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable

from flask import current_app
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models.nse_market_cache import NseMarketCache
from app.services.nse_client import (
    NseProviderError,
    ProviderPayload,
    fetch_nse_stock,
    fetch_nse_stocks,
    normalize_symbol,
)


class NseUnavailableError(RuntimeError):
    """Raised when neither the provider nor last-known-good data is available."""


@dataclass(frozen=True, slots=True)
class NseMarketResult:
    payload: dict | list
    source_updated_at: datetime | None
    fetched_at: datetime
    stale: bool


Fetcher = Callable[..., ProviderPayload]


def _read_cache(cache_key: str) -> NseMarketCache | None:
    return db.session.scalar(
        select(NseMarketCache).where(NseMarketCache.cache_key == cache_key)
    )


def _store_cache(
    cache_key: str,
    provider_payload: ProviderPayload,
    fetched_at: datetime,
) -> None:
    statement = insert(NseMarketCache).values(
        cache_key=cache_key,
        payload=provider_payload.payload,
        source_updated_at=provider_payload.source_updated_at,
        fetched_at=fetched_at,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[NseMarketCache.cache_key],
        set_={
            "payload": statement.excluded.payload,
            "source_updated_at": statement.excluded.source_updated_at,
            "fetched_at": statement.excluded.fetched_at,
        },
    )
    try:
        db.session.execute(statement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _resolve(
    cache_key: str,
    *,
    fetcher: Fetcher,
    fetch_kwargs: dict,
    now: datetime,
) -> NseMarketResult:
    cached = _read_cache(cache_key)
    cache_ttl = timedelta(seconds=current_app.config["NSE_CACHE_TTL_SECONDS"])

    if cached is not None and now - cached.fetched_at <= cache_ttl:
        return NseMarketResult(
            payload=cached.payload,
            source_updated_at=cached.source_updated_at,
            fetched_at=cached.fetched_at,
            stale=False,
        )

    # End the read transaction before waiting on an external network call.
    db.session.rollback()

    try:
        provider_payload = fetcher(**fetch_kwargs)
    except NseProviderError as error:
        current_app.logger.warning(
            "nse_provider_unavailable cache_key=%s cached=%s error_type=%s",
            cache_key,
            cached is not None,
            type(error).__name__,
        )
        if cached is not None:
            return NseMarketResult(
                payload=cached.payload,
                source_updated_at=cached.source_updated_at,
                fetched_at=cached.fetched_at,
                stale=True,
            )
        raise NseUnavailableError("NSE market data is temporarily unavailable") from error

    _store_cache(cache_key, provider_payload, now)
    return NseMarketResult(
        payload=provider_payload.payload,
        source_updated_at=provider_payload.source_updated_at,
        fetched_at=now,
        stale=False,
    )


def get_nse_stocks(
    *,
    fetcher: Fetcher = fetch_nse_stocks,
    now: datetime | None = None,
) -> NseMarketResult:
    return _resolve(
        "market:list",
        fetcher=fetcher,
        fetch_kwargs={
            "api_base_url": current_app.config["NSE_API_BASE_URL"],
            "minimum_stock_count": current_app.config["NSE_MIN_STOCK_COUNT"],
            "connect_timeout_seconds": current_app.config[
                "NSE_CONNECT_TIMEOUT_SECONDS"
            ],
            "read_timeout_seconds": current_app.config["NSE_READ_TIMEOUT_SECONDS"],
        },
        now=now or datetime.now(UTC),
    )


def get_nse_stock(
    symbol: str,
    *,
    fetcher: Fetcher = fetch_nse_stock,
    now: datetime | None = None,
) -> NseMarketResult:
    normalized_symbol = normalize_symbol(symbol)
    return _resolve(
        f"stock:{normalized_symbol.removesuffix('.KE')}",
        fetcher=fetcher,
        fetch_kwargs={
            "symbol": normalized_symbol,
            "api_base_url": current_app.config["NSE_API_BASE_URL"],
            "connect_timeout_seconds": current_app.config[
                "NSE_CONNECT_TIMEOUT_SECONDS"
            ],
            "read_timeout_seconds": current_app.config["NSE_READ_TIMEOUT_SECONDS"],
        },
        now=now or datetime.now(UTC),
    )
