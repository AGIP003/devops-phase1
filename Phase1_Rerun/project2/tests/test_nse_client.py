from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.nse_client import (
    NseDataError,
    fetch_nse_stock,
    fetch_nse_stocks,
    normalize_symbol,
)


pytestmark = pytest.mark.no_database


class FakeResponse:
    def __init__(self, payload, content_type="application/json"):
        self.payload = payload
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        return None

    def json(self, **kwargs):
        return self.payload


def stock_row(symbol="SCOM.KE", name="Safaricom PLC"):
    return {
        "symbol": symbol,
        "name": name,
        "price": Decimal("37.25"),
        "openPrice": Decimal("36.60"),
        "change": Decimal("1.776"),
        "currency": "KES",
        "exchange": "NSE",
        "sector": "Telecommunications",
        "assetType": "STOCK",
        "listingStatus": "ACTIVE",
        "tradingEnabled": True,
        "isTradeable": True,
        "previousClose": Decimal("37.25"),
        "lastPriceUpdate": "2026-08-25T16:45:15.481Z",
    }


def test_market_client_validates_unique_nse_rows_and_preserves_decimal_strings():
    request_details = {}

    def fake_get(url, **kwargs):
        request_details.update({"url": url, **kwargs})
        return FakeResponse([
            stock_row(),
            stock_row("KCB.KE", "KCB Group PLC"),
        ])

    result = fetch_nse_stocks(
        api_base_url="https://licensed.example/api/v1",
        minimum_stock_count=2,
        connect_timeout_seconds=3,
        read_timeout_seconds=12,
        http_get=fake_get,
    )

    assert len(result.payload) == 2
    assert result.payload[1]["price"] == "37.25"
    assert result.payload[1]["changePercent"] == "1.776"
    assert result.source_updated_at == datetime(
        2026,
        8,
        25,
        16,
        45,
        15,
        481000,
        tzinfo=UTC,
    )
    assert request_details["params"] == {"exchange": "NSE"}
    assert request_details["timeout"] == (3, 12)


def test_market_client_rejects_incomplete_or_duplicate_market_data():
    with pytest.raises(NseDataError, match="incomplete"):
        fetch_nse_stocks(
            api_base_url="https://licensed.example/api/v1",
            minimum_stock_count=2,
            connect_timeout_seconds=3,
            read_timeout_seconds=12,
            http_get=lambda *args, **kwargs: FakeResponse([stock_row()]),
        )

    with pytest.raises(NseDataError, match="duplicate"):
        fetch_nse_stocks(
            api_base_url="https://licensed.example/api/v1",
            minimum_stock_count=2,
            connect_timeout_seconds=3,
            read_timeout_seconds=12,
            http_get=lambda *args, **kwargs: FakeResponse([
                stock_row(),
                stock_row(),
            ]),
        )


def test_company_client_preserves_unavailable_ratios_instead_of_inventing_zero():
    detail = {
        **stock_row(),
        "description": "A listed telecommunications company.",
        "website": 'https://www.safaricom.co.ke/ "www.safaricom.co.ke"',
        "marketCap": Decimal("1490000000000"),
        "peRatio": None,
        "eps": None,
        "dividendYield": None,
        "dividendPerShare": None,
        "dayLow": Decimal("36.5"),
        "dayHigh": Decimal("37.5"),
        "volume": Decimal("1250000"),
        "priceHistory": [
            {"date": "2026-08-24", "price": Decimal("36.60")},
            {"date": "2026-08-25", "price": Decimal("37.25")},
        ],
        "tradingViewPerformanceReturns": {
            "perf1m": Decimal("5.4"),
            "perfytd": Decimal("20.6"),
        },
    }

    result = fetch_nse_stock(
        "scom",
        api_base_url="https://licensed.example/api/v1",
        connect_timeout_seconds=3,
        read_timeout_seconds=12,
        http_get=lambda *args, **kwargs: FakeResponse(detail),
    )

    assert result.payload["symbol"] == "SCOM.KE"
    assert result.payload["website"] == "https://www.safaricom.co.ke/"
    assert result.payload["peRatio"] is None
    assert result.payload["eps"] is None
    assert result.payload["performance"]["1M"] == "5.4"
    assert result.payload["priceHistory"][1]["price"] == "37.25"


def test_symbol_validation_accepts_ticker_or_provider_symbol_only():
    assert normalize_symbol("scom") == "SCOM.KE"
    assert normalize_symbol("KCB.KE") == "KCB.KE"
    with pytest.raises(NseDataError):
        normalize_symbol("../../secrets")
