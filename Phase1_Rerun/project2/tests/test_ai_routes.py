import pytest
from types import SimpleNamespace

from app.schemas import (
    AnalyticsAnswer,
    AnalyticsQuestionPlan,
    TelegramAssistantResponse,
    WeeklyFinanceNarrative,
)
from app.services.ai_support import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
)


pytestmark = pytest.mark.external


@pytest.fixture()
def enabled_ai(app, monkeypatch):
    """Enable AI for tests that replace the external provider boundary."""
    monkeypatch.setitem(
        app.config,
        "AI_FALLBACK_ENABLED",
        True,
    )
    return app

def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_telegram_assistant_requires_authentication(client):
    response = client.post(
        "/api/ai/telegram/respond",
        json={"text": "How do I add a transaction?"},
    )

    assert response.status_code == 401


@pytest.mark.critical
def test_telegram_assistant_returns_only_validated_output(
    client,
    register_user,
    monkeypatch,
    enabled_ai,
):
    from app import ai_routes

    owner = register_user("assistant-owner", "assistant@example.com")
    captured = {}
    parsed = TelegramAssistantResponse.model_validate({
        "intent": "help",
        "reply": "Use /add AMOUNT DESCRIPTION to prepare a transaction.",
        "transaction": None,
    })

    def fake_run(text, *, user_id):
        captured.update({"text": text, "user_id": user_id})
        return SimpleNamespace(response=parsed)

    monkeypatch.setattr(
        ai_routes,
        "run_telegram_assistant_ai",
        fake_run,
    )

    response = client.post(
        "/api/ai/telegram/respond",
        headers=authorization(owner["token"]),
        json={"text": "How do I add a transaction?"},
    )

    assert response.status_code == 200
    assert response.get_json() == parsed.model_dump(mode="json")
    assert captured["text"] == "How do I add a transaction?"
    assert isinstance(captured["user_id"], int)
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "private, no-store"


def test_telegram_assistant_returns_fixed_reply_for_unrelated_topic(
    client,
    register_user,
    monkeypatch,
    enabled_ai,
):
    from app import ai_routes
    from app.services.telegram_assistant import (
        AssistantOutOfScopeError,
        OUT_OF_SCOPE_REPLY,
    )

    owner = register_user("scope-owner", "scope-owner@example.com")

    def reject_unrelated(*args, **kwargs):
        raise AssistantOutOfScopeError("Outside application scope")

    monkeypatch.setattr(
        ai_routes,
        "run_telegram_assistant_ai",
        reject_unrelated,
    )

    response = client.post(
        "/api/ai/telegram/respond",
        headers=authorization(owner["token"]),
        json={"text": "What is Docker?"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "intent": "unsupported",
        "reply": OUT_OF_SCOPE_REPLY,
        "transaction": None,
    }


def test_disabled_ai_returns_service_unavailable(
    app,
    client,
    register_user,
    monkeypatch,
):
    owner = register_user("disabled-ai", "disabled-ai@example.com")
    monkeypatch.setitem(app.config, "AI_FALLBACK_ENABLED", False)

    response = client.post(
        "/api/ai/telegram/respond",
        headers=authorization(owner["token"]),
        json={"text": "hello"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "AI assistance disabled"


@pytest.mark.critical
def test_ai_provider_error_returns_correlated_safe_request_id(
    client,
    register_user,
    monkeypatch,
    enabled_ai,
):
    from app import ai_routes

    owner = register_user("provider-error", "provider-error@example.com")

    def unavailable(*args, **kwargs):
        raise AIServiceUnavailableError("AI assistance is temporarily unavailable")

    monkeypatch.setattr(ai_routes, "run_telegram_assistant_ai", unavailable)
    response = client.post(
        "/api/ai/telegram/respond",
        headers=authorization(owner["token"]),
        json={"text": "hello"},
    )

    payload = response.get_json()
    assert response.status_code == 503
    assert payload["requestId"] == response.headers["X-Request-ID"]
    assert "provider" not in payload.get("message", "").lower()


def test_analytics_question_returns_only_bounded_tool_evidence(
    client,
    register_user,
    monkeypatch,
    enabled_ai,
):
    from app import ai_routes

    owner = register_user("finance-ai", "finance-ai@example.com")
    captured = {}
    plan = AnalyticsQuestionPlan.model_validate({
        "tool": "search_spending",
        "period": "month",
        "query": "airtime",
    })
    answer = AnalyticsAnswer.model_validate({
        "answer": "You recorded airtime twice.",
        "evidence": ["2 recorded matches"],
        "caveats": ["Only recorded data is included."],
    })

    def fake_run(question, *, user_id):
        captured.update({"question": question, "user_id": user_id})
        return SimpleNamespace(
            plan=plan,
            answer=answer,
            tool_result={"totalCount": 2, "totalAmount": "350.00"},
        )

    monkeypatch.setattr(ai_routes, "run_finance_question_ai", fake_run)
    response = client.post(
        "/api/ai/analytics/questions",
        headers=authorization(owner["token"]),
        json={"question": "How often did I buy airtime this month?"},
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["operation"] == "search_spending"
    assert payload["periodOffset"] == 0
    assert payload["data"]["totalCount"] == 2
    assert captured["question"].startswith("How often")
    assert isinstance(captured["user_id"], int)
    assert response.headers["Cache-Control"] == "private, no-store"


@pytest.mark.critical
def test_weekly_summary_falls_back_to_verified_data(
    client,
    register_user,
    monkeypatch,
    enabled_ai,
):
    from app import ai_routes

    owner = register_user("weekly-owner", "weekly-owner@example.com")
    narrative = WeeklyFinanceNarrative(
        headline="No recorded cash-flow activity this week",
        summary="The current week contains no recorded income or expenses.",
        observations=[],
        options=["Check whether this week's transactions are recorded."],
        caveats=["Only recorded transactions are included."],
    )
    snapshot = {
        "currentWeek": {
            "period": {
                "key": "week",
                "start": "2026-08-31",
                "end": "2026-09-06",
                "currency": "KES",
            },
        },
        "previousWeek": {},
    }

    def invalid_ai(*args, **kwargs):
        raise AIInvalidResponseError("AI returned an invalid weekly summary")

    monkeypatch.setattr(ai_routes, "run_weekly_summary_ai", invalid_ai)
    monkeypatch.setattr(
        ai_routes,
        "build_weekly_data_summary",
        lambda **kwargs: (narrative, snapshot),
    )

    response = client.post(
        "/api/ai/analytics/weekly-summary",
        headers=authorization(owner["token"]),
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["generationMode"] == "data_summary"
    assert response.get_json()["narrative"]["observations"] == []
    assert response.headers["Cache-Control"] == "private, no-store"
