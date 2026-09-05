from decimal import Decimal

from sqlalchemy import func, select

from app.extensions import db
from app.importers.contracts import (
    ParsedTransactionMessage,
    ProviderFlowDirection,
    TransactionClassification,
)
from app.models.payment_method import PaymentMethod
from app.models.telegram_preferences import TelegramUserPreferences
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport
from app.schemas import ProviderImportParseResult
from app.services.ai_support import AIUsageMetadata
from app.services.provider_import_ai import AIProviderImportResult


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def sample_mpesa_airtime_message() -> str:
    return (
        "UAAIU30XE9 confirmed.You bought Ksh50.00 of airtime "
        "on 17/8/26 at 10:23 AM.New M-PESA balance is Ksh6.11. "
        "Transaction cost, Ksh0.00. Amount you can transact within the day "
        "is 499,950.00. Download My OneApp on https://saf.cx/example"
    )


def sample_airtel_topup_message() -> str:
    return (
        "29813220000 Successful. Airtime top up of Ksh 300 "
        "to 0700000000. Bal: Ksh 828.5."
    )


def sample_airtel_topup_for_line_message() -> str:
    return (
        "29148245185 Successful. Airtime top up for line 101784609 "
        "of Ksh 20 is successful. Bal: Ksh 520.5. To check your "
        "airtime balance, dial *131#"
    )


def sample_airtel_wallet_transfer_message() -> str:
    return (
        "Y3QV334AMGX. Ksh 17,500 sent to SAMPLE PERSON 703602692 "
        "on 05/09/26 at 11:20 PM. Fee: Ksh 105. Bal: Ksh 95.5. "
        "MPESA ID: UI5IU5CE3F"
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


def test_airtel_topup_requires_user_supplied_date_when_provider_omits_it(
    app,
    client,
    register_user,
):
    seed_provider_payment_methods(app)
    owner = register_user("owner", "owner@example.com")
    headers = authorization(owner["token"])

    preview = client.post(
        "/api/transaction-imports/preview",
        headers=headers,
        json={"message": sample_airtel_topup_message()},
    )

    assert preview.status_code == 200
    assert preview.get_json()["requiresDate"] is True
    assert preview.get_json()["occurredAt"] is None
    assert preview.get_json()["suggestedCategory"] == "airtime"

    missing_date = client.post(
        "/api/transaction-imports",
        headers=headers,
        json={
            "message": sample_airtel_topup_message(),
            "description": "Airtime for family",
            "category": "airtime",
        },
    )
    assert missing_date.status_code == 400

    saved = client.post(
        "/api/transaction-imports",
        headers=headers,
        json={
            "message": sample_airtel_topup_message(),
            "description": "Airtime for family",
            "category": "airtime",
            "date": "2026-08-20",
        },
    )

    assert saved.status_code == 201, saved.get_json()
    assert saved.get_json()["data"]["date"] == "2026-08-20"
    assert saved.get_json()["import"]["occurredAt"] is None


def test_preview_accepts_airtel_topup_for_line_template(
    client,
    register_user,
):
    owner = register_user("owner", "owner@example.com")

    response = client.post(
        "/api/transaction-imports/preview",
        headers=authorization(owner["token"]),
        json={"message": sample_airtel_topup_for_line_message()},
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["provider"] == "airtel_money"
    assert payload["amount"] == "20"
    assert payload["suggestedCategory"] == "airtime"
    assert payload["requiresDate"] is True
    assert payload["occurredAt"] is None
    assert "101784609" not in str(payload)


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
        assert import_record.provider_flow == "money_out"
        assert import_record.fee_source == "provider_reported"
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


def test_ambiguous_wallet_movement_requires_classification_and_transfer_fee_counts(
    app,
    client,
    register_user,
):
    seed_provider_payment_methods(app)
    owner = register_user("transfer-owner", "transfer-owner@example.com")
    headers = authorization(owner["token"])
    message = sample_airtel_wallet_transfer_message()

    preview = client.post(
        "/api/transaction-imports/preview",
        headers=headers,
        json={"message": message},
    )

    assert preview.status_code == 200, preview.get_json()
    preview_data = preview.get_json()
    assert preview_data["flowDirection"] == "money_out"
    assert preview_data["suggestedType"] == "expense"
    assert preview_data["requiresClassification"] is True

    missing_choice = client.post(
        "/api/transaction-imports",
        headers=headers,
        json={
            "message": message,
            "description": "Moved to my M-Pesa wallet",
            "category": "internal transfer",
        },
    )
    assert missing_choice.status_code == 400
    assert "choose whether" in missing_choice.get_json()["message"].lower()

    saved = client.post(
        "/api/transaction-imports",
        headers=headers,
        json={
            "message": message,
            "description": "Moved to my M-Pesa wallet",
            "type": "transfer",
            "category": "internal transfer",
        },
    )
    assert saved.status_code == 201, saved.get_json()
    assert saved.get_json()["data"]["type"] == "transfer"
    assert saved.get_json()["data"]["provider_flow"] == "money_out"

    summary = client.get(
        "/api/analytics/summary?period=30-days",
        headers=headers,
    )
    assert summary.status_code == 200, summary.get_json()
    cash_flow = summary.get_json()["cashFlow"]
    assert cash_flow["income"] == "0.00"
    assert cash_flow["recordedExpenses"] == "0.00"
    assert cash_flow["transactionFees"] == "105.00"
    assert cash_flow["expenses"] == "105.00"

    with app.app_context():
        import_record = db.session.scalar(select(TransactionImport))
        assert import_record.provider_flow == "money_out"


def test_fuliza_notice_is_previewed_and_saved_without_counting_principal_as_spending(
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
    assert response.get_json()["importable"] is True
    assert response.get_json()["requiresDate"] is True

    missing_date = client.post(
        "/api/provider-financing-events",
        headers=authorization(owner["token"]),
        json={"message": message},
    )
    assert missing_date.status_code == 400

    saved = client.post(
        "/api/provider-financing-events",
        headers=authorization(owner["token"]),
        json={"message": message, "date": "2026-08-23"},
    )
    assert saved.status_code == 201, saved.get_json()
    assert saved.get_json()["data"]["principalAmount"] == "1010.00"
    assert saved.get_json()["data"]["financingFee"] == "10.10"

    duplicate = client.post(
        "/api/provider-financing-events",
        headers=authorization(owner["token"]),
        json={"message": message, "date": "2026-08-23"},
    )
    assert duplicate.status_code == 409

    summary = client.get(
        "/api/analytics/summary?period=30-days",
        headers=authorization(owner["token"]),
    )
    assert summary.status_code == 200
    cash_flow = summary.get_json()["cashFlow"]
    assert cash_flow["recordedExpenses"] == "0.00"
    assert cash_flow["financingCharges"] == "10.10"
    assert cash_flow["expenses"] == "10.10"


def test_ai_fallback_preview_can_be_confirmed_and_saved_once(
    app,
    client,
    register_user,
    monkeypatch,
):
    from app import routes

    seed_provider_payment_methods(app)
    owner = register_user("ai-import-owner", "ai-import-owner@example.com")
    headers = authorization(owner["token"])
    raw_message = (
        "Z3QRSOZ29C6 Confirmed. Ksh 700 completed to SAMPLE MERCHANT "
        "on 03/09/26 at 02:19 PM. Fee: Ksh 12.00. Bal: Ksh 17000.5."
    )
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "Z3QRSOZ29C6",
            "occurred_at": "2026-09-03T14:19:00+03:00",
            "amount": "700.00",
            "currency": "KES",
            "flow_direction": "money_out",
            "description": "Paid SAMPLE MERCHANT",
            "counterparty": "SAMPLE MERCHANT",
            "fee": "12.00",
            "provider_transaction_type": "merchant_payment",
            "confidence": 0.82,
            "needs_review": True,
        },
    })
    ai_result = AIProviderImportResult(
        extraction=extraction,
        parsed=ParsedTransactionMessage(
            provider="airtel_money",
            external_reference="Z3QRSOZ29C6",
            occurred_at=extraction.transaction.occurred_at,
            amount=extraction.transaction.amount,
            currency="KES",
            flow_direction=ProviderFlowDirection.MONEY_OUT,
            suggested_classification=TransactionClassification.EXPENSE,
            description="Paid SAMPLE MERCHANT",
            counterparty="SAMPLE MERCHANT",
            fee=Decimal("12.00"),
            provider_transaction_type="merchant_payment",
        ),
        format_signature="airtel:confirmed:fee:balance",
        usage=AIUsageMetadata(
            model="gpt-5.6-luna",
            latency_ms=10,
            input_tokens=100,
            cached_input_tokens=0,
            output_tokens=30,
            estimated_cost_usd=Decimal("0.0001"),
        ),
    )
    monkeypatch.setattr(routes, "run_provider_import_ai", lambda message: ai_result)
    monkeypatch.setitem(app.config, "AI_FALLBACK_ENABLED", True)

    preview = client.post(
        "/api/transaction-imports/preview",
        headers=headers,
        json={"message": raw_message},
    )

    assert preview.status_code == 200, preview.get_json()
    preview_payload = preview.get_json()
    assert preview_payload["parserStrategy"] == "ai"
    assert preview_payload["needsReview"] is True
    assert preview_payload["previewToken"]

    save_payload = {
        "message": raw_message,
        "previewToken": preview_payload["previewToken"],
        "description": "Equipment payment",
        "category": "food",
        "type": "expense",
    }
    saved = client.post(
        "/api/transaction-imports",
        headers=headers,
        json=save_payload,
    )

    assert saved.status_code == 201, saved.get_json()
    assert saved.get_json()["import"]["fee"] == "12.00"

    duplicate = client.post(
        "/api/transaction-imports",
        headers=headers,
        json=save_payload,
    )
    assert duplicate.status_code == 409


def test_ai_preview_token_rejects_a_changed_provider_message(
    app,
    client,
    register_user,
    monkeypatch,
):
    from app import routes

    owner = register_user("bound-preview", "bound-preview@example.com")
    headers = authorization(owner["token"])
    raw_message = (
        "Z3QRSOZ29C6 Confirmed. Ksh 700 completed to SAMPLE MERCHANT "
        "on 03/09/26 at 02:19 PM. Fee: Ksh 12.00. Bal: Ksh 17000.5."
    )
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "Z3QRSOZ29C6",
            "occurred_at": "2026-09-03T14:19:00+03:00",
            "amount": "700.00",
            "currency": "KES",
            "flow_direction": "money_out",
            "description": "Paid SAMPLE MERCHANT",
            "counterparty": "SAMPLE MERCHANT",
            "fee": "12.00",
            "provider_transaction_type": "merchant_payment",
            "confidence": 0.82,
            "needs_review": True,
        },
    })
    ai_result = AIProviderImportResult(
        extraction=extraction,
        parsed=ParsedTransactionMessage(
            provider="airtel_money",
            external_reference="Z3QRSOZ29C6",
            occurred_at=extraction.transaction.occurred_at,
            amount=extraction.transaction.amount,
            currency="KES",
            flow_direction=ProviderFlowDirection.MONEY_OUT,
            suggested_classification=TransactionClassification.EXPENSE,
            description="Paid SAMPLE MERCHANT",
            counterparty="SAMPLE MERCHANT",
            fee=Decimal("12.00"),
            provider_transaction_type="merchant_payment",
        ),
        format_signature="airtel:confirmed:fee:balance",
        usage=AIUsageMetadata(
            model="gpt-5.6-luna",
            latency_ms=10,
            input_tokens=100,
            cached_input_tokens=0,
            output_tokens=30,
            estimated_cost_usd=Decimal("0.0001"),
        ),
    )
    monkeypatch.setattr(routes, "run_provider_import_ai", lambda message: ai_result)
    monkeypatch.setitem(app.config, "AI_FALLBACK_ENABLED", True)
    preview = client.post(
        "/api/transaction-imports/preview",
        headers=headers,
        json={"message": raw_message},
    ).get_json()

    changed = client.post(
        "/api/transaction-imports",
        headers=headers,
        json={
            "message": raw_message.replace("Ksh 700", "Ksh 900"),
            "previewToken": preview["previewToken"],
            "description": "Equipment payment",
            "category": "shopping",
        },
    )

    assert changed.status_code == 400
    assert "does not match" in changed.get_json()["message"]
