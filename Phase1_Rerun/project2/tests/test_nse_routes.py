from datetime import UTC, datetime, timedelta

from app.services.nse_client import NseProviderError, ProviderPayload
from app.services.nse_service import NseMarketResult, get_nse_stocks


MARKET_ROWS = [{
    "symbol": "SCOM.KE",
    "ticker": "SCOM",
    "name": "Safaricom PLC",
    "price": "37.25",
    "changePercent": "1.776",
    "currency": "KES",
    "exchange": "NSE",
    "sector": "Telecommunications",
    "lastPriceUpdate": "2026-08-25T16:45:15+00:00",
}]


def test_nse_cache_avoids_repeat_network_calls_and_serves_stale_data(app, monkeypatch):
    now = datetime(2026, 8, 26, 8, tzinfo=UTC)
    calls = {"count": 0}

    def successful_fetcher(**kwargs):
        calls["count"] += 1
        return ProviderPayload(
            payload=MARKET_ROWS,
            source_updated_at=datetime(2026, 8, 25, 16, 45, tzinfo=UTC),
        )

    with app.app_context():
        first = get_nse_stocks(fetcher=successful_fetcher, now=now)
        second = get_nse_stocks(
            fetcher=successful_fetcher,
            now=now + timedelta(minutes=5),
        )

        monkeypatch.setitem(app.config, "NSE_CACHE_TTL_SECONDS", 1)

        def failing_fetcher(**kwargs):
            raise NseProviderError("provider timeout")

        stale = get_nse_stocks(
            fetcher=failing_fetcher,
            now=now + timedelta(hours=1),
        )

    assert first.stale is False
    assert second.stale is False
    assert calls["count"] == 1
    assert stale.stale is True
    assert stale.payload[0]["ticker"] == "SCOM"


def test_nse_market_route_requires_authentication_and_attributes_source(
    client,
    register_user,
    monkeypatch,
):
    unauthorized = client.get("/api/nse/stocks")
    assert unauthorized.status_code == 401

    owner = register_user("nse_owner", "nse-owner@example.com")
    result = NseMarketResult(
        payload=MARKET_ROWS,
        source_updated_at=datetime(2026, 8, 25, 16, 45, tzinfo=UTC),
        fetched_at=datetime(2026, 8, 26, 8, tzinfo=UTC),
        stale=False,
    )
    monkeypatch.setattr("app.nse_routes.get_nse_stocks", lambda: result)

    response = client.get(
        "/api/nse/stocks",
        headers={"Authorization": f"Bearer {owner['token']}"},
    )

    assert response.status_code == 200
    assert response.get_json()["stocks"][0]["price"] == "37.25"
    assert response.get_json()["source"]["license"] == "CC BY 4.0"
    assert response.get_json()["source"]["quoteType"] == "Delayed or end-of-day"
    assert response.headers["Cache-Control"] == "private, max-age=60"
