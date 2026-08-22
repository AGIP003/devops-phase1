from types import SimpleNamespace

from app.schemas import (
    AnalyticsAnswer,
    AnalyticsQuestionPlan,
    TelegramAssistantResponse,
)


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_telegram_assistant_requires_authentication(client):
    response = client.post(
        "/api/ai/telegram/respond",
        json={"text": "How do I add a transaction?"},
    )

    assert response.status_code == 401


def test_telegram_assistant_returns_only_validated_output(
    client,
    register_user,
    monkeypatch,
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


def test_analytics_question_returns_only_bounded_tool_evidence(
    client,
    register_user,
    monkeypatch,
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
    assert payload["data"]["totalCount"] == 2
    assert captured["question"].startswith("How often")
    assert isinstance(captured["user_id"], int)
    assert response.headers["Cache-Control"] == "private, no-store"
