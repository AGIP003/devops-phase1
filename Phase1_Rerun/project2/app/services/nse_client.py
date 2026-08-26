from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Callable

import requests


class NseProviderError(RuntimeError):
    """Raised when the licensed market-data provider cannot be reached."""


class NseDataError(NseProviderError):
    """Raised when a provider response violates the expected data contract."""


@dataclass(frozen=True, slots=True)
class ProviderPayload:
    payload: dict | list
    source_updated_at: datetime | None


HttpGet = Callable[..., requests.Response]
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{1,12}(?:\.KE)?$")
URL_PATTERN = re.compile(r"https?://[^\s\"']+", re.IGNORECASE)
NSE_QUOTE_CURRENCIES = {"KES", "USD"}


def normalize_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise NseDataError("Invalid NSE security symbol")
    return normalized if normalized.endswith(".KE") else f"{normalized}.KE"


def _request_json(
    url: str,
    *,
    params: dict | None,
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
    http_get: HttpGet,
):
    try:
        response = http_get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "MoneyTiq/1.0 licensed-nse-market-client",
            },
            timeout=(connect_timeout_seconds, read_timeout_seconds),
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise NseProviderError("NSE market provider request failed") from error

    content_type = response.headers.get("Content-Type", "").lower()
    if "application/json" not in content_type:
        raise NseDataError("NSE market provider returned a non-JSON response")

    try:
        return response.json(parse_float=Decimal)
    except (ValueError, TypeError) as error:
        raise NseDataError("NSE market provider returned invalid JSON") from error


def _text(value, field: str, *, required=True, maximum=5000) -> str | None:
    if value is None:
        if required:
            raise NseDataError(f"NSE provider omitted {field}")
        return None
    cleaned = " ".join(str(value).strip().split())
    if required and not cleaned:
        raise NseDataError(f"NSE provider returned an empty {field}")
    return cleaned[:maximum] or None


def _decimal(value, field: str, *, required=False) -> str | None:
    if value is None or value == "":
        if required:
            raise NseDataError(f"NSE provider omitted {field}")
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise NseDataError(f"NSE provider returned an invalid {field}") from error
    if not number.is_finite() or number < 0:
        raise NseDataError(f"NSE provider returned an invalid {field}")
    return format(number, "f")


def _signed_decimal(value, field: str) -> str | None:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise NseDataError(f"NSE provider returned an invalid {field}") from error
    if not number.is_finite():
        raise NseDataError(f"NSE provider returned an invalid {field}")
    return format(number, "f")


def _timestamp(value, field: str, *, required=False) -> datetime | None:
    if value in (None, ""):
        if required:
            raise NseDataError(f"NSE provider omitted {field}")
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as error:
        raise NseDataError(f"NSE provider returned an invalid {field}") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_url(value) -> str | None:
    if not value:
        return None
    match = URL_PATTERN.search(str(value))
    return match.group(0).rstrip(".,)") if match else None


def _normalize_summary(row: dict) -> tuple[dict, datetime | None]:
    if not isinstance(row, dict):
        raise NseDataError("NSE provider stock row must be an object")

    symbol = normalize_symbol(_text(row.get("symbol"), "symbol", maximum=15))
    exchange = _text(row.get("exchange"), "exchange", maximum=12).upper()
    currency = _text(row.get("currency"), "currency", maximum=3).upper()
    if exchange != "NSE" or currency not in NSE_QUOTE_CURRENCIES:
        raise NseDataError("NSE provider returned an unexpected market or currency")

    updated_at = _timestamp(row.get("lastPriceUpdate"), "lastPriceUpdate")
    return {
        "symbol": symbol,
        "ticker": symbol.removesuffix(".KE"),
        "name": _text(row.get("name"), "name", maximum=180),
        "price": _decimal(row.get("price"), "price", required=True),
        "openPrice": _decimal(row.get("openPrice"), "openPrice"),
        "previousClose": _decimal(row.get("previousClose"), "previousClose"),
        "changePercent": _signed_decimal(row.get("change"), "change"),
        "currency": currency,
        "exchange": exchange,
        "sector": _text(row.get("sector"), "sector", required=False, maximum=100)
        or "Unclassified",
        "assetType": _text(row.get("assetType"), "assetType", required=False, maximum=32),
        "listingStatus": _text(
            row.get("listingStatus"),
            "listingStatus",
            required=False,
            maximum=32,
        ),
        "tradingEnabled": bool(row.get("tradingEnabled")),
        "isTradeable": bool(row.get("isTradeable")),
        "lastPriceUpdate": updated_at.isoformat() if updated_at else None,
    }, updated_at


def fetch_nse_stocks(
    *,
    api_base_url: str,
    minimum_stock_count: int,
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
    http_get: HttpGet = requests.get,
) -> ProviderPayload:
    """Fetch and validate the full NSE security list at one-security-per-row grain."""
    payload = _request_json(
        f"{api_base_url.rstrip('/')}/stocks",
        params={"exchange": "NSE"},
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
        http_get=http_get,
    )
    if not isinstance(payload, list):
        raise NseDataError("NSE provider stock response must be a list")
    if len(payload) < minimum_stock_count:
        raise NseDataError("NSE provider returned an unexpectedly incomplete market list")

    stocks = []
    timestamps = []
    seen_symbols = set()
    for row in payload:
        stock, updated_at = _normalize_summary(row)
        if stock["symbol"] in seen_symbols:
            raise NseDataError("NSE provider returned a duplicate security symbol")
        seen_symbols.add(stock["symbol"])
        stocks.append(stock)
        if updated_at:
            timestamps.append(updated_at)

    stocks.sort(key=lambda stock: stock["ticker"])
    return ProviderPayload(
        payload=stocks,
        source_updated_at=max(timestamps) if timestamps else None,
    )


def _normalize_history(value) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise NseDataError("NSE provider price history must be a list")

    history = []
    for row in value[-500:]:
        if not isinstance(row, dict):
            continue
        observed_at = row.get("date") or row.get("timestamp") or row.get("time")
        price = row.get("price") or row.get("close") or row.get("value")
        if observed_at in (None, "") or price in (None, ""):
            continue
        try:
            parsed_price = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if not parsed_price.is_finite() or parsed_price < 0:
            continue
        history.append({"date": str(observed_at), "price": format(parsed_price, "f")})
    return history


def fetch_nse_stock(
    symbol: str,
    *,
    api_base_url: str,
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
    http_get: HttpGet = requests.get,
) -> ProviderPayload:
    """Fetch and validate the provider's detailed company/security record."""
    normalized_symbol = normalize_symbol(symbol)
    row = _request_json(
        f"{api_base_url.rstrip('/')}/stocks/{normalized_symbol}",
        params=None,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
        http_get=http_get,
    )
    summary, updated_at = _normalize_summary(row)
    if summary["symbol"] != normalized_symbol:
        raise NseDataError("NSE provider returned the wrong security")

    performance_source = row.get("tradingViewPerformanceReturns") or {}
    if not isinstance(performance_source, dict):
        raise NseDataError("NSE provider performance returns must be an object")
    performance = {
        period: _signed_decimal(performance_source.get(provider_key), provider_key)
        for period, provider_key in {
            "1D": "perf1d",
            "5D": "perf5d",
            "1M": "perf1m",
            "3M": "perf3m",
            "6M": "perf6m",
            "YTD": "perfytd",
            "1Y": "perf1y",
            "3Y": "perf3y",
            "5Y": "perf5y",
            "10Y": "perf10y",
            "MAX": "perfAll",
        }.items()
    }

    detail = {
        **summary,
        "description": _text(
            row.get("description"),
            "description",
            required=False,
            maximum=5000,
        ),
        "industry": _text(row.get("industry"), "industry", required=False, maximum=120),
        "isin": _text(row.get("isin"), "isin", required=False, maximum=32),
        "website": _safe_url(row.get("website")),
        "marketCap": _decimal(row.get("marketCap"), "marketCap"),
        "peRatio": _signed_decimal(row.get("peRatio"), "peRatio"),
        "eps": _signed_decimal(row.get("eps"), "eps"),
        "dividendPerShare": _decimal(row.get("dividendPerShare"), "dividendPerShare"),
        "dividendYield": _decimal(row.get("dividendYield"), "dividendYield"),
        "sharesOutstanding": _decimal(row.get("sharesOutstanding"), "sharesOutstanding"),
        "dayLow": _decimal(row.get("dayLow"), "dayLow"),
        "dayHigh": _decimal(row.get("dayHigh"), "dayHigh"),
        "volume": _decimal(row.get("volume"), "volume"),
        "quoteConfidence": _text(
            row.get("quoteConfidence"),
            "quoteConfidence",
            required=False,
            maximum=40,
        ),
        "eodStatus": _text(row.get("eodStatus"), "eodStatus", required=False, maximum=40),
        "priceAsOf": _text(row.get("priceAsOf"), "priceAsOf", required=False, maximum=60),
        "lastAuthoritativeSessionDate": _text(
            row.get("lastAuthoritativeSessionDate"),
            "lastAuthoritativeSessionDate",
            required=False,
            maximum=32,
        ),
        "priceHistory": _normalize_history(row.get("priceHistory")),
        "performance": performance,
    }
    return ProviderPayload(payload=detail, source_updated_at=updated_at)
