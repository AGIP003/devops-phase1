from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.schemas import ProviderImportParseResult
from app.services import provider_import_ai


pytestmark = [pytest.mark.no_database, pytest.mark.external]


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


def _response_with(extraction):
    return SimpleNamespace(
        _request_id="req_provider_import_123",
        status="completed",
        output_parsed=extraction,
        usage=SimpleNamespace(
            input_tokens=120,
            output_tokens=45,
            input_tokens_details=SimpleNamespace(cached_tokens=20),
        ),
    )


@pytest.fixture()
def ai_app():
    app = Flask(__name__)
    app.config.update(
        AI_REASONING_EFFORT="low",
        AI_TRANSACTION_MAX_OUTPUT_TOKENS=500,
    )
    return app


def test_minimized_provider_message_removes_unnecessary_sensitive_fields():
    message = (
        "ABCDEFGHIJK Confirmed. Ksh 564 successfully paid to SAMPLE STORE "
        "account 123456 on 03/09/26 at 02:19 PM. Fee: Ksh 10.00. "
        "Bal: Ksh 17700.5. Call 0700000000. https://example.test/path"
    )

    minimized = provider_import_ai.minimize_provider_message(message)

    assert "ABCDEFGHIJK" in minimized
    assert "Ksh 564" in minimized
    assert "SAMPLE STORE" in minimized
    assert "Fee: Ksh 10.00" in minimized
    assert "123456" not in minimized
    assert "17700.5" not in minimized
    assert "0700000000" not in minimized
    assert "https://" not in minimized


def test_minimized_provider_message_removes_nine_digit_airtel_line():
    message = (
        "29148245185 Successful. Airtime top up for line 101784609 "
        "of Ksh 20 is successful. Bal: Ksh 520.5."
    )

    minimized = provider_import_ai.minimize_provider_message(message)

    assert "29148245185" in minimized
    assert "101784609" not in minimized
    assert "Ksh 20" in minimized


def test_safe_format_signature_contains_structure_not_message_values():
    message = (
        "Q3QRSOZ29C6 Confirmed. Ksh 564 successfully paid to SAMPLE STORE "
        "on 03/09/26 at 02:19 PM. Fee: Ksh 10.00. Bal: Ksh 17700.5."
    )

    signature = provider_import_ai.safe_format_signature(message)

    assert signature == "airtel:confirmed:successful:paid_to:fee:balance"
    assert "SAMPLE" not in signature
    assert "564" not in signature
    assert "Q3QRSOZ29C6" not in signature


def test_ai_provider_import_returns_validated_import_evidence(
    ai_app,
    monkeypatch,
):
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "Q3QRSOZ29C6",
            "occurred_at": "2026-09-03T14:19:00+03:00",
            "amount": "564.00",
            "currency": "KES",
            "flow_direction": "money_out",
            "description": "Paid SAMPLE PAYMENT C2B",
            "counterparty": "SAMPLE PAYMENT C2B",
            "fee": "10.00",
            "provider_transaction_type": "merchant_payment",
            "confidence": 0.91,
            "needs_review": True,
        },
    })
    fake_client = FakeClient(_response_with(extraction))
    monkeypatch.setattr(
        provider_import_ai,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        provider_import_ai,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )
    message = (
        "Q3QRSOZ29C6 Confirmed. Ksh 564 completed to SAMPLE PAYMENT C2B "
        "on 03/09/26 at 02:19 PM. Fee: Ksh 10.00. Bal: Ksh 17700.5."
    )

    with ai_app.app_context():
        result = provider_import_ai.parse_provider_message_with_ai(message)

    assert result.parsed is not None
    assert result.parsed.amount == Decimal("564.00")
    assert result.parsed.flow_direction is provider_import_ai.ProviderFlowDirection.MONEY_OUT
    assert result.parsed.resulting_balance is None
    assert result.extraction.transaction.needs_review is True
    assert fake_client.responses.request["store"] is False
    assert "17700.5" not in fake_client.responses.request["input"]


def test_ai_provider_import_rejects_reference_not_present_in_message(
    ai_app,
    monkeypatch,
):
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "ABCDEFGHIJK",
            "occurred_at": "2026-09-03T14:19:00+03:00",
            "amount": "564.00",
            "currency": "KES",
            "flow_direction": "money_out",
            "description": "Paid SAMPLE PAYMENT C2B",
            "counterparty": "SAMPLE PAYMENT C2B",
            "fee": "10.00",
            "provider_transaction_type": "merchant_payment",
            "confidence": 0.91,
            "needs_review": True,
        },
    })
    fake_client = FakeClient(_response_with(extraction))
    monkeypatch.setattr(
        provider_import_ai,
        "create_openai_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        provider_import_ai,
        "get_ai_model",
        lambda: "gpt-5.6-luna",
    )

    with ai_app.app_context(), pytest.raises(
        provider_import_ai.AIInvalidResponseError,
        match="mismatched provider reference",
    ):
        provider_import_ai.parse_provider_message_with_ai(
            "Q3QRSOZ29C6 Confirmed. Ksh 564 completed to SAMPLE PAYMENT "
            "on 03/09/26 at 02:19 PM. Fee: Ksh 10.00."
        )


def test_ai_provider_import_rejects_counterparty_as_message_provider(
    ai_app,
    monkeypatch,
):
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "UI5IU5CE3F",
            "occurred_at": "2026-09-05T23:21:00+03:00",
            "amount": "17500.00",
            "currency": "KES",
            "flow_direction": "money_in",
            "description": "Received from another wallet",
            "counterparty": "SAMPLE WALLET",
            "fee": None,
            "provider_transaction_type": "received_money",
            "confidence": 0.89,
            "needs_review": True,
        },
    })
    monkeypatch.setattr(
        provider_import_ai,
        "create_openai_client",
        lambda: FakeClient(_response_with(extraction)),
    )
    monkeypatch.setattr(provider_import_ai, "get_ai_model", lambda: "gpt-5.6-luna")

    with ai_app.app_context(), pytest.raises(
        provider_import_ai.AIInvalidResponseError,
        match="provider that conflicts",
    ):
        provider_import_ai.parse_provider_message_with_ai(
            "UI5IU5CE3F Confirmed. You have received Ksh17,500.00 from "
            "AIRTEL MONEY - SAMPLE USER 101784609 on 5/9/26 at 11:21 PM "
            "New M-PESA balance is Ksh17,500.00."
        )


def test_ai_provider_import_rejects_flow_opposite_to_explicit_wording(
    ai_app,
    monkeypatch,
):
    extraction = ProviderImportParseResult.model_validate({
        "can_parse": True,
        "reason": None,
        "transaction": {
            "provider": "airtel_money",
            "external_reference": "Q3QRSOZ29C6",
            "occurred_at": "2026-09-03T14:19:00+03:00",
            "amount": "564.00",
            "currency": "KES",
            "flow_direction": "money_in",
            "description": "Paid SAMPLE STORE",
            "counterparty": "SAMPLE STORE",
            "fee": "10.00",
            "provider_transaction_type": "merchant_payment",
            "confidence": 0.91,
            "needs_review": True,
        },
    })
    monkeypatch.setattr(
        provider_import_ai,
        "create_openai_client",
        lambda: FakeClient(_response_with(extraction)),
    )
    monkeypatch.setattr(provider_import_ai, "get_ai_model", lambda: "gpt-5.6-luna")

    with ai_app.app_context(), pytest.raises(
        provider_import_ai.AIInvalidResponseError,
        match="direction that conflicts",
    ):
        provider_import_ai.parse_provider_message_with_ai(
            "Q3QRSOZ29C6 Confirmed. Ksh 564 successfully paid to SAMPLE "
            "STORE on 03/09/26 at 02:19 PM. Fee: Ksh 10.00."
        )
