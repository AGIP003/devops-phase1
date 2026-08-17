from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.extensions import db
from app.models.debt import Debt, DebtEntry
from app.models.transaction import Transaction
from app.services.debt_service import CreateDebtInput, create_debt_for_user


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def new_debt_payload() -> dict[str, object]:
    return {
        "title": "KCB M-PESA loan",
        "direction": "i_owe",
        "category": "mobile_loan",
        "trackingKind": "new",
        "originalAmount": "10000.00",
        "amountAlreadyRepaid": "2000.00",
        "counterparty": "KCB M-PESA",
        "currencyCode": "KES",
        "openedOn": date.today().isoformat(),
        "hasInterest": True,
        "statedInterestRate": "8.8000",
        "interestPeriod": "fixed",
        "feeTerms": [
            {"feeCategory": "processing"},
            {
                "feeCategory": "other",
                "customFeeName": "Mobile loan access charge",
            },
        ],
        "schedule": {
            "frequency": "one_time",
            "intervalCount": 1,
            "installmentAmount": "8000.00",
            "nextDueDate": date.today().isoformat(),
            "finalDueDate": date.today().isoformat(),
        },
        "notes": "Track the amount reported by the lender",
    }


def create_debt(client, headers, payload=None):
    response = client.post(
        "/api/debts",
        headers=headers,
        json=payload or new_debt_payload(),
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_debt_creation_balance_and_ownership(client, register_user):
    owner = register_user("debt-owner", "debt-owner@example.com")
    intruder = register_user("debt-intruder", "debt-intruder@example.com")
    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])

    debt = create_debt(client, owner_headers)

    assert debt["title"] == "KCB M-PESA loan"
    assert debt["openingBalance"] == "8000.00"
    assert debt["currentBalance"] == "8000.00"
    assert debt["paidAmount"] == "2000.00"
    assert debt["progress"] == 20
    assert debt["schedule"]["frequency"] == "one_time"
    assert len(debt["feeTerms"]) == 2

    intruder_list = client.get("/api/debts", headers=intruder_headers)
    assert intruder_list.status_code == 200
    assert intruder_list.get_json() == []

    debt_id = debt["id"]
    assert client.get(
        f"/api/debts/{debt_id}", headers=intruder_headers
    ).status_code == 404
    assert client.post(
        f"/api/debts/{debt_id}/entries",
        headers=intruder_headers,
        json={
            "entryType": "repayment",
            "amount": "100.00",
            "occurredOn": date.today().isoformat(),
        },
    ).status_code == 404
    assert client.delete(
        f"/api/debts/{debt_id}", headers=intruder_headers
    ).status_code == 404

    owner_response = client.get(f"/api/debts/{debt_id}", headers=owner_headers)
    assert owner_response.status_code == 200
    assert owner_response.get_json()["currentBalance"] == "8000.00"


def test_entries_change_balance_and_repayment_can_link_transaction(
    client,
    register_user,
    payment_method,
):
    owner = register_user("entry-owner", "entry-owner@example.com")
    headers = authorization(owner["token"])
    debt = create_debt(client, headers)
    debt_id = debt["id"]

    repayment_response = client.post(
        f"/api/debts/{debt_id}/entries",
        headers=headers,
        json={
            "entryType": "repayment",
            "amount": "1000.00",
            "occurredOn": date.today().isoformat(),
            "createTransaction": True,
            "paymentMethod": "m-pesa",
        },
    )
    assert repayment_response.status_code == 201, repayment_response.get_json()
    after_repayment = repayment_response.get_json()["data"]
    repayment = after_repayment["entries"][0]
    assert after_repayment["currentBalance"] == "7000.00"
    assert repayment["transactionId"] is not None

    fee_response = client.post(
        f"/api/debts/{debt_id}/entries",
        headers=headers,
        json={
            "entryType": "fee",
            "amount": "350.00",
            "occurredOn": date.today().isoformat(),
            "feeCategory": "late_payment",
        },
    )
    assert fee_response.status_code == 201
    assert fee_response.get_json()["data"]["currentBalance"] == "7350.00"

    interest_response = client.post(
        f"/api/debts/{debt_id}/entries",
        headers=headers,
        json={
            "entryType": "interest",
            "amount": "150.00",
            "occurredOn": date.today().isoformat(),
        },
    )
    assert interest_response.status_code == 201
    assert interest_response.get_json()["data"]["currentBalance"] == "7500.00"


def test_owner_can_correct_debt_and_linked_repayment_atomically(
    app,
    client,
    register_user,
    payment_method,
):
    owner = register_user("debt-editor", "debt-editor@example.com")
    intruder = register_user("debt-edit-intruder", "debt-edit-intruder@example.com")
    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])
    debt = create_debt(client, owner_headers)

    details = new_debt_payload()
    details.update({
        "title": "Corrected KCB M-PESA loan",
        "originalAmount": "12000.00",
    })
    updated = client.patch(
        f"/api/debts/{debt['id']}",
        headers=owner_headers,
        json=details,
    )
    assert updated.status_code == 200, updated.get_json()
    assert updated.get_json()["data"]["openingBalance"] == "10000.00"
    assert updated.get_json()["data"]["amountRepaidBeforeTracking"] == "2000.00"

    repayment_response = client.post(
        f"/api/debts/{debt['id']}/entries",
        headers=owner_headers,
        json={
            "entryType": "repayment",
            "amount": "1000.00",
            "occurredOn": date.today().isoformat(),
            "createTransaction": True,
            "paymentMethod": "m-pesa",
        },
    )
    repayment = repayment_response.get_json()["data"]["entries"][0]

    corrected = client.patch(
        f"/api/debts/{debt['id']}/entries/{repayment['id']}",
        headers=owner_headers,
        json={
            "entryType": "repayment",
            "amount": "500.00",
            "occurredOn": date.today().isoformat(),
            "notes": "Corrected repayment",
        },
    )
    assert corrected.status_code == 200, corrected.get_json()
    assert corrected.get_json()["data"]["currentBalance"] == "9500.00"

    with app.app_context():
        linked = db.session.get(Transaction, repayment["transactionId"])
        assert linked is not None
        assert linked.amount == Decimal("500.00")
        assert linked.description == "Debt repayment: Corrected KCB M-PESA loan"

    hidden = client.patch(
        f"/api/debts/{debt['id']}",
        headers=intruder_headers,
        json=details,
    )
    assert hidden.status_code == 404


def test_other_fee_requires_custom_name(client, register_user):
    owner = register_user("fee-owner", "fee-owner@example.com")
    headers = authorization(owner["token"])

    payload = new_debt_payload()
    payload["feeTerms"] = [{"feeCategory": "other"}]
    create_response = client.post("/api/debts", headers=headers, json=payload)
    assert create_response.status_code == 400
    assert "custom fee name" in create_response.get_json()["message"].lower()

    debt = create_debt(client, headers)
    entry_response = client.post(
        f"/api/debts/{debt['id']}/entries",
        headers=headers,
        json={
            "entryType": "fee",
            "amount": "100.00",
            "occurredOn": date.today().isoformat(),
            "feeCategory": "other",
        },
    )
    assert entry_response.status_code == 400


def test_failed_linked_repayment_rolls_back_both_records(
    app,
    client,
    register_user,
    internal_user_id,
):
    owner = register_user("rollback-owner", "rollback-owner@example.com")
    headers = authorization(owner["token"])
    user_id = internal_user_id(owner)
    debt = create_debt(client, headers)

    response = client.post(
        f"/api/debts/{debt['id']}/entries",
        headers=headers,
        json={
            "entryType": "repayment",
            "amount": "1000.00",
            "occurredOn": date.today().isoformat(),
            "createTransaction": True,
            "paymentMethod": "missing-method",
        },
    )
    assert response.status_code == 400

    with app.app_context():
        entry_count = db.session.scalar(
            select(func.count(DebtEntry.id)).where(DebtEntry.debt_id == debt["id"])
        )
        transaction_count = db.session.scalar(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        stored_debt = db.session.get(Debt, debt["id"])
        assert entry_count == 0
        assert transaction_count == 0
        assert stored_debt is not None
        assert stored_debt.opening_balance == Decimal("8000.00")


def test_external_reference_makes_future_ingestion_idempotent(
    app,
    register_user,
    internal_user_id,
):
    owner = register_user("parser-owner", "parser-owner@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        command = CreateDebtInput(
            title="Amina lunch advance",
            direction="owed_to_me",
            category="personal",
            tracking_kind="existing",
            current_balance=Decimal("8500.00"),
            created_via="telegram",
            external_reference="telegram-message-9281",
        )
        first = create_debt_for_user(user_id, command)
        second = create_debt_for_user(user_id, command)
        stored_count = db.session.scalar(
            select(func.count(Debt.id)).where(Debt.user_id == user_id)
        )

        assert second.id == first.id
        assert stored_count == 1


def test_archived_debt_is_hidden_but_preserved(app, client, register_user):
    owner = register_user("archive-owner", "archive-owner@example.com")
    headers = authorization(owner["token"])
    debt = create_debt(client, headers)

    response = client.delete(f"/api/debts/{debt['id']}", headers=headers)
    assert response.status_code == 200
    assert client.get(f"/api/debts/{debt['id']}", headers=headers).status_code == 404

    with app.app_context():
        stored_debt = db.session.get(Debt, debt["id"])
        assert stored_debt is not None
        assert stored_debt.deleted_at is not None
