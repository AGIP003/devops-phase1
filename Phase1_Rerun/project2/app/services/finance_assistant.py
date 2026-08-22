from __future__ import annotations

import hmac
import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256
from time import perf_counter

from flask import current_app
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from app.schemas import (
    AnalyticsAnswer,
    AnalyticsQuestionPlan,
    WeeklyFinanceNarrative,
)
from app.services.ai_support import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
    AIUsageMetadata,
    build_usage_metadata,
    combine_usage_metadata,
    create_openai_client,
    get_ai_model,
)
from app.services.analytics_service import build_calendar_cashflow
from app.services.analytics_tools import execute_analytics_tool


logger = logging.getLogger(__name__)
MAX_FINANCE_QUESTION_CHARACTERS = 500

PLAN_PROMPT = """
Choose exactly one read-only Moneytiqx analytics operation for the user's
question. Never produce SQL and never request or infer a user ID.

Operations:
- search_spending: count or total purchases matching any description or merchant.
- compare_periods: compare current and previous week, month or year.
- get_fee_summary: confirmed and estimated provider or financing fees.
- get_cashflow_summary: income, spending, fees and net cash flow.
- get_commitment_pressure: bills, subscriptions, debt schedules and goal needs.
- get_goal_progress: recorded savings-goal position.
- get_debt_position: recorded debt balance, repayments and fees.
- run_what_if_scenario: illustrate reducing one searched spending area.

Interpret "this week", "this month" and "this year" as week, month and year.
Use month when no period is stated. Preserve the user's search wording in query.
This plan only reads data; it must never create, edit or delete anything.
""".strip()

ANSWER_PROMPT = """
Explain one verified Moneytiqx analytics result. The JSON data came from
ownership-filtered SQLAlchemy queries and is the only source of numeric facts.

Rules:
- Never invent a value or claim access to data absent from the JSON.
- Clearly distinguish confirmed fees from estimated fees.
- State the date range used.
- For an empty match, say no matching recorded transactions were found; do not
  claim the user never made that purchase.
- Present options and trade-offs, not commands or guaranteed outcomes.
- Do not provide investment, legal or tax instructions.
- Do not claim that anything was saved or changed.
- Keep the answer concise and useful.
""".strip()

WEEKLY_PROMPT = """
Write an opt-in weekly personal-finance review from the supplied verified JSON.
Compare the current and previous week, distinguish confirmed from estimated
fees, and give practical options without shame or certainty. Do not provide
investment, legal or tax instructions. Do not claim any automatic change was
made. If data is sparse, make that limitation prominent.
""".strip()


@dataclass(frozen=True, slots=True)
class AIFinanceAnswerResult:
    plan: AnalyticsQuestionPlan
    answer: AnalyticsAnswer
    tool_result: dict[str, object]
    usage: AIUsageMetadata


@dataclass(frozen=True, slots=True)
class AIWeeklySummaryResult:
    narrative: WeeklyFinanceNarrative
    snapshot: dict[str, object]
    usage: AIUsageMetadata


def normalize_finance_question(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Finance question must be text")
    clean = " ".join(value.strip().split())
    if len(clean) < 2:
        raise ValueError("Finance question must contain at least 2 characters")
    if len(clean) > MAX_FINANCE_QUESTION_CHARACTERS:
        raise ValueError(
            f"Finance question cannot exceed {MAX_FINANCE_QUESTION_CHARACTERS} characters"
        )
    return clean


def _safety_identifier(user_id: int) -> str:
    return hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        f"finance-assistant:{user_id}".encode("utf-8"),
        sha256,
    ).hexdigest()


def _parse_response(
    *,
    client,
    model: str,
    instructions: str,
    input_text: str,
    text_format,
    user_id: int,
):
    started_at = perf_counter()
    response = client.responses.parse(
        model=model,
        instructions=instructions,
        input=input_text,
        text_format=text_format,
        reasoning={"effort": current_app.config["AI_REASONING_EFFORT"]},
        max_output_tokens=current_app.config["AI_ASSISTANT_MAX_OUTPUT_TOKENS"],
        safety_identifier=_safety_identifier(user_id),
        store=False,
    )
    if response.status != "completed" or response.output_parsed is None:
        raise AIInvalidResponseError("AI finance response was incomplete")
    return response.output_parsed, build_usage_metadata(
        response,
        model=model,
        started_at=started_at,
    )


def answer_finance_question(
    question: str,
    *,
    user_id: int,
    today: date | None = None,
) -> AIFinanceAnswerResult:
    clean = normalize_finance_question(question)
    model = get_ai_model()
    client = create_openai_client()
    try:
        plan, plan_usage = _parse_response(
            client=client,
            model=model,
            instructions=PLAN_PROMPT,
            input_text=clean,
            text_format=AnalyticsQuestionPlan,
            user_id=user_id,
        )
        tool_result = execute_analytics_tool(
            user_id,
            plan,
            today=today,
        )
        answer_input = json.dumps(
            {"question": clean, "plan": plan.model_dump(mode="json"), "data": tool_result},
            separators=(",", ":"),
        )
        answer, answer_usage = _parse_response(
            client=client,
            model=model,
            instructions=ANSWER_PROMPT,
            input_text=answer_input,
            text_format=AnalyticsAnswer,
            user_id=user_id,
        )
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError) as error:
        logger.warning(
            "AI finance assistant unavailable",
            extra={"error_type": type(error).__name__},
        )
        raise AIServiceUnavailableError(
            "AI financial analysis is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        raise AIInvalidResponseError(
            "AI returned an invalid finance operation"
        ) from error

    return AIFinanceAnswerResult(
        plan=plan,
        answer=answer,
        tool_result=tool_result,
        usage=combine_usage_metadata(plan_usage, answer_usage),
    )


def build_weekly_finance_summary(
    *,
    user_id: int,
    today: date | None = None,
) -> AIWeeklySummaryResult:
    anchor = today or date.today()
    current = build_calendar_cashflow(user_id, "week", anchor=anchor)
    current_start = date.fromisoformat(current["period"]["start"])
    previous = build_calendar_cashflow(
        user_id,
        "week",
        anchor=current_start - timedelta(days=1),
    )
    snapshot = {"currentWeek": current, "previousWeek": previous}
    model = get_ai_model()
    client = create_openai_client()
    try:
        narrative, usage = _parse_response(
            client=client,
            model=model,
            instructions=WEEKLY_PROMPT,
            input_text=json.dumps(snapshot, separators=(",", ":")),
            text_format=WeeklyFinanceNarrative,
            user_id=user_id,
        )
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError) as error:
        raise AIServiceUnavailableError(
            "AI weekly summary is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        raise AIInvalidResponseError(
            "AI returned an invalid weekly summary"
        ) from error
    return AIWeeklySummaryResult(
        narrative=narrative,
        snapshot=snapshot,
        usage=usage,
    )
