from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Callable

from flask import current_app
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models.forex_rate import ForexRate
from app.services.forex_client import (
    ForexProviderError,
    ProviderRate,
    fetch_provider_rates,
)


SUPPORTED_QUOTES = (
    "AED",
    "AUD",
    "BIF",
    "CAD",
    "CHF",
    "CNY",
    "DKK",
    "EUR",
    "GBP",
    "HKD",
    "INR",
    "JPY",
    "NOK",
    "RWF",
    "SAR",
    "SEK",
    "SGD",
    "TZS",
    "UGX",
    "USD",
    "ZAR",
)


class ForexUnavailableError(RuntimeError):
    """Raised when neither the provider nor the local cache can serve rates."""


@dataclass(frozen=True, slots=True)
class ForexRatesResult:
    provider: str
    base: str
    rate_date: date
    fetched_at: datetime
    rates: dict[str, Decimal]
    stale: bool


Fetcher = Callable[..., tuple[ProviderRate, ...]]


def _read_complete_cache(provider: str, base: str) -> ForexRatesResult | None:
    latest_date = db.session.scalar(
        select(func.max(ForexRate.rate_date)).where(
            ForexRate.provider == provider,
            ForexRate.base_currency == base,
        )
    )
    if latest_date is None:
        return None

    rows = list(
        db.session.scalars(
            select(ForexRate).where(
                ForexRate.provider == provider,
                ForexRate.base_currency == base,
                ForexRate.rate_date == latest_date,
            )
        ).all()
    )
    rates = {row.quote_currency: row.rate for row in rows}

    if set(rates) != set(SUPPORTED_QUOTES):
        return None

    return ForexRatesResult(
        provider=provider,
        base=base,
        rate_date=latest_date,
        fetched_at=min(row.fetched_at for row in rows),
        rates=rates,
        stale=False,
    )


def _store_rates(
    provider: str,
    rates: tuple[ProviderRate, ...],
    fetched_at: datetime,
) -> None:
    values = [
        {
            "provider": provider,
            "base_currency": rate.base,
            "quote_currency": rate.quote,
            "rate": rate.rate,
            "rate_date": rate.rate_date,
            "fetched_at": fetched_at,
        }
        for rate in rates
    ]
    statement = insert(ForexRate).values(values)
    statement = statement.on_conflict_do_update(
        constraint="uq_forex_rates_provider_pair_date",
        set_={
            "rate": statement.excluded.rate,
            "fetched_at": statement.excluded.fetched_at,
        },
    )

    try:
        db.session.execute(statement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def get_current_forex_rates(
    *,
    fetcher: Fetcher = fetch_provider_rates,
    now: datetime | None = None,
) -> ForexRatesResult:
    """Return current rates or degrade to a validated last-known-good set."""
    current_time = now or datetime.now(UTC)
    provider = current_app.config["FOREX_PROVIDER"]
    base = "KES"
    cache_ttl = timedelta(
        seconds=current_app.config["FOREX_CACHE_TTL_SECONDS"]
    )

    cached = _read_complete_cache(provider, base)
    # End the read transaction before a potentially slow network request.
    db.session.rollback()

    if cached is not None and current_time - cached.fetched_at <= cache_ttl:
        return cached

    try:
        provider_rates = fetcher(
            api_base_url=current_app.config["FOREX_API_BASE_URL"],
            provider=provider,
            base=base,
            quotes=SUPPORTED_QUOTES,
            connect_timeout_seconds=current_app.config[
                "FOREX_CONNECT_TIMEOUT_SECONDS"
            ],
            read_timeout_seconds=current_app.config[
                "FOREX_READ_TIMEOUT_SECONDS"
            ],
        )
    except ForexProviderError as error:
        if cached is not None:
            return ForexRatesResult(
                provider=cached.provider,
                base=cached.base,
                rate_date=cached.rate_date,
                fetched_at=cached.fetched_at,
                rates=cached.rates,
                stale=True,
            )
        raise ForexUnavailableError("Forex rates are temporarily unavailable") from error

    _store_rates(provider, provider_rates, current_time)

    return ForexRatesResult(
        provider=provider,
        base=base,
        rate_date=provider_rates[0].rate_date,
        fetched_at=current_time,
        rates={rate.quote: rate.rate for rate in provider_rates},
        stale=False,
    )
