import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models.forex_rate import ForexRate
from app.services.forex_client import (
    ForexDataError,
    ForexProviderError,
    ProviderRate,
    fetch_provider_rates,
)
from app.services.forex_service import (
    ForexRatesResult,
    ForexUnavailableError,
    SUPPORTED_QUOTES,
    get_current_forex_rates,
)


QUOTES = SUPPORTED_QUOTES
RATE_VALUES = {
    "AED": Decimal("0.02843"),
    "AUD": Decimal("0.01095"),
    "BIF": Decimal("23.13"),
    "CAD": Decimal("0.01077"),
    "CHF": Decimal("0.00629"),
    "CNY": Decimal("0.05219"),
    "DKK": Decimal("0.05013"),
    "EUR": Decimal("0.0067"),
    "GBP": Decimal("0.00573"),
    "HKD": Decimal("0.06072"),
    "INR": Decimal("0.74074"),
    "JPY": Decimal("1.2327"),
    "NOK": Decimal("0.07348"),
    "RWF": Decimal("11.36"),
    "SAR": Decimal("0.02905"),
    "SEK": Decimal("0.07391"),
    "SGD": Decimal("0.0099"),
    "TZS": Decimal("20.46"),
    "UGX": Decimal("28.7"),
    "USD": Decimal("0.00774"),
    "ZAR": Decimal("0.12531"),
}


class FakeResponse:
    def __init__(self, payload, content_type="application/json"):
        self._body = json.dumps(payload)
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        return None

    def json(self, **kwargs):
        return json.loads(self._body, **kwargs)


def provider_rates(rate_date=date(2026, 8, 14)):
    return tuple(
        ProviderRate(
            rate_date=rate_date,
            base="KES",
            quote=quote,
            rate=RATE_VALUES[quote],
        )
        for quote in QUOTES
    )


def test_provider_client_validates_and_parses_decimal_rates():
    payload = [
        {
            "date": "2026-08-14",
            "base": "KES",
            "quote": quote,
            "rate": float(RATE_VALUES[quote]),
        }
        for quote in QUOTES
    ]
    request_details = {}

    def fake_get(url, **kwargs):
        request_details.update({"url": url, **kwargs})
        return FakeResponse(payload)

    rates = fetch_provider_rates(
        api_base_url="https://example.test/v2",
        provider="CBK",
        base="KES",
        quotes=QUOTES,
        connect_timeout_seconds=3,
        read_timeout_seconds=10,
        http_get=fake_get,
    )

    usd_rate = next(rate for rate in rates if rate.quote == "USD")
    assert usd_rate.rate == Decimal("0.00774")
    assert isinstance(usd_rate.rate, Decimal)
    assert request_details["params"]["providers"] == "CBK"
    assert request_details["timeout"] == (3, 10)


def test_provider_client_rejects_html_before_parsing():
    def fake_get(url, **kwargs):
        return FakeResponse(
            "<html>security challenge</html>",
            content_type="text/html",
        )

    with pytest.raises(ForexDataError, match="non-JSON"):
        fetch_provider_rates(
            api_base_url="https://example.test/v2",
            provider="CBK",
            base="KES",
            quotes=QUOTES,
            connect_timeout_seconds=3,
            read_timeout_seconds=10,
            http_get=fake_get,
        )


def test_validated_rates_are_persisted_and_fresh_cache_avoids_network(app):
    now = datetime(2026, 8, 16, 10, tzinfo=UTC)
    calls = {"count": 0}

    def successful_fetcher(**kwargs):
        calls["count"] += 1
        return provider_rates()

    with app.app_context():
        first = get_current_forex_rates(fetcher=successful_fetcher, now=now)
        second = get_current_forex_rates(
            fetcher=successful_fetcher,
            now=now + timedelta(minutes=5),
        )
        stored_count = db.session.scalar(select(func.count(ForexRate.id)))

    assert first.stale is False
    assert second.stale is False
    assert second.rates["USD"] == Decimal("0.007740000000")
    assert stored_count == len(QUOTES)
    assert calls["count"] == 1


def test_provider_failure_serves_stale_last_known_good(app):
    fetched_at = datetime(2026, 8, 15, 1, tzinfo=UTC)

    with app.app_context():
        db.session.add_all([
            ForexRate(
                provider="CBK",
                base_currency="KES",
                quote_currency=quote,
                rate=RATE_VALUES[quote],
                rate_date=date(2026, 8, 14),
                fetched_at=fetched_at,
            )
            for quote in QUOTES
        ])
        db.session.commit()

        def failing_fetcher(**kwargs):
            raise ForexProviderError("provider timed out")

        result = get_current_forex_rates(
            fetcher=failing_fetcher,
            now=fetched_at + timedelta(days=1),
        )

    assert result.stale is True
    assert result.rate_date == date(2026, 8, 14)
    assert result.rates["UGX"] == Decimal("28.700000000000")


def test_provider_failure_without_cache_is_unavailable(app):
    def failing_fetcher(**kwargs):
        raise ForexProviderError("provider timed out")

    with app.app_context(), pytest.raises(ForexUnavailableError):
        get_current_forex_rates(fetcher=failing_fetcher)


def test_forex_route_requires_authentication_and_serializes_rates(
    client,
    register_user,
    monkeypatch,
):
    unauthorized = client.get("/api/forex/rates")
    assert unauthorized.status_code == 401

    owner = register_user("forex_owner", "forex-owner@example.com")
    result = ForexRatesResult(
        provider="CBK",
        base="KES",
        rate_date=date(2026, 8, 14),
        fetched_at=datetime(2026, 8, 16, 10, tzinfo=UTC),
        rates=RATE_VALUES,
        stale=False,
    )
    monkeypatch.setattr("app.routes.get_current_forex_rates", lambda: result)

    response = client.get(
        "/api/forex/rates",
        headers={"Authorization": f"Bearer {owner['token']}"},
    )

    assert response.status_code == 200
    assert response.get_json()["rates"]["USD"] == "0.00774"
    assert response.get_json()["source"] == "Frankfurter"
    assert response.get_json()["stale"] is False
    assert response.headers["Cache-Control"] == "private, max-age=300"
