import asyncio
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from bot.handlers import import_message


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


def test_plain_provider_message_starts_import_without_command(monkeypatch):
    captured = {}

    async def fake_start(update, context, raw_message, **kwargs):
        captured["message"] = raw_message
        captured["fallback_to_welcome"] = kwargs["fallback_to_welcome"]
        return import_message.IMPORT_DESCRIPTION

    monkeypatch.setattr(import_message, "_start_import", fake_start)
    message = FakeMessage(
        "29813220000 Successful. Airtime top up of Ksh 300 "
        "to 0700000000. Bal: Ksh 828.5."
    )

    state = asyncio.run(
        import_message.automatic_import_handler(
            SimpleNamespace(message=message),
            SimpleNamespace(user_data={}),
        )
    )

    assert state == import_message.IMPORT_DESCRIPTION
    assert captured["message"].startswith("29813220000 Successful.")
    assert captured["fallback_to_welcome"] is True


def test_ordinary_text_continues_to_welcome_handler(monkeypatch):
    welcomed = []

    async def fake_welcome(update, context):
        welcomed.append(update.message.text)

    monkeypatch.setattr(import_message, "welcome_handler", fake_welcome)
    message = FakeMessage("hello there")

    state = asyncio.run(
        import_message.automatic_import_handler(
            SimpleNamespace(message=message),
            SimpleNamespace(user_data={}),
        )
    )

    assert state == ConversationHandler.END
    assert welcomed == ["hello there"]


def test_provider_like_text_that_fails_full_parse_returns_to_welcome(monkeypatch):
    welcomed = []

    async def run_immediately(function, *args):
        return function(*args)

    async def fake_welcome(update, context):
        welcomed.append(update.message.text)

    def reject_preview(token, message):
        raise import_message.UnsupportedProviderMessageError(
            "Unsupported provider message"
        )

    monkeypatch.setattr(import_message.asyncio, "to_thread", run_immediately)
    monkeypatch.setattr(
        import_message,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "temporary-token"},
    )
    monkeypatch.setattr(
        import_message,
        "get_telegram_preferences",
        lambda token: {"category_aliases": {}},
    )
    monkeypatch.setattr(import_message, "preview_transaction_import", reject_preview)
    monkeypatch.setattr(import_message, "welcome_handler", fake_welcome)
    message = FakeMessage("ABCDEFGHIJK. ordinary text after a provider-like prefix")
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=123),
    )

    state = asyncio.run(
        import_message.automatic_import_handler(
            update,
            SimpleNamespace(user_data={}),
        )
    )

    assert state == ConversationHandler.END
    assert welcomed == [message.text]


def test_failed_airtel_notice_is_silently_ignored(monkeypatch):
    welcomed = []

    async def fake_welcome(update, context):
        welcomed.append(update.message.text)

    monkeypatch.setattr(import_message, "welcome_handler", fake_welcome)
    message = FakeMessage(
        "Your transaction has failed. Your Airtel Money balance is "
        "Ksh 1000. Please try again later. TID: J3Q4QR1C9UQ"
    )

    state = asyncio.run(
        import_message.automatic_import_handler(
            SimpleNamespace(message=message),
            SimpleNamespace(user_data={}),
        )
    )

    assert state == ConversationHandler.END
    assert welcomed == []
    assert message.replies == []


def test_missing_provider_date_is_required_before_category_selection():
    message = FakeMessage("Airtime for family")
    context = SimpleNamespace(
        user_data={
            "pending_import": {
                "started_at": import_message.time.monotonic(),
                "preview": {
                    "requiresDate": True,
                    "direction": "expense",
                    "counterparty": "Airtel subscriber",
                    "providerTransactionType": "airtime_topup",
                    "suggestedCategory": "airtime",
                },
                "aliases": {},
            }
        }
    )

    state = asyncio.run(
        import_message.import_description_handler(
            SimpleNamespace(message=message),
            context,
        )
    )
    assert state == import_message.IMPORT_DATE

    date_message = FakeMessage("2026-08-20")
    state = asyncio.run(
        import_message.import_date_handler(
            SimpleNamespace(message=date_message),
            context,
        )
    )

    assert state == import_message.IMPORT_CATEGORY
    assert context.user_data["pending_import"]["transaction_date"] == "2026-08-20"
    keyboard = date_message.replies[-1][1]["reply_markup"]
    assert keyboard.inline_keyboard[0][0].text == "Airtime"


def test_import_requires_description_and_clears_sensitive_state(monkeypatch):
    raw_message = "SAFE SAMPLE PROVIDER MESSAGE"
    captured_import = {}

    async def run_immediately(function, *args, **kwargs):
        # Production deliberately moves blocking requests off the event loop.
        # This unit test replaces the thread boundary with a deterministic call.
        return function(*args, **kwargs)

    monkeypatch.setattr(import_message.asyncio, "to_thread", run_immediately)

    monkeypatch.setattr(
        import_message,
        "get_telegram_session",
        lambda telegram_id: {"linked": True, "token": "temporary-token"},
    )
    monkeypatch.setattr(
        import_message,
        "get_telegram_preferences",
        lambda token: {"category_aliases": {}},
    )
    monkeypatch.setattr(
        import_message,
        "preview_transaction_import",
        lambda token, message: {
            "kind": "transaction",
            "importable": True,
            "provider": "mpesa",
            "providerTransactionType": "data_bundle",
            "direction": "expense",
            "amount": "50.00",
            "currency": "KES",
            "occurredAt": "2026-08-17T10:23:00+03:00",
            "counterparty": "Safaricom",
            "fee": "0.00",
            "paymentMethod": "m-pesa",
            "suggestedCategory": "airtime",
        },
    )

    def fake_import(
        token,
        message,
        description,
        category,
        transaction_date=None,
        remember_alias=None,
    ):
        captured_import.update({
            "token": token,
            "message": message,
            "description": description,
            "category": category,
            "remember_alias": remember_alias,
            "transaction_date": transaction_date,
        })
        return {
            "data": {
                "amount": "50.00",
                "date": "2026-08-17",
                "description": "weekly data bundle",
                "category": "Airtime",
                "payment_method": "m-pesa",
            },
            "rememberedAlias": "weekly data bundle",
        }

    monkeypatch.setattr(
        import_message,
        "import_transaction_message",
        fake_import,
    )

    message = FakeMessage()
    context = SimpleNamespace(
        args=raw_message.split(),
        user_data={},
    )
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=123),
    )

    state = asyncio.run(import_message.import_message_handler(update, context))
    assert state == import_message.IMPORT_DESCRIPTION
    assert context.user_data["pending_import"]["raw_message"] == raw_message
    assert "What was this transaction for?" in message.replies[-1][0]

    description_update = SimpleNamespace(
        message=FakeMessage("Weekly data bundle")
    )
    state = asyncio.run(
        import_message.import_description_handler(description_update, context)
    )
    assert state == import_message.IMPORT_CATEGORY
    keyboard = description_update.message.replies[-1][1]["reply_markup"]
    assert keyboard.inline_keyboard[0][0].text == "Airtime"

    category_query = FakeCallbackQuery("importcat|airtime")
    state = asyncio.run(
        import_message.import_category_callback(
            SimpleNamespace(callback_query=category_query),
            context,
        )
    )
    assert state == import_message.IMPORT_CONFIRM
    assert "Save & remember" in {
        button.text
        for row in category_query.edits[-1][1]["reply_markup"].inline_keyboard
        for button in row
    }

    save_query = FakeCallbackQuery("importsave|remember")
    state = asyncio.run(
        import_message.import_save_callback(
            SimpleNamespace(callback_query=save_query),
            context,
        )
    )

    assert state == ConversationHandler.END
    assert captured_import["description"] == "Weekly data bundle"
    assert captured_import["category"] == "airtime"
    assert captured_import["remember_alias"] == "weekly data bundle"
    assert "pending_import" not in context.user_data
    assert "import_access_token" not in context.user_data
