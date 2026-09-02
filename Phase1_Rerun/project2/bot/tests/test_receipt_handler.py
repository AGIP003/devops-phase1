import asyncio
from types import SimpleNamespace

import pytest
from telegram.ext import ConversationHandler

from app.services.image_validation import ValidatedImage
from bot.handlers import receipts


pytestmark = [pytest.mark.no_database, pytest.mark.external]


class FakeStatus:
    def __init__(self):
        self.edits = []

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []
        self.status = FakeStatus()

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))
        return self.status


class FakeCallbackQuery:
    def __init__(self, data):
        self.data = data
        self.edits = []

    async def answer(self):
        return None

    async def edit_message_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


def _receipt_preview(currency="KES"):
    return {
        "can_parse": True,
        "reason": None,
        "receipt": {
            "merchant": "Khetia Drapers",
            "total": "1200.00",
            "transaction_date": "2026-08-22",
            "currency": currency,
            "suggested_category": "groceries",
            "items": [],
            "confidence": 0.91,
            "needs_review": False,
        },
    }


def test_receipt_requires_human_fields_and_confirmation(monkeypatch):
    saved = []

    async def run_immediately(function, *args, **kwargs):
        return function(*args, **kwargs)

    async def fake_download(message):
        return ValidatedImage(b"validated-image", "image/png")

    monkeypatch.setattr(receipts.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        receipts,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "short-lived-token"},
    )
    monkeypatch.setattr(receipts, "download_largest_receipt", fake_download)
    monkeypatch.setattr(
        receipts,
        "preview_receipt",
        lambda token, data, media_type: _receipt_preview(),
    )

    def fake_create_transaction(*args):
        saved.append(args)
        return {
            "data": {
                "amount": "1200.00",
                "description": "weekly groceries",
                "category": "groceries",
            }
        }

    monkeypatch.setattr(
        receipts,
        "create_transaction",
        fake_create_transaction,
    )

    message = FakeMessage()
    context = SimpleNamespace(user_data={})
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=123),
    )

    state = asyncio.run(receipts.handle_receipt_photo(update, context))
    assert state == receipts.RECEIPT_DESCRIPTION
    assert saved == []
    assert "description is required" in message.status.edits[-1][0]
    assert "validated-image" not in str(context.user_data)

    state = asyncio.run(
        receipts.receipt_description_handler(
            SimpleNamespace(message=FakeMessage("Weekly groceries")),
            context,
        )
    )
    assert state == receipts.RECEIPT_CATEGORY
    assert saved == []

    category_query = FakeCallbackQuery("receiptcat|groceries")
    state = asyncio.run(
        receipts.receipt_category_callback(
            SimpleNamespace(callback_query=category_query),
            context,
        )
    )
    assert state == receipts.RECEIPT_PAYMENT

    payment_query = FakeCallbackQuery("receiptpm|m-pesa")
    state = asyncio.run(
        receipts.receipt_payment_callback(
            SimpleNamespace(callback_query=payment_query),
            context,
        )
    )
    assert state == receipts.RECEIPT_CONFIRM
    assert saved == []
    assert "still not saved" in payment_query.edits[-1][0]

    save_query = FakeCallbackQuery("receiptsave")
    state = asyncio.run(
        receipts.receipt_save_callback(
            SimpleNamespace(callback_query=save_query),
            context,
        )
    )

    assert state == ConversationHandler.END
    assert len(saved) == 1
    assert saved[0][1] == "Weekly groceries"
    assert saved[0][2] == "1200.00"
    assert saved[0][3] == "groceries"
    assert saved[0][6] == "m-pesa"
    assert "pending_receipt" not in context.user_data
    assert "receipt_access_token" not in context.user_data


def test_foreign_currency_receipt_is_not_saved_as_kes(monkeypatch):
    async def run_immediately(function, *args, **kwargs):
        return function(*args, **kwargs)

    async def fake_download(message):
        return ValidatedImage(b"validated-image", "image/png")

    monkeypatch.setattr(receipts.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        receipts,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "short-lived-token"},
    )
    monkeypatch.setattr(receipts, "download_largest_receipt", fake_download)
    monkeypatch.setattr(
        receipts,
        "preview_receipt",
        lambda token, data, media_type: _receipt_preview("USD"),
    )

    message = FakeMessage()
    context = SimpleNamespace(user_data={})
    state = asyncio.run(
        receipts.handle_receipt_photo(
            SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=123),
            ),
            context,
        )
    )

    assert state == ConversationHandler.END
    assert "not saved" in message.status.edits[-1][0]
    assert "Saving this amount as KES" in message.status.edits[-1][0]
    assert context.user_data == {}
