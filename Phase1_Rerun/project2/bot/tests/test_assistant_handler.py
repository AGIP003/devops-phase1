import asyncio
from types import SimpleNamespace

import pytest
from telegram.ext import ConversationHandler

from bot.handlers import assistant


pytestmark = [pytest.mark.no_database, pytest.mark.external]


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


class FakeCallbackQuery:
    def __init__(self, data):
        self.data = data
        self.edits = []

    async def answer(self):
        return None

    async def edit_message_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


def _update(message, user_id=123):
    return SimpleNamespace(
        message=message,
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id),
    )


def _transaction_response():
    return {
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
    }


def test_finance_question_returns_bounded_ai_reply(monkeypatch):
    async def run_immediately(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(assistant.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        assistant,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "short-lived-token"},
    )
    monkeypatch.setattr(
        assistant,
        "request_telegram_assistant",
        lambda token, text: {
            "intent": "finance_education",
            "reply": "An emergency fund covers unexpected essential costs.",
            "transaction": None,
        },
    )

    message = FakeMessage("What is an emergency fund?")
    state = asyncio.run(
        assistant.assistant_message_handler(
            _update(message),
            SimpleNamespace(user_data={}),
        )
    )

    assert state == ConversationHandler.END
    assert "unexpected essential costs" in message.replies[-1][0]


def test_ai_transaction_requires_review_before_save(monkeypatch):
    saved = []

    async def run_immediately(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(assistant.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        assistant,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "short-lived-token"},
    )
    monkeypatch.setattr(
        assistant,
        "request_telegram_assistant",
        lambda token, text: _transaction_response(),
    )
    monkeypatch.setattr(
        assistant,
        "get_telegram_preferences",
        lambda token: {"default_payment_method": "m-pesa"},
    )

    def fake_create_transaction(*args):
        saved.append(args)
        return {
            "data": {
                "amount": "300.00",
                "description": "lunch",
                "category": "food",
                "payment_method": "m-pesa",
            }
        }

    monkeypatch.setattr(
        assistant,
        "create_transaction",
        fake_create_transaction,
    )

    message = FakeMessage("I spent 300 on lunch")
    context = SimpleNamespace(user_data={})
    state = asyncio.run(
        assistant.assistant_message_handler(_update(message), context)
    )

    assert state == ConversationHandler.END
    assert saved == []
    assert "nothing has been saved" in message.replies[-1][0]
    assert context.user_data["pending_ai_transaction"]["transaction"][
        "payment_method"
    ] == "m-pesa"

    query = FakeCallbackQuery("aitxn|save")
    asyncio.run(
        assistant.assistant_transaction_callback(
            SimpleNamespace(
                callback_query=query,
                effective_user=SimpleNamespace(id=123),
            ),
            context,
        )
    )

    assert len(saved) == 1
    assert saved[0][1] == "lunch"
    assert saved[0][2] == "300.00"
    assert "pending_ai_transaction" not in context.user_data
    assert "ai_transaction_access_token" not in context.user_data


def test_ai_failure_keeps_balance_available(monkeypatch):
    async def run_immediately(function, *args, **kwargs):
        return function(*args, **kwargs)

    balance_requests = []

    async def fake_balance(update, context):
        balance_requests.append(update.effective_message.text)

    monkeypatch.setattr(assistant.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        assistant,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "short-lived-token"},
    )
    monkeypatch.setattr(
        assistant,
        "request_telegram_assistant",
        lambda token, text: (_ for _ in ()).throw(
            RuntimeError("AI assistance is temporarily unavailable")
        ),
    )
    monkeypatch.setattr(assistant, "balance_handler", fake_balance)

    message = FakeMessage("What is my balance?")
    asyncio.run(
        assistant.assistant_message_handler(
            _update(message),
            SimpleNamespace(user_data={}),
        )
    )

    assert balance_requests == ["What is my balance?"]
    assert message.replies == []
