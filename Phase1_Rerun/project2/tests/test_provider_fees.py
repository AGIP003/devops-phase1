from sqlalchemy import select

from app.extensions import db
from app.models.payment_method import PaymentMethod
from app.models.transaction_import import TransactionImport
from app.services.provider_fee_service import backfill_missing_provider_fees


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def seed_payment_methods(app):
    with app.app_context():
        db.session.add_all([
            PaymentMethod(name="m-pesa"),
            PaymentMethod(name="airtel money"),
        ])
        db.session.commit()


def airtel_topup_message() -> str:
    return (
        "29813220000 Successful. Airtime top up of Ksh 300 "
        "to 0700000000. Bal: Ksh 828.5."
    )


def mpesa_airtime_message() -> str:
    return (
        "UAAIU30XE9 confirmed.You bought Ksh50.00 of airtime "
        "on 17/8/26 at 10:23 AM.New M-PESA balance is Ksh6.11. "
        "Transaction cost, Ksh0.00."
    )


def import_message(client, headers, message, *, date_value=None):
    payload = {
        "message": message,
        "description": "Family airtime",
        "category": "airtime",
    }
    if date_value:
        payload["date"] = date_value
    response = client.post(
        "/api/transaction-imports",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_fee_backfill_is_dry_run_by_default_and_user_can_confirm_estimate(
    app,
    client,
    register_user,
):
    seed_payment_methods(app)
    owner = register_user("fee-owner", "fee-owner@example.com")
    other = register_user("fee-other", "fee-other@example.com")
    transaction = import_message(
        client,
        authorization(owner["token"]),
        airtel_topup_message(),
        date_value="2026-08-20",
    )

    with app.app_context():
        record = db.session.scalar(select(TransactionImport))
        record.provider = "mpesa"
        record.provider_transaction_type = "buy_goods"
        record.transaction.merchant_name = "Khetia Drapers"
        db.session.commit()

        preview = backfill_missing_provider_fees()
        db.session.refresh(record)
        assert preview["mode"] == "dry-run"
        assert preview["candidateCount"] == 1
        assert record.fee is None
        assert record.fee_source == "unknown"

        applied = backfill_missing_provider_fees(apply_changes=True)
        db.session.refresh(record)
        assert applied["candidateCount"] == 1
        assert record.fee_source == "estimated_tariff"
        assert str(record.fee) == "0.00"
        assert str(record.original_estimated_fee) == "0.00"

        repeated = backfill_missing_provider_fees(apply_changes=True)
        assert repeated["candidateCount"] == 0

    forbidden = client.patch(
        f"/api/transactions/{transaction['id']}/provider-fee",
        headers=authorization(other["token"]),
        json={"fee": "3.50"},
    )
    assert forbidden.status_code == 404

    confirmed = client.patch(
        f"/api/transactions/{transaction['id']}/provider-fee",
        headers=authorization(owner["token"]),
        json={"fee": "3.50"},
    )
    assert confirmed.status_code == 200, confirmed.get_json()
    assert confirmed.get_json()["data"]["fee"] == "3.50"
    assert confirmed.get_json()["data"]["feeSource"] == "user_confirmed"
    assert confirmed.get_json()["data"]["originalEstimatedFee"] == "0.00"


def test_provider_reported_fee_cannot_be_overwritten(
    app,
    client,
    register_user,
):
    seed_payment_methods(app)
    owner = register_user("actual-fee", "actual-fee@example.com")
    transaction = import_message(
        client,
        authorization(owner["token"]),
        mpesa_airtime_message(),
    )

    response = client.patch(
        f"/api/transactions/{transaction['id']}/provider-fee",
        headers=authorization(owner["token"]),
        json={"fee": "12.00"},
    )

    assert response.status_code == 400
    assert "provider-reported" in response.get_json()["message"]
