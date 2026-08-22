from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.schemas import ReceiptParseResult, TransactionParseResult
from app.services import ai_budget_service, ai_parser, receipt_parser
from app.services.ai_support import (
    AIInvalidResponseError,
    estimate_luna_cost,
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


def response_with(extraction, *, status="completed"):
    return SimpleNamespace(
        status=status,
        output_parsed=extraction,
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=20,
            input_tokens_details=SimpleNamespace(cached_tokens=25),
        ),
    )


@pytest.fixture()
def ai_app():
    app = Flask(__name__)
    app.config.update(
        AI_REASONING_EFFORT="low",
        AI_TRANSACTION_MAX_OUTPUT_TOKENS=500,
        AI_RECEIPT_MAX_OUTPUT_TOKENS=1600,
    )
    return app


def test_luna_cost_separates_cached_input_tokens():
    cost = estimate_luna_cost(
        input_tokens=100,
        cached_input_tokens=25,
        output_tokens=20,
    )

    assert cost == Decimal("0.00003950")


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
    assert fake_client.responses.request["store"] is False
    assert (
        fake_client.responses.request["max_output_tokens"]
        == 500
    )


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
