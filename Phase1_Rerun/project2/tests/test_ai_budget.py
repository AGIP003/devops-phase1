from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.ai_daily_usage import AIDailyUsage
from app.services.ai_budget_service import (
    AIBudgetExceededError,
    complete_reservation,
    fail_reservation,
    reserve_daily_budget,
)
from app.services.ai_support import AIUsageMetadata


def test_daily_budget_counts_concurrent_reservations(app, monkeypatch):
    monkeypatch.setitem(
        app.config,
        "AI_DAILY_BUDGET_USD",
        Decimal("0.01"),
    )
    monkeypatch.setitem(
        app.config,
        "AI_TRANSACTION_RESERVATION_USD",
        Decimal("0.005"),
    )

    with app.app_context():
        reserve_daily_budget("transaction")
        reserve_daily_budget("transaction")

        with pytest.raises(AIBudgetExceededError):
            reserve_daily_budget("transaction")

        usage = db.session.get(
            AIDailyUsage,
            datetime.now(UTC).date(),
        )
        assert usage is not None
        assert usage.reserved_cost_usd == Decimal("0.01000000")


def test_completed_request_replaces_reservation_with_actual_cost(
    app,
    monkeypatch,
):
    monkeypatch.setitem(
        app.config,
        "AI_DAILY_BUDGET_USD",
        Decimal("0.25"),
    )
    monkeypatch.setitem(
        app.config,
        "AI_TRANSACTION_RESERVATION_USD",
        Decimal("0.005"),
    )

    metadata = AIUsageMetadata(
        model="gpt-5.6-luna",
        latency_ms=125,
        input_tokens=100,
        cached_input_tokens=25,
        output_tokens=20,
        estimated_cost_usd=Decimal("0.00003950"),
    )

    with app.app_context():
        reservation = reserve_daily_budget("transaction")
        complete_reservation(reservation, metadata)

        usage = db.session.get(AIDailyUsage, reservation.usage_date)
        assert usage is not None
        assert usage.reserved_cost_usd == Decimal("0E-8")
        assert usage.estimated_cost_usd == Decimal("0.00003950")
        assert usage.input_tokens == 100
        assert usage.cached_input_tokens == 25
        assert usage.output_tokens == 20
        assert usage.completed_requests == 1


def test_failed_request_is_counted_conservatively(app, monkeypatch):
    monkeypatch.setitem(
        app.config,
        "AI_DAILY_BUDGET_USD",
        Decimal("0.25"),
    )
    monkeypatch.setitem(
        app.config,
        "AI_RECEIPT_RESERVATION_USD",
        Decimal("0.05"),
    )

    with app.app_context():
        reservation = reserve_daily_budget("receipt")
        fail_reservation(reservation)

        usage = db.session.get(AIDailyUsage, reservation.usage_date)
        assert usage is not None
        assert usage.reserved_cost_usd == Decimal("0E-8")
        assert usage.estimated_cost_usd == Decimal("0.05000000")
        assert usage.failed_requests == 1


def test_assistant_uses_its_smaller_reservation(app, monkeypatch):
    monkeypatch.setitem(
        app.config,
        "AI_DAILY_BUDGET_USD",
        Decimal("0.01"),
    )
    monkeypatch.setitem(
        app.config,
        "AI_ASSISTANT_RESERVATION_USD",
        Decimal("0.002"),
    )

    with app.app_context():
        reservation = reserve_daily_budget("assistant")

        assert reservation.amount_usd == Decimal("0.002")


def test_finance_question_reserves_for_its_two_model_calls(app, monkeypatch):
    monkeypatch.setitem(
        app.config,
        "AI_FINANCE_RESERVATION_USD",
        Decimal("0.004"),
    )

    with app.app_context():
        reservation = reserve_daily_budget("finance")

        assert reservation.amount_usd == Decimal("0.004")
