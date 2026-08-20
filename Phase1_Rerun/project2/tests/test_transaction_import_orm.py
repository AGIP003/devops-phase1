from sqlalchemy import func, select

from app.extensions import db
from app.models.payment_method import PaymentMethod
from app.models.telegram_preferences import TelegramUserPreferences
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def sample_mpesa_airtime_message() -> str:
    return (
        "UAAIU30XE9 confirmed.You bought Ksh50.00 of airtime "
        "on 17/8/26 at 10:23 AM.New M-PESA balance is Ksh6.11. "
        "Transaction cost, Ksh0.00. Amount you can transact within the day "
        "is 499,950.00. Download My OneApp on https://saf.cx/example"
    )


def seed_provider_payment_methods(app) -> None:
    with app.app_context():
        db.session.add_all([
            PaymentMethod(name="m-pesa"),
            PaymentMethod(name="airtel money"),
        ])
        db.session.commit()


def test_preview_recognizes_data_bundle_as_airtime(
    app,
    client,
    register_user,
):
    owner = register_user("owner", "owner@example.com")

    response = client.post(
        "/api/transaction-imports/preview",
        headers=authorization(owner["token"]),
        json={"message": sample_mpesa_airtime_message()},
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.get_json()["suggestedCategory"] == "airtime"
    assert response.get_json()["importable"] is True


def test_import_requires_user_description(
    app,
    client,
    register_user,
):
    owner = register_user("owner", "owner@example.com")

    response = client.post(
        "/api/transaction-imports",
        headers=authorization(owner["token"]),
        json={
            "message": sample_mpesa_airtime_message(),
            "category": "airtime",
        },
    )

    assert response.status_code == 400
    assert "describe" in response.get_json()["message"].lower()


def test_import_saves_original_date_fee_and_explicit_alias_atomically(
    app,
    client,
    register_user,
    internal_user_id,
):
    seed_provider_payment_methods(app)
    owner = register_user("owner", "owner@example.com")
    user_id = internal_user_id(owner)

    response = client.post(
        "/api/transaction-imports",
        headers=authorization(owner["token"]),
        json={
            "message": sample_mpesa_airtime_message(),
            "description": "Weekly data bundle",
            "category": "airtime",
            "rememberAlias": "weekly data bundle",
        },
    )

    assert response.status_code == 201, response.get_json()
    assert response.headers["Cache-Control"] == "private, no-store"
    payload = response.get_json()
    assert payload["data"]["date"] == "2026-08-17"
    assert payload["data"]["description"] == "weekly data bundle"
    assert payload["data"]["category"] == "Airtime"
    assert payload["import"]["fee"] == "0.00"
    assert payload["rememberedAlias"] == "weekly data bundle"

    with app.app_context():
        import_record = db.session.scalar(select(TransactionImport))
        preferences = db.session.get(TelegramUserPreferences, user_id)

        assert import_record is not None
        assert import_record.transaction_id == payload["data"]["id"]
        assert len(import_record.message_fingerprint) == 64
        assert not hasattr(import_record, "raw_message")
        assert preferences.category_aliases["weekly data bundle"] == "airtime"


def test_duplicate_message_is_rejected_without_second_transaction(
    app,
    client,
    register_user,
    internal_user_id,
):
    seed_provider_payment_methods(app)
    owner = register_user("owner", "owner@example.com")
    user_id = internal_user_id(owner)
    payload = {
        "message": sample_mpesa_airtime_message(),
        "description": "Data for work",
        "category": "airtime",
    }

    first = client.post(
        "/api/transaction-imports",
        headers=authorization(owner["token"]),
        json=payload,
    )
    duplicate = client.post(
        "/api/transaction-imports",
        headers=authorization(owner["token"]),
        json=payload,
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    with app.app_context():
        count = db.session.scalar(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        assert count == 1


def test_same_message_is_scoped_to_each_user(
    app,
    client,
    register_user,
):
    seed_provider_payment_methods(app)
    owner = register_user("owner", "owner@example.com")
    second_user = register_user("second", "second@example.com")
    payload = {
        "message": sample_mpesa_airtime_message(),
        "description": "Data bundle",
        "category": "airtime",
    }

    first = client.post(
        "/api/transaction-imports",
        headers=authorization(owner["token"]),
        json=payload,
    )
    second = client.post(
        "/api/transaction-imports",
        headers=authorization(second_user["token"]),
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201


def test_fuliza_notice_is_previewed_but_not_saved(
    client,
    register_user,
):
    owner = register_user("owner", "owner@example.com")
    message = (
        "UAAIU33DWG Confirmed. Fuliza M-PESA amount is Ksh 1010.00. "
        "Access Fee charged Ksh 10.10. Total Fuliza M-PESA outstanding "
        "amount is Ksh1135.13 due on 16/09/26. To check daily charges, "
        "Dial *334#OK Select Query Charges"
    )

    response = client.post(
        "/api/transaction-imports/preview",
        headers=authorization(owner["token"]),
        json={"message": message},
    )

    assert response.status_code == 200
    assert response.get_json()["kind"] == "fuliza_notice"
    assert response.get_json()["importable"] is False
