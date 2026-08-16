from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable

import requests


class ForexProviderError(RuntimeError):
    """Raised when the remote provider cannot return a usable response."""


class ForexDataError(ForexProviderError):
    """Raised when a successful HTTP response violates the data contract."""


@dataclass(frozen=True, slots=True)
class ProviderRate:
    rate_date: date
    base: str
    quote: str
    rate: Decimal


HttpGet = Callable[..., requests.Response]


def fetch_provider_rates(
    *,
    api_base_url: str,
    provider: str,
    base: str,
    quotes: tuple[str, ...],
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
    http_get: HttpGet = requests.get,
) -> tuple[ProviderRate, ...]:
    """Fetch and validate one complete set of daily reference rates."""
    normalized_base = base.upper()
    expected_quotes = {quote.upper() for quote in quotes}

    try:
        response = http_get(
            f"{api_base_url.rstrip('/')}/rates",
            params={
                "base": normalized_base,
                "quotes": ",".join(sorted(expected_quotes)),
                "providers": provider,
            },
            headers={
                "Accept": "application/json",
                "User-Agent": "MoneyTiq/1.0 forex-rate-client",
            },
            timeout=(connect_timeout_seconds, read_timeout_seconds),
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise ForexProviderError("Forex provider request failed") from error

    content_type = response.headers.get("Content-Type", "").lower()
    if "application/json" not in content_type:
        raise ForexDataError("Forex provider returned a non-JSON response")

    try:
        payload = response.json(parse_float=Decimal)
    except (ValueError, TypeError) as error:
        raise ForexDataError("Forex provider returned invalid JSON") from error

    if not isinstance(payload, list):
        raise ForexDataError("Forex provider response must be a list")

    parsed_rates: dict[str, ProviderRate] = {}
    observed_dates: set[date] = set()

    for row in payload:
        if not isinstance(row, dict):
            raise ForexDataError("Forex provider row must be an object")

        required_fields = {"date", "base", "quote", "rate"}
        if not required_fields.issubset(row):
            raise ForexDataError("Forex provider row is missing required fields")

        row_base = str(row["base"]).upper()
        row_quote = str(row["quote"]).upper()

        if row_base != normalized_base or row_quote not in expected_quotes:
            raise ForexDataError("Forex provider returned an unexpected currency pair")
        if row_quote in parsed_rates:
            raise ForexDataError("Forex provider returned a duplicate currency pair")

        try:
            rate_date = date.fromisoformat(str(row["date"]))
            rate = Decimal(str(row["rate"]))
        except (ValueError, InvalidOperation) as error:
            raise ForexDataError("Forex provider returned an invalid date or rate") from error

        if not rate.is_finite() or rate <= 0:
            raise ForexDataError("Forex provider rate must be finite and positive")

        observed_dates.add(rate_date)
        parsed_rates[row_quote] = ProviderRate(
            rate_date=rate_date,
            base=row_base,
            quote=row_quote,
            rate=rate,
        )

    missing_quotes = expected_quotes - parsed_rates.keys()
    if missing_quotes:
        raise ForexDataError(
            f"Forex provider omitted required currencies: {sorted(missing_quotes)}"
        )
    if len(observed_dates) != 1:
        raise ForexDataError("Forex provider returned rates from different dates")

    return tuple(parsed_rates[quote] for quote in sorted(parsed_rates))
