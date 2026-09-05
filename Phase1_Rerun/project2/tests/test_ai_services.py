from decimal import Decimal
import json
from types import SimpleNamespace

import pytest
from flask import Flask

from app.schemas import (
    AnalyticsAnswer,
    AnalyticsQuestionPlan,
    ReceiptParseResult,
    TelegramAssistantResponse,
    TransactionParseResult,
    WeeklyFinanceNarrative,
)
from app.services import (
    ai_budget_service,
    ai_parser,
    receipt_parser,
    telegram_assistant,
    finance_assistant,
)
from app.services.ai_support import (
    AIInvalidResponseError,
    estimate_luna_cost,
    log_ai_provider_failure,
)
from app.services.image_validation import ValidatedImage


pytestmark = pytest.mark.no_database


class FakeResponses:
    def __init__(self, response):
        self.response = response
        self.request = None

    def parse(self, **kwargs):
        self.request = kwargs
        return self.response


class FakeClient:
    def __init__(self, response):
        self.responses = FakeResponses(response)


class SequenceResponses:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.requests = []

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        return next(self._responses)


class SequenceClient:
    def __init__(self, responses):
        self.responses = SequenceResponses(responses)


def response_with(extraction, *, status="completed"):
    return SimpleNamespace(
        _request_id="req_test_provider_123",
        status=status,
        output_parsed=extraction,
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=20,
            input_tokens_details=SimpleNamespace(cached_tokens=25),
        ),
    )


def test_weekly_narrative_accepts_sparse_but_honest_evidence():
    narrative = WeeklyFinanceNarrative.model_validate({
        "headline": "No recorded activity this week",
        "summary": "There is not enough recorded activity for a comparison.",
        "observations": [],
        "options": [],
        "caveats": ["Only recorded transactions are included."],
    })

    assert narrative.observations == []
    assert narrative.options == []


def test_analytics_plan_distinguishes_last_month_from_this_month():
    plan = AnalyticsQuestionPlan.model_validate({
        "tool": "search_spending",
        "period": "month",
        "offset": -1,
        "query": "Pamela Wandera",
    })

    assert plan.offset == -1
    assert plan.query == "Pamela Wandera"


def test_all_time_analytics_rejects_a_period_offset():
    with pytest.raises(ValueError, match="All-time analytics"):
        AnalyticsQuestionPlan.model_validate({
            "tool": "search_spending",
            "period": "all",
            "offset": -1,
            "query": "airtime",
        })


def test_weekly_data_summary_handles_an_empty_week(ai_app, monkeypatch):
    snapshots = iter([
        {
            "period": {
                "key": "week",
                "start": "2026-08-31",
                "end": "2026-09-06",
                "currency": "KES",
            },
            "income": "0.00",
            "recordedExpenses": "0.00",
            "confirmedFees": "0.00",
            "estimatedFees": "0.00",
            "totalExpenses": "0.00",
            "net": "0.00",
            "transactionCount": 0,
            "topExpenseCategories": [],
        },
        {
            "period": {
                "key": "week",
                "start": "2026-08-24",
                "end": "2026-08-30",
                "currency": "KES",
            },
            "income": "0.00",
            "recordedExpenses": "0.00",
            "confirmedFees": "0.00",
            "estimatedFees": "0.00",
            "totalExpenses": "0.00",
            "net": "0.00",
            "transactionCount": 0,
            "topExpenseCategories": [],
        },
    ])
    monkeypatch.setattr(
        finance_assistant,
        "build_calendar_cashflow",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        finance_assistant,
        "build_analytics_summary",
        lambda *args, **kwargs: {
            "commitments": {"totalMonthlyCommitted": "1200.00"},
            "goals": {"activeCount": 1, "remaining": "5000.00"},
            "debts": {},
            "upcoming": [],
            "adjustmentOpportunities": [],
            "recordedHistory": {"transactionCount": 0},
        },
    )

    with ai_app.app_context():
        narrative, snapshot = finance_assistant.build_weekly_data_summary(
            user_id=42,
        )

    assert narrative.headline == "No transactions recorded this week"
    assert "monthly commitments total" in narrative.observations[0]
    assert "active goal" in narrative.observations[1]
    assert snapshot["currentWeek"]["income"] == "0.00"


def test_weekly_data_summary_reviews_one_transaction_without_claiming_a_pattern(
    ai_app,
    monkeypatch,
):
    current = {
        "period": {
            "key": "week",
            "start": "2026-08-31",
            "end": "2026-09-06",
            "currency": "KES",
        },
        "income": "0.00",
        "recordedExpenses": "564.00",
        "confirmedFees": "10.00",
        "estimatedFees": "0.00",
        "totalExpenses": "574.00",
        "net": "-574.00",
        "transactionCount": 1,
        "topExpenseCategories": [
            {
                "category": "Utilities",
                "amount": "564.00",
                "transactionCount": 1,
            }
        ],
    }
    previous = {
        **current,
        "period": {
            **current["period"],
            "start": "2026-08-24",
            "end": "2026-08-30",
        },
        "recordedExpenses": "0.00",
        "confirmedFees": "0.00",
        "totalExpenses": "0.00",
        "net": "0.00",
        "transactionCount": 0,
        "topExpenseCategories": [],
    }
    snapshots = iter([current, previous])
    monkeypatch.setattr(
        finance_assistant,
        "build_calendar_cashflow",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        finance_assistant,
        "build_analytics_summary",
        lambda *args, **kwargs: {
            "commitments": {"totalMonthlyCommitted": "0.00"},
            "goals": {"activeCount": 0, "remaining": "0.00"},
            "debts": {},
            "upcoming": [],
            "adjustmentOpportunities": [],
            "recordedHistory": {"transactionCount": 1},
        },
    )

    with ai_app.app_context():
        narrative, _ = finance_assistant.build_weekly_data_summary(user_id=42)

    assert narrative.headline == "One transaction recorded this week"
    assert "Across 1 recorded transaction" in narrative.summary
    assert "not enough to establish a spending pattern" in narrative.caveats[0]


@pytest.fixture()
def ai_app():
    app = Flask(__name__)
    app.config.update(
        AI_REASONING_EFFORT="low",
        AI_TRANSACTION_MAX_OUTPUT_TOKENS=500,
        AI_RECEIPT_MAX_OUTPUT_TOKENS=1600,
        AI_ASSISTANT_MAX_OUTPUT_TOKENS=450,
        SECRET_KEY="test-secret-for-opaque-safety-identifiers",
    )
    return app


def test_luna_cost_separates_cached_input_tokens():
    cost = estimate_luna_cost(
        input_tokens=100,
        cached_input_tokens=25,
        output_tokens=20,
    )

    assert cost == Decimal("0.00003950")


@pytest.mark.parametrize(
    "schema",
    [TransactionParseResult, ReceiptParseResult, TelegramAssistantResponse],
)
def test_ai_json_schemas_do_not_emit_unsupported_regex_lookarounds(schema):
    encoded_schema = json.dumps(schema.model_json_schema())

    assert "(?" not in encoded_schema


def test_provider_failure_logging_exposes_diagnostics_not_sensitive_data(caplog):
    class ProviderError(Exception):
        status_code = 401
        request_id = "req_provider_failure_123"
        body = {
            "error": {
                "code": "invalid_api_key",
                "message": "Never log this provider message or sk-secret-value",
            }
        }

    with caplog.at_level("WARNING"):
        log_ai_provider_failure(
            ai_parser.logger,
            operation="transaction_parse",
            error=ProviderError(),
        )

    log_text = caplog.text
    assert "status_code=401" in log_text
    assert "provider_request_id=req_provider_failure_123" in log_text
    assert "error_code=invalid_api_key" in log_text
    assert "sk-secret-value" not in log_text


@pytest.mark.external
def test_transaction_parser_returns_validated_output(
    ai_app,
    monkeypatch,
):
    extraction = TransactionParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "kind": "expense",
            "amount": "250.00",
            "category": "transport",
            "description": "matatu fare",
            "currency": "KES",
            "confidence": 0.95,
            "needs_review": False,
        },
    })
    fake_client = FakeClient(response_with(extraction))
    monkeypatch.setattr(
        ai_parser,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        ai_parser,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context():
        result = ai_parser.parse_with_ai("250 matatu fare")

    assert result.extraction.transaction.category == "transport"
    assert result.usage.input_tokens == 100
    assert result.usage.provider_request_ids == ("req_test_provider_123",)
    assert fake_client.responses.request["store"] is False
    assert (
        fake_client.responses.request["max_output_tokens"]
        == 500
    )


@pytest.mark.external
def test_transaction_parser_rejects_noncanonical_category(
    ai_app,
    monkeypatch,
):
    extraction = TransactionParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "kind": "expense",
            "amount": "250.00",
            "category": "commuting",
            "description": "matatu fare",
            "currency": "KES",
            "confidence": 0.95,
            "needs_review": False,
        },
    })
    monkeypatch.setattr(
        ai_parser,
        "create_openai_client",
        lambda: FakeClient(response_with(extraction)),
    )
    monkeypatch.setattr(
        ai_parser,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context(), pytest.raises(
        AIInvalidResponseError,
        match="unsupported transaction category",
    ):
        ai_parser.parse_with_ai("250 matatu fare")


@pytest.mark.external
def test_receipt_parser_returns_validated_output(
    ai_app,
    monkeypatch,
):
    extraction = ReceiptParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "receipt": {
            "merchant": "Khetia Drapers",
            "total": "1200.00",
            "transaction_date": "2026-08-22",
            "currency": "KES",
            "suggested_category": "groceries",
            "items": [],
            "confidence": 0.91,
            "needs_review": False,
        },
    })
    fake_client = FakeClient(response_with(extraction))
    monkeypatch.setattr(
        receipt_parser,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        receipt_parser,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context():
        result = receipt_parser.parse_receipt_image(
            ValidatedImage(b"validated-image", "image/png")
        )

    assert result.extraction.receipt.total == Decimal("1200.00")
    assert result.usage.output_tokens == 20
    assert fake_client.responses.request["store"] is False
    assert "instructions" in fake_client.responses.request


@pytest.mark.external
def test_receipt_parser_rejects_incomplete_provider_response(
    ai_app,
    monkeypatch,
):
    monkeypatch.setattr(
        receipt_parser,
        "create_openai_client",
        lambda: FakeClient(response_with(None, status="incomplete")),
    )
    monkeypatch.setattr(
        receipt_parser,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context(), pytest.raises(
        AIInvalidResponseError,
        match="status 'incomplete'",
    ):
        receipt_parser.parse_receipt_image(
            ValidatedImage(b"validated-image", "image/png")
        )


def test_invalid_transaction_input_spends_no_budget(monkeypatch):
    def forbidden_reservation(purpose):
        raise AssertionError("Invalid input must not reserve AI budget")

    monkeypatch.setattr(
        ai_budget_service,
        "reserve_daily_budget",
        forbidden_reservation,
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        ai_budget_service.run_transaction_ai("   ")


def test_unvalidated_receipt_spends_no_budget(monkeypatch):
    def forbidden_reservation(purpose):
        raise AssertionError("Invalid input must not reserve AI budget")

    monkeypatch.setattr(
        ai_budget_service,
        "reserve_daily_budget",
        forbidden_reservation,
    )

    with pytest.raises(TypeError, match="must be validated"):
        ai_budget_service.run_receipt_ai(b"raw-user-input")


@pytest.mark.external
def test_telegram_assistant_returns_validated_transaction(
    ai_app,
    monkeypatch,
):
    parsed = TelegramAssistantResponse.model_validate({
        "intent": "transaction",
        "reply": "I found a possible transaction.",
        "transaction": {
            "kind": "expense",
            "amount": "300.00",
            "category": "food",
            "description": "lunch",
            "currency": "KES",
            "confidence": 0.92,
            "needs_review": False,
        },
    })
    fake_client = FakeClient(response_with(parsed))
    monkeypatch.setattr(
        telegram_assistant,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        telegram_assistant,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context():
        result = telegram_assistant.respond_to_telegram_message(
            "I spent 300 on lunch",
            user_id=42,
        )

    request = fake_client.responses.request
    assert result.response.transaction.category == "food"
    assert request["store"] is False
    assert request["safety_identifier"] != "42"
    assert len(request["safety_identifier"]) == 64
    assert request["max_output_tokens"] == 450


@pytest.mark.parametrize(
    "text",
    [
        "What is Docker?",
        "Who is Edgar Obare?",
        "Write Python code for me",
    ],
)
def test_telegram_assistant_marks_unrelated_topics_out_of_scope(text):
    assert telegram_assistant.is_message_in_scope(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "Hey",
        "How do I add a transaction?",
        "What is an emergency fund?",
        "How much did I spend on airtime this month?",
        "Show my budgets and goals",
        "How much have I spent this month?",
        "I paid KES 300 for lunch",
        "Show my subscription fees",
    ],
)
def test_telegram_assistant_accepts_app_and_finance_topics(text):
    assert telegram_assistant.is_message_in_scope(text) is True


def test_unrelated_telegram_message_spends_no_ai_budget(monkeypatch):
    def forbidden_reservation(purpose):
        raise AssertionError("Unrelated text must not reserve AI budget")

    monkeypatch.setattr(
        ai_budget_service,
        "reserve_daily_budget",
        forbidden_reservation,
    )

    with pytest.raises(telegram_assistant.AssistantOutOfScopeError):
        ai_budget_service.run_telegram_assistant_ai(
            "What is Docker?",
            user_id=1,
        )


@pytest.mark.external
def test_unsupported_ai_wording_is_replaced(ai_app, monkeypatch):
    parsed = TelegramAssistantResponse.model_validate({
        "intent": "unsupported",
        "reply": "Docker packages applications into containers.",
        "transaction": None,
    })
    fake_client = FakeClient(response_with(parsed))
    monkeypatch.setattr(
        telegram_assistant,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        telegram_assistant,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context():
        result = telegram_assistant.respond_to_telegram_message(
            "Is a software subscription a recurring expense?",
            user_id=42,
        )

    assert result.response.reply == telegram_assistant.OUT_OF_SCOPE_REPLY


def test_invalid_assistant_input_spends_no_budget(monkeypatch):
    def forbidden_reservation(purpose):
        raise AssertionError("Invalid input must not reserve AI budget")

    monkeypatch.setattr(
        ai_budget_service,
        "reserve_daily_budget",
        forbidden_reservation,
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        ai_budget_service.run_telegram_assistant_ai("  ", user_id=1)


@pytest.mark.external
def test_finance_assistant_uses_one_allowlisted_owned_tool(ai_app, monkeypatch):
    plan = AnalyticsQuestionPlan.model_validate({
        "tool": "search_spending",
        "period": "month",
        "query": "airtime",
        "reduction_percent": None,
    })
    answer = AnalyticsAnswer.model_validate({
        "answer": "You recorded airtime twice this month.",
        "evidence": ["2 matches totalling KES 350.00"],
        "caveats": ["Only recorded transactions are included."],
    })
    fake_client = SequenceClient([
        response_with(plan),
        response_with(answer),
    ])
    captured = {}
    monkeypatch.setattr(
        finance_assistant,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        finance_assistant,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    def fake_execute(user_id, selected_plan, *, today=None):
        captured.update({"user_id": user_id, "plan": selected_plan})
        return {
            "query": "airtime",
            "period": {"start": "2026-08-01", "end": "2026-08-31"},
            "totalCount": 2,
            "totalAmount": "350.00",
            "series": [],
        }

    monkeypatch.setattr(
        finance_assistant,
        "execute_analytics_tool",
        fake_execute,
    )

    with ai_app.app_context():
        result = finance_assistant.answer_finance_question(
            "How often did I buy airtime this month?",
            user_id=42,
        )

    assert captured["user_id"] == 42
    assert captured["plan"].tool.value == "search_spending"
    assert result.answer.answer.startswith("You recorded airtime")
    assert result.usage.input_tokens == 200
    assert len(fake_client.responses.requests) == 2
    assert all(request["store"] is False for request in fake_client.responses.requests)
    assert "42" not in fake_client.responses.requests[0]["input"]
