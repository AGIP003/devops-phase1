from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models.savings_goal import SavingsGoal, SavingsGoalEntry
from app.services.savings_goal_service import (
    CreateSavingsGoalEntryInput,
    CreateSavingsGoalInput,
    add_savings_goal_entry_for_user,
    calculate_savings_goal_plan,
    create_savings_goal_for_user,
)


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def goal_payload() -> dict[str, object]:
    return {
        "name": "Emergency fund",
        "targetAmount": "100000.00",
        "currentSavings": "20000.00",
        "targetDate": (date.today() + timedelta(days=70)).isoformat(),
        "contributionFrequency": "weekly",
        "currencyCode": "KES",
        "notes": "Three months of essential expenses",
    }


def create_goal(client, headers):
    response = client.post("/api/goals", headers=headers, json=goal_payload())
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


@pytest.mark.parametrize(
    ("frequency", "target_date", "expected_periods", "expected_amount"),
    [
        ("weekly", date(2026, 8, 30), 2, Decimal("500.00")),
        ("fortnightly", date(2026, 8, 30), 1, Decimal("1000.00")),
        ("monthly", date(2026, 10, 17), 3, Decimal("333.34")),
    ],
)
def test_suggested_contribution_uses_the_selected_frequency(
    frequency,
    target_date,
    expected_periods,
    expected_amount,
):
    goal = SavingsGoal(
        user_id=1,
        name="Frequency example",
        target_amount=Decimal("1000.00"),
        target_date=target_date,
        contribution_frequency=frequency,
        currency_code="KES",
    )

    plan = calculate_savings_goal_plan(goal, as_of=date(2026, 8, 16))

    assert plan.remaining_periods == expected_periods
    assert plan.suggested_contribution == expected_amount


def test_goal_creation_calculates_plan_and_enforces_ownership(
    client,
    register_user,
):
    owner = register_user("goal-owner", "goal-owner@example.com")
    intruder = register_user("goal-intruder", "goal-intruder@example.com")
    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])

    goal = create_goal(client, owner_headers)

    assert goal["name"] == "Emergency fund"
    assert goal["currentSavings"] == "20000.00"
    assert goal["remainingAmount"] == "80000.00"
    assert goal["remainingPeriods"] == 10
    assert goal["suggestedContribution"] == "8000.00"
    assert goal["progress"] == 20
    assert goal["entries"][0]["notes"] == "Opening savings"

    assert client.get("/api/goals", headers=intruder_headers).get_json() == []
    assert client.get(
        f"/api/goals/{goal['id']}", headers=intruder_headers
    ).status_code == 404
    assert client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=intruder_headers,
        json={"entryType": "contribution", "amount": "1000.00"},
    ).status_code == 404
    assert client.delete(
        f"/api/goals/{goal['id']}", headers=intruder_headers
    ).status_code == 404


def test_contribution_and_withdrawal_update_balance(client, register_user):
    owner = register_user("activity-owner", "activity-owner@example.com")
    headers = authorization(owner["token"])
    goal = create_goal(client, headers)

    contribution = client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=headers,
        json={
            "entryType": "contribution",
            "amount": "5000.00",
            "occurredOn": date.today().isoformat(),
            "notes": "Weekly saving",
        },
    )
    assert contribution.status_code == 201
    assert contribution.get_json()["data"]["currentSavings"] == "25000.00"

    withdrawal = client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=headers,
        json={
            "entryType": "withdrawal",
            "amount": "2000.00",
            "occurredOn": date.today().isoformat(),
            "notes": "Emergency repair",
        },
    )
    assert withdrawal.status_code == 201
    assert withdrawal.get_json()["data"]["currentSavings"] == "23000.00"
    assert withdrawal.get_json()["data"]["entries"][0]["entryType"] == "withdrawal"


def test_future_savings_activity_is_rejected_on_create_and_correction(
    client,
    register_user,
):
    owner = register_user("future-goal-owner", "future-goal-owner@example.com")
    headers = authorization(owner["token"])
    goal = create_goal(client, headers)
    future_date = (date.today() + timedelta(days=1)).isoformat()

    future_entry = client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=headers,
        json={
            "entryType": "contribution",
            "amount": "5000.00",
            "occurredOn": future_date,
        },
    )
    assert future_entry.status_code == 400

    opening_entry_id = goal["entries"][0]["id"]
    future_correction = client.patch(
        f"/api/goals/{goal['id']}/entries/{opening_entry_id}",
        headers=headers,
        json={
            "entryType": "contribution",
            "amount": "5000.00",
            "occurredOn": future_date,
        },
    )
    assert future_correction.status_code == 400

    unchanged = client.get(f"/api/goals/{goal['id']}", headers=headers)
    assert unchanged.status_code == 200
    assert unchanged.get_json()["currentSavings"] == "20000.00"
    assert unchanged.get_json()["entries"][0]["occurredOn"] == date.today().isoformat()


def test_owner_can_correct_goal_details_and_savings_activity(
    client,
    register_user,
):
    owner = register_user("goal-editor", "goal-editor@example.com")
    intruder = register_user("goal-editor-intruder", "goal-editor-intruder@example.com")
    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])
    goal = create_goal(client, owner_headers)

    details = goal_payload()
    details.update({
        "name": "Emergency reserve",
        "targetAmount": "120000.00",
        "contributionFrequency": "monthly",
    })
    updated = client.patch(
        f"/api/goals/{goal['id']}",
        headers=owner_headers,
        json=details,
    )
    assert updated.status_code == 200, updated.get_json()
    assert updated.get_json()["data"]["name"] == "Emergency reserve"
    assert updated.get_json()["data"]["targetAmount"] == "120000.00"

    opening_entry_id = goal["entries"][0]["id"]
    corrected = client.patch(
        f"/api/goals/{goal['id']}/entries/{opening_entry_id}",
        headers=owner_headers,
        json={
            "entryType": "contribution",
            "amount": "5000.00",
            "occurredOn": date.today().isoformat(),
            "notes": "Corrected opening savings",
        },
    )
    assert corrected.status_code == 200, corrected.get_json()
    assert corrected.get_json()["data"]["currentSavings"] == "5000.00"

    hidden = client.patch(
        f"/api/goals/{goal['id']}/entries/{opening_entry_id}",
        headers=intruder_headers,
        json={
            "entryType": "contribution",
            "amount": "1.00",
            "occurredOn": date.today().isoformat(),
        },
    )
    assert hidden.status_code == 404


def test_invalid_withdrawal_rolls_back_and_session_recovers(
    app,
    client,
    register_user,
):
    owner = register_user("withdraw-owner", "withdraw-owner@example.com")
    headers = authorization(owner["token"])
    goal = create_goal(client, headers)

    failed = client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=headers,
        json={
            "entryType": "withdrawal",
            "amount": "25000.00",
            "occurredOn": date.today().isoformat(),
        },
    )
    assert failed.status_code == 400

    successful = client.post(
        f"/api/goals/{goal['id']}/entries",
        headers=headers,
        json={
            "entryType": "contribution",
            "amount": "1000.00",
            "occurredOn": date.today().isoformat(),
        },
    )
    assert successful.status_code == 201
    assert successful.get_json()["data"]["currentSavings"] == "21000.00"

    with app.app_context():
        count = db.session.scalar(
            select(func.count(SavingsGoalEntry.id)).where(
                SavingsGoalEntry.goal_id == goal["id"]
            )
        )
        assert count == 2  # Opening savings and the successful contribution.


def test_telegram_source_reference_is_idempotent(
    app,
    register_user,
    internal_user_id,
):
    owner = register_user("telegram-goal", "telegram-goal@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        goal_command = CreateSavingsGoalInput(
            name="Emergency fund",
            target_amount=Decimal("60000.00"),
            target_date=date.today() + timedelta(days=90),
            contribution_frequency="monthly",
            created_via="telegram",
            external_reference="telegram-goal-201",
        )
        first_goal = create_savings_goal_for_user(user_id, goal_command)
        second_goal = create_savings_goal_for_user(user_id, goal_command)
        assert second_goal.id == first_goal.id

        entry_command = CreateSavingsGoalEntryInput(
            entry_type="contribution",
            amount=Decimal("2000.00"),
            occurred_on=date.today(),
            created_via="telegram",
            external_reference="telegram-message-202",
        )
        first_result = add_savings_goal_entry_for_user(
            user_id,
            first_goal.id,
            entry_command,
        )
        second_result = add_savings_goal_entry_for_user(
            user_id,
            first_goal.id,
            entry_command,
        )
        assert first_result is not None
        assert second_result is not None
        assert second_result.current_savings == Decimal("2000.00")

        goal_count = db.session.scalar(select(func.count(SavingsGoal.id)))
        entry_count = db.session.scalar(select(func.count(SavingsGoalEntry.id)))
        assert goal_count == 1
        assert entry_count == 1


def test_archived_goal_is_hidden_but_preserved(app, client, register_user):
    owner = register_user("archive-goal", "archive-goal@example.com")
    headers = authorization(owner["token"])
    goal = create_goal(client, headers)

    response = client.delete(f"/api/goals/{goal['id']}", headers=headers)
    assert response.status_code == 200
    assert client.get(
        f"/api/goals/{goal['id']}", headers=headers
    ).status_code == 404

    with app.app_context():
        stored_goal = db.session.get(SavingsGoal, goal["id"])
        assert stored_goal is not None
        assert stored_goal.deleted_at is not None
