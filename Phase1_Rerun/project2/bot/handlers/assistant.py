from __future__ import annotations

import asyncio
import re
import time
from datetime import date

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import (
    create_transaction,
    get_telegram_preferences,
    get_telegram_session,
    request_telegram_assistant,
)
from bot.handlers.balance import balance_handler
from bot.transaction_parser import (
    CATEGORIES,
    PAYMENT_METHODS,
    normalize_payment_method,
)


AI_TRANSACTION_TTL_SECONDS = 10 * 60
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_LIST_ITEM = re.compile(r"^(?:[-*•]|\d+[.)])\s+")


def _format_mobile_paragraphs(value: str) -> str:
    """Make validated AI text readable on a narrow Telegram screen.

    The formatter changes spacing only. It does not reinterpret, summarize, or
    add financial claims to the model's answer.
    """

    source_blocks = re.split(r"\n\s*\n", value.strip())
    formatted_blocks = []

    for source_block in source_blocks:
        lines = [
            " ".join(line.split())
            for line in source_block.splitlines()
            if line.strip()
        ]
        if not lines:
            continue
        if any(_LIST_ITEM.match(line) for line in lines):
            formatted_blocks.append("\n".join(lines))
            continue

        paragraph = " ".join(lines)
        formatted_blocks.extend(
            sentence.strip()
            for sentence in _SENTENCE_BOUNDARY.split(paragraph)
            if sentence.strip()
        )

    return "\n\n".join(formatted_blocks)


def _format_ai_reply(result: dict) -> str:
    sections = [_format_mobile_paragraphs(result["reply"])]

    evidence = [
        " ".join(str(item).split())
        for item in result.get("evidence") or []
        if str(item).strip()
    ]
    if evidence:
        sections.append(
            "From your records\n" + "\n".join(f"• {item}" for item in evidence)
        )

    caveats = [
        " ".join(str(item).split())
        for item in result.get("caveats") or []
        if str(item).strip()
    ]
    if caveats:
        sections.append(
            "Keep in mind\n" + "\n".join(f"• {item}" for item in caveats)
        )

    return "\n\n".join(section for section in sections if section)


def _clear_pending_ai_transaction(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    context.user_data.pop("pending_ai_transaction", None)
    context.user_data.pop("ai_transaction_access_token", None)


def _pending_ai_transaction(context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get("pending_ai_transaction")
    if not pending:
        return None
    if time.monotonic() - pending["started_at"] > AI_TRANSACTION_TTL_SECONDS:
        _clear_pending_ai_transaction(context)
        return None
    return pending


def _review_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Save", callback_data="aitxn|save"),
            InlineKeyboardButton("Cancel", callback_data="aitxn|cancel"),
        ],
        [
            InlineKeyboardButton(
                "Change category",
                callback_data="aitxn|menu|category",
            ),
            InlineKeyboardButton(
                "Change payment",
                callback_data="aitxn|menu|payment",
            ),
        ],
    ])


def _category_keyboard(transaction_type: str):
    categories = CATEGORIES[transaction_type]
    rows = []
    for index in range(0, len(categories), 2):
        rows.append([
            InlineKeyboardButton(
                category.title(),
                callback_data=f"aitxn|category|{category}",
            )
            for category in categories[index:index + 2]
        ])
    rows.append([
        InlineKeyboardButton("Back", callback_data="aitxn|review")
    ])
    return InlineKeyboardMarkup(rows)


def _payment_keyboard():
    rows = []
    for index in range(0, len(PAYMENT_METHODS), 2):
        rows.append([
            InlineKeyboardButton(
                payment.title(),
                callback_data=f"aitxn|payment|{payment}",
            )
            for payment in PAYMENT_METHODS[index:index + 2]
        ])
    rows.append([
        InlineKeyboardButton("Back", callback_data="aitxn|review")
    ])
    return InlineKeyboardMarkup(rows)


def _review_text(pending: dict) -> str:
    transaction = pending["transaction"]
    review_note = (
        "\nReview carefully: the AI marked this as uncertain."
        if transaction.get("needs_review")
        else ""
    )
    return (
        "AI transaction preview — nothing has been saved\n\n"
        f"Amount: {transaction['currency']} {transaction['amount']}\n"
        f"Date: {transaction['date']}\n"
        f"Description: {transaction['description']}\n"
        f"Category: {transaction['category'].title()}\n"
        f"Type: {transaction['type'].title()}\n"
        f"Payment: {transaction['payment_method'].title()}"
        f"{review_note}\n\n"
        "Check every field, then choose what to do."
    )


async def _deterministic_fallback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
):
    """Keep core commands useful when the external AI service is offline."""

    clean = text.casefold()
    if re.search(r"\b(my\s+)?(balance|income|expenses?)\b", clean):
        await balance_handler(update, context)
        return

    await update.effective_message.reply_text(
        "AI assistance is unavailable right now, but the core bot still works.\n\n"
        "Use /add AMOUNT DESCRIPTION to add a transaction, paste an M-Pesa "
        "or Airtel SMS to import it, send a receipt photo, use /balance for "
        "your totals, or /help for every command."
    )


async def assistant_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Use validated AI routing for ordinary text from a linked user."""

    message = update.effective_message
    telegram_user = update.effective_user
    if message is None or telegram_user is None:
        return ConversationHandler.END

    text = " ".join((message.text or "").strip().split())
    if not text:
        return ConversationHandler.END

    try:
        session = await asyncio.to_thread(
            get_telegram_session,
            telegram_user.id,
        )
    except requests.RequestException:
        await message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return ConversationHandler.END
    except RuntimeError as error:
        await message.reply_text(f"I couldn’t check your account: {error}")
        return ConversationHandler.END

    if not session.get("linked"):
        await message.reply_text(
            "Link your account first using /link YOUR_CODE."
        )
        return ConversationHandler.END

    token = session["token"]
    try:
        result = await asyncio.to_thread(
            request_telegram_assistant,
            token,
            text,
        )
    except requests.RequestException:
        await message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return ConversationHandler.END
    except RuntimeError:
        await _deterministic_fallback(update, context, text)
        return ConversationHandler.END

    intent = result["intent"]
    if intent == "balance":
        await balance_handler(update, context)
        return ConversationHandler.END

    if intent != "transaction":
        await message.reply_text(_format_ai_reply(result))
        return ConversationHandler.END

    transaction = result["transaction"]
    if transaction["currency"] != "KES":
        await message.reply_text(
            "I found a possible transaction, but it was not saved.\n\n"
            f"Amount: {transaction['currency']} {transaction['amount']}\n"
            f"Description: {transaction['description']}\n\n"
            "Foreign-currency transaction storage is not available yet. "
            "Saving it as KES would corrupt your analytics."
        )
        return ConversationHandler.END

    try:
        preferences = await asyncio.to_thread(
            get_telegram_preferences,
            token,
        )
    except (requests.RequestException, RuntimeError):
        preferences = {}

    payment_method = normalize_payment_method(
        preferences.get("default_payment_method")
    ) or "m-pesa"
    pending = {
        "started_at": time.monotonic(),
        "telegram_user_id": telegram_user.id,
        "transaction": {
            "amount": transaction["amount"],
            "description": transaction["description"],
            "category": transaction["category"],
            "type": transaction["kind"],
            "currency": transaction["currency"],
            "confidence": transaction["confidence"],
            "needs_review": transaction["needs_review"],
            "payment_method": payment_method,
            "date": date.today().isoformat(),
        },
    }
    context.user_data["pending_ai_transaction"] = pending
    context.user_data["ai_transaction_access_token"] = token

    await message.reply_text(
        _review_text(pending),
        reply_markup=_review_keyboard(),
    )
    return ConversationHandler.END


async def assistant_transaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Apply review choices; only the explicit save action writes data."""

    query = update.callback_query
    await query.answer()
    pending = _pending_ai_transaction(context)
    token = context.user_data.get("ai_transaction_access_token")

    if (
        pending is None
        or not token
        or update.effective_user is None
        or pending["telegram_user_id"] != update.effective_user.id
    ):
        _clear_pending_ai_transaction(context)
        await query.edit_message_text(
            "This AI preview expired. Send the transaction again."
        )
        return

    parts = query.data.split("|", 2)
    action = parts[1]
    transaction = pending["transaction"]

    if action == "cancel":
        _clear_pending_ai_transaction(context)
        await query.edit_message_text("Transaction cancelled. Nothing was saved.")
        return

    if action == "menu" and parts[2] == "category":
        await query.edit_message_text(
            "Choose the category:",
            reply_markup=_category_keyboard(transaction["type"]),
        )
        return

    if action == "menu" and parts[2] == "payment":
        await query.edit_message_text(
            "Choose the payment method:",
            reply_markup=_payment_keyboard(),
        )
        return

    if action == "category":
        category = parts[2]
        if category not in CATEGORIES[transaction["type"]]:
            _clear_pending_ai_transaction(context)
            await query.edit_message_text("That category is not valid.")
            return
        transaction["category"] = category

    if action == "payment":
        payment = parts[2]
        if payment not in PAYMENT_METHODS:
            _clear_pending_ai_transaction(context)
            await query.edit_message_text("That payment method is not valid.")
            return
        transaction["payment_method"] = payment

    if action in {"category", "payment", "review"}:
        await query.edit_message_text(
            _review_text(pending),
            reply_markup=_review_keyboard(),
        )
        return

    if action != "save":
        _clear_pending_ai_transaction(context)
        await query.edit_message_text("That action is not valid.")
        return

    try:
        result = await asyncio.to_thread(
            create_transaction,
            token,
            transaction["description"],
            transaction["amount"],
            transaction["category"],
            transaction["type"],
            transaction["date"],
            transaction["payment_method"],
        )
    except requests.RequestException:
        await query.edit_message_text(
            "I can’t reach Finance Tracker right now. Nothing was saved. "
            "Use the buttons to retry or cancel.",
            reply_markup=_review_keyboard(),
        )
        return
    except RuntimeError as error:
        await query.edit_message_text(
            f"Could not save the transaction: {error}",
            reply_markup=_review_keyboard(),
        )
        return

    saved = result.get("data", {})
    _clear_pending_ai_transaction(context)
    await query.edit_message_text(
        "✅ Transaction saved\n\n"
        f"Amount: KES {saved.get('amount', transaction['amount'])}\n"
        f"Description: {saved.get('description', transaction['description'])}\n"
        f"Category: {saved.get('category', transaction['category'])}\n"
        f"Payment: {saved.get('payment_method', transaction['payment_method'])}"
    )
