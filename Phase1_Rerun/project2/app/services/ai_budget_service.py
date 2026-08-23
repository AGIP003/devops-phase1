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
    current_request_id,
    get_ai_model,
    get_openai_api_key,
)
from app.services.image_validation import ValidatedImage
from app.services.receipt_parser import (
    AIReceiptParseResult,
    parse_receipt_image,
)
from app.services.telegram_assistant import (
    AITelegramAssistantResult,
    normalize_assistant_input,
    respond_to_telegram_message,
)
from app.services.finance_assistant import (
    AIFinanceAnswerResult,
    AIWeeklySummaryResult,
    answer_finance_question,
    build_weekly_finance_summary,
    normalize_finance_question,
)


class AIBudgetExceededError(RuntimeError):
    """The configured daily application AI budget has been reserved."""


@dataclass(frozen=True, slots=True)
class AIBudgetReservation:
    usage_date: date
    amount_usd: Decimal


def _log_ai_completion(purpose: str, usage: AIUsageMetadata) -> None:
    current_app.logger.info(
        "ai_request_completed request_id=%s purpose=%s model=%s "
        "provider_request_ids=%s latency_ms=%s input_tokens=%s "
        "cached_input_tokens=%s output_tokens=%s estimated_cost_usd=%s",
        current_request_id(),
        purpose,
        usage.model,
        ",".join(usage.provider_request_ids) or "unavailable",
        usage.latency_ms,
        usage.input_tokens,
        usage.cached_input_tokens,
        usage.output_tokens,
        usage.estimated_cost_usd,
    )


def _log_ai_failure(purpose: str, error: Exception) -> None:
    current_app.logger.warning(
        "ai_request_failed request_id=%s purpose=%s error_type=%s",
        current_request_id(),
        purpose,
        type(error).__name__,
    )


def _reservation_amount(purpose: str) -> Decimal:
    config_names = {
        "transaction": "AI_TRANSACTION_RESERVATION_USD",
        "receipt": "AI_RECEIPT_RESERVATION_USD",
        "assistant": "AI_ASSISTANT_RESERVATION_USD",
        "finance": "AI_FINANCE_RESERVATION_USD",
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
            # Flask-SQLAlchemy keeps objects after commit. Refresh the locked
            # row so repeated reservations cannot reuse a stale identity-map
            # value and accidentally exceed the configured budget.
            .execution_options(populate_existing=True)
        )
        if usage is None:
            raise RuntimeError("AI daily usage row could not be created")

        committed_and_reserved = (
            usage.estimated_cost_usd + usage.reserved_cost_usd
        )
        if committed_and_reserved + reservation_amount > daily_budget:
            db.session.rollback()
            current_app.logger.warning(
                "ai_budget_rejected request_id=%s purpose=%s "
                "committed_and_reserved_usd=%s requested_usd=%s "
                "daily_budget_usd=%s",
                current_request_id(),
                purpose,
                committed_and_reserved,
                reservation_amount,
                daily_budget,
            )
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
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(
            "ai_budget_reservation_failed request_id=%s purpose=%s "
            "error_type=%s",
            current_request_id(),
            purpose,
            type(error).__name__,
        )
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
            .execution_options(populate_existing=True)
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
            .execution_options(populate_existing=True)
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
    except Exception as error:
        _log_ai_failure("transaction", error)
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI transaction budget reconciliation failed"
            )
        raise

    complete_reservation(reservation, result.usage)
    _log_ai_completion("transaction", result.usage)
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
    except Exception as error:
        _log_ai_failure("receipt", error)
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI receipt budget reconciliation failed"
            )
        raise

    complete_reservation(reservation, result.usage)
    _log_ai_completion("receipt", result.usage)
    return result


def run_telegram_assistant_ai(
    text: str,
    *,
    user_id: int,
) -> AITelegramAssistantResult:
    clean_text = normalize_assistant_input(text)
    get_ai_model()
    get_openai_api_key()
    reservation = reserve_daily_budget("assistant")
    try:
        result = respond_to_telegram_message(
            clean_text,
            user_id=user_id,
        )
    except Exception as error:
        _log_ai_failure("telegram_assistant", error)
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI Telegram budget reconciliation failed"
            )
        raise

    complete_reservation(reservation, result.usage)
    _log_ai_completion("telegram_assistant", result.usage)
    return result


def run_finance_question_ai(
    question: str,
    *,
    user_id: int,
) -> AIFinanceAnswerResult:
    clean = normalize_finance_question(question)
    get_ai_model()
    get_openai_api_key()
    reservation = reserve_daily_budget("finance")
    try:
        result = answer_finance_question(clean, user_id=user_id)
    except Exception as error:
        _log_ai_failure("finance_question", error)
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI finance-question budget reconciliation failed"
            )
        raise
    complete_reservation(reservation, result.usage)
    _log_ai_completion("finance_question", result.usage)
    return result


def run_weekly_summary_ai(*, user_id: int) -> AIWeeklySummaryResult:
    get_ai_model()
    get_openai_api_key()
    reservation = reserve_daily_budget("assistant")
    try:
        result = build_weekly_finance_summary(user_id=user_id)
    except Exception as error:
        _log_ai_failure("weekly_summary", error)
        try:
            fail_reservation(reservation)
        except Exception:
            current_app.logger.exception(
                "AI weekly-summary budget reconciliation failed"
            )
        raise
    complete_reservation(reservation, result.usage)
    _log_ai_completion("weekly_summary", result.usage)
    return result
