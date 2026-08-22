from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from flask import current_app
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models.ai_daily_usage import AIDailyUsage
from app.services.ai_parser import (
    AITransactionParseResult,
    normalize_transaction_input,
    parse_with_ai,
)
from app.services.ai_support import (
    AIUsageMetadata,
    get_ai_model,
    get_openai_api_key,
)
from app.services.image_validation import ValidatedImage
from app.services.receipt_parser import (
    AIReceiptParseResult,
    parse_receipt_image,
)


class AIBudgetExceededError(RuntimeError):
    """The configured daily application AI budget has been reserved."""


@dataclass(frozen=True, slots=True)
class AIBudgetReservation:
    usage_date: date
    amount_usd: Decimal


def _reservation_amount(purpose: str) -> Decimal:
    config_names = {
        "transaction": "AI_TRANSACTION_RESERVATION_USD",
        "receipt": "AI_RECEIPT_RESERVATION_USD",
    }
    try:
        return current_app.config[config_names[purpose]]
    except KeyError as error:
        raise ValueError(f"Unsupported AI purpose: {purpose!r}") from error


def reserve_daily_budget(purpose: str) -> AIBudgetReservation:
    """Atomically reserve conservative request cost across all workers."""

    usage_date = datetime.now(UTC).date()
    reservation_amount = _reservation_amount(purpose)
    daily_budget = current_app.config["AI_DAILY_BUDGET_USD"]

    if daily_budget <= 0:
        raise AIBudgetExceededError("AI daily budget is disabled")

    try:
        db.session.execute(
            insert(AIDailyUsage)
            .values(usage_date=usage_date)
            .on_conflict_do_nothing(index_elements=["usage_date"])
        )

        usage = db.session.scalar(
            select(AIDailyUsage)
            .where(AIDailyUsage.usage_date == usage_date)
            .with_for_update()
        )
        if usage is None:
            raise RuntimeError("AI daily usage row could not be created")

        committed_and_reserved = (
            usage.estimated_cost_usd + usage.reserved_cost_usd
        )
        if committed_and_reserved + reservation_amount > daily_budget:
            db.session.rollback()
            raise AIBudgetExceededError(
                "The application AI budget has been reached for today"
            )

        usage.reserved_cost_usd += reservation_amount
        db.session.commit()
        return AIBudgetReservation(
            usage_date=usage_date,
            amount_usd=reservation_amount,
        )
    except AIBudgetExceededError:
        raise
    except Exception:
        db.session.rollback()
        raise


def complete_reservation(
    reservation: AIBudgetReservation,
    usage_metadata: AIUsageMetadata,
) -> None:
    try:
        usage = db.session.scalar(
            select(AIDailyUsage)
            .where(AIDailyUsage.usage_date == reservation.usage_date)
            .with_for_update()
        )
        if usage is None:
            raise RuntimeError("AI budget reservation no longer exists")

        usage.reserved_cost_usd = max(
            usage.reserved_cost_usd - reservation.amount_usd,
            Decimal("0"),
        )
        usage.estimated_cost_usd += usage_metadata.estimated_cost_usd
        usage.input_tokens += usage_metadata.input_tokens
        usage.cached_input_tokens += usage_metadata.cached_input_tokens
        usage.output_tokens += usage_metadata.output_tokens
        usage.completed_requests += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def fail_reservation(reservation: AIBudgetReservation) -> None:
    """Conservatively count the reservation when provider cost is unknown."""

    try:
        usage = db.session.scalar(
            select(AIDailyUsage)
            .where(AIDailyUsage.usage_date == reservation.usage_date)
            .with_for_update()
        )
        if usage is None:
            raise RuntimeError("AI budget reservation no longer exists")

        usage.reserved_cost_usd = max(
            usage.reserved_cost_usd - reservation.amount_usd,
            Decimal("0"),
        )
        usage.estimated_cost_usd += reservation.amount_usd
        usage.failed_requests += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def run_transaction_ai(text: str) -> AITransactionParseResult:
    clean_text = normalize_transaction_input(text)
    get_ai_model()
    get_openai_api_key()
    reservation = reserve_daily_budget("transaction")
    try:
        result = parse_with_ai(clean_text)
    except Exception:
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI transaction budget reconciliation failed"
            )
        raise

    complete_reservation(reservation, result.usage)
    return result


def run_receipt_ai(image: ValidatedImage) -> AIReceiptParseResult:
    if not isinstance(image, ValidatedImage):
        raise TypeError(
            "Receipt image must be validated before AI parsing"
        )
    if not image.data:
        raise ValueError("Receipt image cannot be empty")

    get_ai_model()
    get_openai_api_key()
    reservation = reserve_daily_budget("receipt")
    try:
        result = parse_receipt_image(image)
    except Exception:
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI receipt budget reconciliation failed"
            )
        raise

    complete_reservation(reservation, result.usage)
    return result
