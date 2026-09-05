from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.category import Category
from app.models.provider_financing_event import ProviderFinancingEvent
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport
from app.services.fee_dashboard_service import (
    FeeEstimateError,
    estimate_public_tariff,
    get_fee_tariff_catalog,
)


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.no_database
@pytest.mark.parametrize(
    ("service", "amount", "expected_fee"),
    [
        ("other_network", "100.00", "0.00"),
        ("other_network", "100.01", "6.00"),
        ("other_network", "500.00", "6.00"),
        ("other_network", "500.01", "11.00"),
        ("withdrawal", "100.00", "10.00"),
        ("withdrawal", "100.01", "25.00"),
        ("paybill_wallet_bank", "35000.00", "95.00"),
        ("on_net", "250000.00", "0.00"),
    ],
)
def test_airtel_tariff_boundaries(service, amount, expected_fee):
    result = estimate_public_tariff("airtel_money", service, amount)

    assert result["estimatedFee"] == expected_fee
    assert result["confidence"] == "published_band_estimate"
    assert result["source"].startswith("https://")


@pytest.mark.no_database
@pytest.mark.parametrize(
    ("service", "amount", "expected_fee"),
    [
        ("send_money", "100.00", "0.00"),
        ("send_money", "100.01", "7.00"),
        ("send_money", "1000.00", "13.00"),
        ("send_money", "250000.00", "108.00"),
        ("withdrawal", "49.00", "0.00"),
        ("withdrawal", "50.00", "11.00"),
        ("withdrawal", "50000.00", "278.00"),
        ("pochi", "2500.00", "33.00"),
    ],
)
def test_mpesa_tariff_boundaries(service, amount, expected_fee):
    result = estimate_public_tariff("mpesa", service, amount)

    assert result["estimatedFee"] == expected_fee
    assert result["confidence"] == "published_band_estimate"
    assert result["warning"].startswith("Estimate only")


@pytest.mark.no_database
@pytest.mark.parametrize("amount", ["0", "not-money", "10.001", "250000.01"])
def test_tariff_estimator_rejects_unsupported_amounts(amount):
    with pytest.raises(FeeEstimateError):
        estimate_public_tariff("airtel_money", "other_network", amount)


@pytest.mark.no_database
def test_tariff_catalog_keeps_sources_and_bank_fees_separate():
    catalog = get_fee_tariff_catalog()
    services = {
        (service["provider"], service["service"]): service
        for service in catalog["services"]
    }

    assert catalog["version"]
    assert any(service["service"] == "paybill_wallet_bank" for service in catalog["services"])
    assert services[("mpesa", "send_money")]["estimationAvailable"] is True
    assert services[("mpesa", "withdrawal")]["estimationAvailable"] is True
    assert services[("mpesa", "pochi")]["estimationAvailable"] is True
    assert services[("mpesa", "paybill")]["estimationAvailable"] is False
    assert services[("fuliza_mpesa", "maintenance_fee")]["estimationAvailable"] is False
    assert services[("bank", "transfer")]["estimationAvailable"] is False
    assert services[("mpesa", "buy_goods")]["estimationAvailable"] is True
    assert {bank["name"] for bank in catalog["bankReferences"]} == {
        "Absa Bank Kenya",
        "Co-operative Bank of Kenya",
        "Equity Bank Kenya",
        "KCB Bank Kenya",
        "NCBA Bank Kenya",
    }
    assert all("bands" not in bank for bank in catalog["bankReferences"])


def _add_imported_fee(
    *,
    user_id: int,
    reference: str,
    provider: str,
    fee: str | None,
    fee_source: str,
    amount: str,
) -> None:
    category = Category(user_id=user_id, name=f"Fees {reference}", type="expense")
    transaction = Transaction(
        user_id=user_id,
        category=category,
        amount=Decimal(amount),
        date=date.today(),
        description=f"Payment {reference}",
        merchant_name=f"Merchant {reference}",
    )
    import_record = TransactionImport(
        user_id=user_id,
        transaction=transaction,
        provider=provider,
        external_reference=reference,
        message_fingerprint=reference.ljust(64, "0"),
        provider_transaction_type="send_money",
        provider_flow="money_out",
        currency_code="KES",
        fee=Decimal(fee) if fee is not None else None,
        fee_source=fee_source,
    )
    db.session.add_all([category, transaction, import_record])


def test_fee_summary_is_live_and_owner_scoped(
    app,
    client,
    register_user,
    internal_user_id,
):
    owner = register_user("fee-owner", "fee-owner@example.com")
    intruder = register_user("fee-intruder", "fee-intruder@example.com")
    owner_id = internal_user_id(owner)
    intruder_id = internal_user_id(intruder)

    with app.app_context():
        _add_imported_fee(
            user_id=owner_id,
            reference="OWNER1",
            provider="airtel_money",
            fee="10.00",
            fee_source="provider_reported",
            amount="1000.00",
        )
        _add_imported_fee(
            user_id=owner_id,
            reference="OWNER2",
            provider="airtel_money",
            fee="6.00",
            fee_source="estimated_tariff",
            amount="500.00",
        )
        _add_imported_fee(
            user_id=owner_id,
            reference="OWNER3",
            provider="mpesa",
            fee=None,
            fee_source="unknown",
            amount="100.00",
        )
        _add_imported_fee(
            user_id=intruder_id,
            reference="OTHER1",
            provider="mpesa",
            fee="999.00",
            fee_source="provider_reported",
            amount="1000.00",
        )
        db.session.add(ProviderFinancingEvent(
            user_id=owner_id,
            provider="fuliza_mpesa",
            external_reference="FULIZA1",
            message_fingerprint="FULIZA1".ljust(64, "0"),
            event_type="draw",
            principal_amount=Decimal("100.00"),
            currency_code="KES",
            financing_fee=Decimal("2.00"),
            recorded_on=date.today(),
        ))
        db.session.commit()

    response = client.get(
        "/api/fees/summary",
        headers=authorization(owner["token"]),
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    payload = response.get_json()
    assert payload["totalMonth"] == "18.00"
    assert payload["confirmedMonth"] == "12.00"
    assert payload["estimatedMonth"] == "6.00"
    assert payload["unknownFeeCount"] == 1
    assert {row["provider"] for row in payload["providerTotals"]} == {
        "airtel_money",
        "fuliza_mpesa",
    }
    assert all(event["fee"] != "999.00" for event in payload["recentEvents"])


def test_fee_catalog_and_estimator_routes_require_authentication(
    client,
    register_user,
):
    assert client.get("/api/fees/summary").status_code == 401
    assert client.get("/api/fees/tariffs").status_code == 401
    assert client.post("/api/fees/estimate", json={}).status_code == 401

    owner = register_user("calculator", "calculator@example.com")
    headers = authorization(owner["token"])
    catalog_response = client.get("/api/fees/tariffs", headers=headers)
    estimate_response = client.post(
        "/api/fees/estimate",
        headers=headers,
        json={
            "provider": "airtel_money",
            "service": "other_network",
            "amount": "500.00",
        },
    )

    assert catalog_response.status_code == 200
    assert estimate_response.status_code == 200
    assert estimate_response.get_json()["estimatedFee"] == "6.00"
    assert estimate_response.headers["Cache-Control"] == "private, no-store"
