from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models.recurring_commitment import (
    CommitmentOccurrence,
    RecurringCommitment,
)
from app.services.recurring_commitment_service import (
    CreateRecurringCommitmentInput,
    ResolveCommitmentCycleInput,
    calculate_next_due_date,
    create_recurring_commitment_for_user,
    resolve_commitment_cycle_for_user,
)


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def bill_payload(**overrides) -> dict[str, object]:
    payload = {
        "kind": "bill",
        "name": "Electricity",
        "provider": "Kenya Power",
        "category": "Utilities",
        "amount": "2500.00",
        "amountKind": "estimated",
        "nextDueDate": "2026-08-31",
        "frequency": "monthly",
        "currencyCode": "KES",
        "notes": "Amount changes with usage",
    }
    payload.update(overrides)
    return payload


def create_bill(client, headers, **overrides):
    response = client.post(
        "/api/commitments",
        headers=headers,
        json=bill_payload(**overrides),
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_bill_creation_and_object_ownership(client, register_user):
    owner = register_user("bill-owner", "bill-owner@example.com")
    intruder = register_user("bill-intruder", "bill-intruder@example.com")
    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])

    bill = create_bill(client, owner_headers)

    assert bill["kind"] == "bill"
    assert bill["amountKind"] == "estimated"
    assert bill["autoRenews"] is None
    assert bill["occurrences"] == []
    assert client.get("/api/commitments", headers=intruder_headers).get_json() == []
    assert client.get(
        f"/api/commitments/{bill['id']}",
        headers=intruder_headers,
    ).status_code == 404
    assert client.post(
        f"/api/commitments/{bill['id']}/cycles",
        headers=intruder_headers,
        json={"resolution": "paid", "actualAmount": "2500.00"},
    ).status_code == 404
    assert client.patch(
        f"/api/commitments/{bill['id']}/status",
        headers=intruder_headers,
        json={"status": "cancelled"},
    ).status_code == 404
    assert client.delete(
        f"/api/commitments/{bill['id']}",
        headers=intruder_headers,
    ).status_code == 404


def test_paid_and_skipped_cycles_append_history_and_advance_due_date(
    client,
    register_user,
):
    owner = register_user("cycle-owner", "cycle-owner@example.com")
    headers = authorization(owner["token"])
    bill = create_bill(client, headers)

    paid = client.post(
        f"/api/commitments/{bill['id']}/cycles",
        headers=headers,
        json={
            "resolution": "paid",
            "actualAmount": "2300.00",
            "resolvedOn": "2026-08-29",
            "notes": "Paid early",
        },
    )
    assert paid.status_code == 201, paid.get_json()
    paid_bill = paid.get_json()["data"]
    assert paid_bill["nextDueDate"] == "2026-09-30"
    assert paid_bill["occurrences"][0]["dueDate"] == "2026-08-31"
    assert paid_bill["occurrences"][0]["actualAmount"] == "2300.00"

    skipped = client.post(
        f"/api/commitments/{bill['id']}/cycles",
        headers=headers,
        json={
            "resolution": "skipped",
            "resolvedOn": "2026-09-30",
            "notes": "Provider waived this cycle",
        },
    )
    assert skipped.status_code == 201, skipped.get_json()
    skipped_bill = skipped.get_json()["data"]
    assert skipped_bill["nextDueDate"] == "2026-10-31"
    assert skipped_bill["occurrences"][0]["resolution"] == "skipped"
    assert skipped_bill["occurrences"][0]["actualAmount"] is None


def test_month_end_recurrence_keeps_its_original_anchor():
    commitment = RecurringCommitment(
        user_id=1,
        kind="bill",
        name="Month-end bill",
        amount=Decimal("100.00"),
        amount_kind="fixed",
        next_due_date=date(2027, 1, 31),
        frequency="monthly",
        recurrence_anchor_day=31,
        auto_renews=None,
    )

    commitment.next_due_date = calculate_next_due_date(commitment)
    assert commitment.next_due_date == date(2027, 2, 28)
    commitment.next_due_date = calculate_next_due_date(commitment)
    assert commitment.next_due_date == date(2027, 3, 31)


def test_subscription_cancel_reactivate_and_archive_preserve_history(
    app,
    client,
    register_user,
):
    owner = register_user("subscription-owner", "subscription-owner@example.com")
    headers = authorization(owner["token"])
    response = client.post(
        "/api/commitments",
        headers=headers,
        json={
            "kind": "subscription",
            "name": "Spotify",
            "provider": "Spotify",
            "amount": "490.00",
            "amountKind": "fixed",
            "nextDueDate": "2026-09-02",
            "frequency": "monthly",
            "autoRenews": True,
        },
    )
    assert response.status_code == 201, response.get_json()
    subscription = response.get_json()["data"]

    cancelled = client.patch(
        f"/api/commitments/{subscription['id']}/status",
        headers=headers,
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200
    assert cancelled.get_json()["data"]["status"] == "cancelled"

    blocked_cycle = client.post(
        f"/api/commitments/{subscription['id']}/cycles",
        headers=headers,
        json={"resolution": "paid", "actualAmount": "490.00"},
    )
    assert blocked_cycle.status_code == 400

    reactivated = client.patch(
        f"/api/commitments/{subscription['id']}/status",
        headers=headers,
        json={"status": "active"},
    )
    assert reactivated.status_code == 200

    archived = client.delete(
        f"/api/commitments/{subscription['id']}",
        headers=headers,
    )
    assert archived.status_code == 200
    assert client.get(
        f"/api/commitments/{subscription['id']}",
        headers=headers,
    ).status_code == 404

    with app.app_context():
        stored = db.session.get(RecurringCommitment, subscription["id"])
        assert stored is not None
        assert stored.deleted_at is not None


def test_invalid_cross_kind_fields_are_rejected(client, register_user):
    owner = register_user("invalid-bill", "invalid-bill@example.com")
    headers = authorization(owner["token"])

    estimated_subscription = client.post(
        "/api/commitments",
        headers=headers,
        json=bill_payload(
            kind="subscription",
            amountKind="estimated",
            autoRenews=True,
        ),
    )
    assert estimated_subscription.status_code == 400

    incomplete_custom = client.post(
        "/api/commitments",
        headers=headers,
        json=bill_payload(frequency="custom"),
    )
    assert incomplete_custom.status_code == 400


def test_external_source_retries_are_idempotent(
    app,
    register_user,
    internal_user_id,
):
    owner = register_user("telegram-bill", "telegram-bill@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        command = CreateRecurringCommitmentInput(
            kind="bill",
            name="Internet",
            amount=Decimal("3990.00"),
            amount_kind="fixed",
            next_due_date=date(2026, 9, 6),
            frequency="monthly",
            created_via="telegram",
            external_reference="telegram-bill-301",
        )
        first = create_recurring_commitment_for_user(user_id, command)
        second = create_recurring_commitment_for_user(user_id, command)
        assert second.id == first.id

        cycle = ResolveCommitmentCycleInput(
            resolution="paid",
            actual_amount=Decimal("3990.00"),
            resolved_on=date(2026, 9, 5),
            created_via="telegram",
            external_reference="telegram-payment-302",
        )
        first_result = resolve_commitment_cycle_for_user(user_id, first.id, cycle)
        second_result = resolve_commitment_cycle_for_user(user_id, first.id, cycle)
        assert first_result is not None
        assert second_result is not None
        assert second_result.next_due_date == date(2026, 10, 6)

        commitment_count = db.session.scalar(
            select(func.count(RecurringCommitment.id))
        )
        occurrence_count = db.session.scalar(
            select(func.count(CommitmentOccurrence.id))
        )
        assert commitment_count == 1
        assert occurrence_count == 1


def test_commit_failure_rolls_back_due_date_and_session_recovers(
    app,
    register_user,
    internal_user_id,
    monkeypatch,
):
    owner = register_user("rollback-bill", "rollback-bill@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        commitment = create_recurring_commitment_for_user(
            user_id,
            CreateRecurringCommitmentInput(
                kind="bill",
                name="Rent",
                amount=Decimal("25000.00"),
                next_due_date=date(2026, 9, 1),
                frequency="monthly",
            ),
        )
        session = db.session()
        real_commit = session.commit

        def fail_commit():
            raise RuntimeError("simulated commit failure")

        monkeypatch.setattr(session, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="simulated commit failure"):
            resolve_commitment_cycle_for_user(
                user_id,
                commitment.id,
                ResolveCommitmentCycleInput(
                    resolution="paid",
                    actual_amount=Decimal("25000.00"),
                    resolved_on=date(2026, 9, 1),
                ),
            )

        monkeypatch.setattr(session, "commit", real_commit)
        stored = db.session.get(RecurringCommitment, commitment.id)
        assert stored is not None
        assert stored.next_due_date == date(2026, 9, 1)
        assert db.session.scalar(select(func.count(CommitmentOccurrence.id))) == 0

        recovered = resolve_commitment_cycle_for_user(
            user_id,
            commitment.id,
            ResolveCommitmentCycleInput(
                resolution="paid",
                actual_amount=Decimal("25000.00"),
                resolved_on=date(2026, 9, 1),
            ),
        )
        assert recovered is not None
        assert recovered.next_due_date == date(2026, 10, 1)
