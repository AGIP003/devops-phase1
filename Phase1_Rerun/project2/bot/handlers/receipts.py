from __future__ import annotations

import asyncio
import logging
import time
from datetime import date

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from app.services.telegram_files_service import download_largest_receipt
from bot.api_client import (
    create_transaction,
    get_telegram_session,
    preview_receipt,
)
from bot.transaction_parser import CATEGORIES, PAYMENT_METHODS


logger = logging.getLogger(__name__)

(
    RECEIPT_DESCRIPTION,
    RECEIPT_DATE,
    RECEIPT_CATEGORY,
    RECEIPT_PAYMENT,
    RECEIPT_CONFIRM,
) = range(5)

RECEIPT_TTL_SECONDS = 10 * 60


def _clear_pending_receipt(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("pending_receipt", None)
    context.user_data.pop("receipt_access_token", None)


def _pending_receipt(context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get("pending_receipt")
    if not pending:
        return None
    if time.monotonic() - pending["started_at"] > RECEIPT_TTL_SECONDS:
        _clear_pending_receipt(context)
        return None
    return pending


def _category_keyboard(suggestion: str):
    categories = list(CATEGORIES["expense"])
    if suggestion in categories:
        categories.remove(suggestion)
        categories.insert(0, suggestion)

    rows = []
    for index in range(0, len(categories), 2):
        rows.append([
            InlineKeyboardButton(
                category.title(),
                callback_data=f"receiptcat|{category}",
            )
            for category in categories[index:index + 2]
        ])
    rows.append([
        InlineKeyboardButton("Cancel", callback_data="receiptcancel")
    ])
    return InlineKeyboardMarkup(rows)


def _payment_keyboard():
    rows = []
    for index in range(0, len(PAYMENT_METHODS), 2):
        rows.append([
            InlineKeyboardButton(
                payment.title(),
                callback_data=f"receiptpm|{payment}",
            )
            for payment in PAYMENT_METHODS[index:index + 2]
        ])
    rows.append([
        InlineKeyboardButton("Cancel", callback_data="receiptcancel")
    ])
    return InlineKeyboardMarkup(rows)


def _confirmation_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Save transaction",
                callback_data="receiptsave",
            ),
            InlineKeyboardButton(
                "Cancel",
                callback_data="receiptcancel",
            ),
        ]
    ])


async def handle_receipt_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    if message is None or update.effective_user is None:
        return ConversationHandler.END

    status = await message.reply_text("Reading receipt…")
    try:
        session = await asyncio.to_thread(
            get_telegram_session,
            update.effective_user.id,
        )
        if not session.get("linked"):
            await status.edit_text(
                "Link your account first using /link YOUR_CODE."
            )
            return ConversationHandler.END

        image = await download_largest_receipt(message)
        preview = await asyncio.to_thread(
            preview_receipt,
            session["token"],
            image.data,
            image.media_type,
        )
    except ValueError as error:
        await status.edit_text(str(error))
        return ConversationHandler.END
    except requests.RequestException:
        await status.edit_text(
            "I can’t reach Finance Tracker right now. Try again shortly."
        )
        return ConversationHandler.END
    except RuntimeError as error:
        await status.edit_text(f"Could not read that receipt: {error}")
        return ConversationHandler.END
    except Exception:
        logger.exception("Receipt preview failed")
        await status.edit_text(
            "Receipt processing failed safely. Please try again."
        )
        return ConversationHandler.END

    if not preview.get("can_parse"):
        await status.edit_text(
            "I could not safely read that receipt. "
            f"{preview.get('reason') or 'Try a clearer photo.'}"
        )
        return ConversationHandler.END

    receipt = preview["receipt"]
    date_text = receipt.get("transaction_date") or "not visible"
    review_text = "yes" if receipt["needs_review"] else "no"

    if receipt["currency"] != "KES":
        await status.edit_text(
            "Receipt read successfully, but it was not saved.\n\n"
            f"Merchant: {receipt['merchant']}\n"
            f"Amount: {receipt['currency']} {receipt['total']}\n"
            f"Date: {date_text}\n\n"
            "Foreign-currency transaction storage is not available yet. "
            "Saving this amount as KES would corrupt your analytics."
        )
        return ConversationHandler.END

    context.user_data["receipt_access_token"] = session["token"]
    context.user_data["pending_receipt"] = {
        "receipt": receipt,
        "started_at": time.monotonic(),
    }

    await status.edit_text(
        "Receipt preview — nothing has been saved\n\n"
        f"Merchant: {receipt['merchant']}\n"
        f"Amount: KES {receipt['total']}\n"
        f"Date: {date_text}\n"
        f"Suggested category: {receipt['suggested_category'].title()}\n"
        f"Needs review: {review_text}\n\n"
        "What was this transaction for? Your description is required."
    )
    return RECEIPT_DESCRIPTION


async def receipt_description_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    pending = _pending_receipt(context)
    if pending is None:
        await update.message.reply_text(
            "This receipt preview expired. Send the photo again."
        )
        return ConversationHandler.END

    description = " ".join(update.message.text.strip().split())
    if not description:
        await update.message.reply_text("Please provide a description.")
        return RECEIPT_DESCRIPTION
    if len(description) > 200:
        await update.message.reply_text(
            "Keep the description to 200 characters or fewer."
        )
        return RECEIPT_DESCRIPTION

    pending["description"] = description
    if pending["receipt"].get("transaction_date") is None:
        await update.message.reply_text(
            "The date was not readable. Enter it as YYYY-MM-DD."
        )
        return RECEIPT_DATE

    return await _request_category(update.message, pending)


async def receipt_date_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    pending = _pending_receipt(context)
    if pending is None:
        await update.message.reply_text(
            "This receipt preview expired. Send the photo again."
        )
        return ConversationHandler.END

    try:
        transaction_date = date.fromisoformat(update.message.text.strip())
    except (TypeError, ValueError):
        await update.message.reply_text(
            "Enter a valid date in YYYY-MM-DD format."
        )
        return RECEIPT_DATE

    if transaction_date > date.today():
        await update.message.reply_text(
            "The transaction date cannot be in the future."
        )
        return RECEIPT_DATE

    pending["transaction_date"] = transaction_date.isoformat()
    return await _request_category(update.message, pending)


async def _request_category(message, pending):
    suggestion = pending["receipt"]["suggested_category"]
    await message.reply_text(
        "Choose the category. The AI suggestion appears first, "
        "but you make the decision.",
        reply_markup=_category_keyboard(suggestion),
    )
    return RECEIPT_CATEGORY


async def receipt_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_receipt(context)
    if pending is None:
        await query.edit_message_text(
            "This receipt preview expired. Send the photo again."
        )
        return ConversationHandler.END

    category = query.data.split("|", 1)[1]
    if category not in CATEGORIES["expense"]:
        _clear_pending_receipt(context)
        await query.edit_message_text("That category is not valid.")
        return ConversationHandler.END

    pending["category"] = category
    await query.edit_message_text(
        "Choose how you paid:",
        reply_markup=_payment_keyboard(),
    )
    return RECEIPT_PAYMENT


async def receipt_payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_receipt(context)
    if pending is None:
        await query.edit_message_text(
            "This receipt preview expired. Send the photo again."
        )
        return ConversationHandler.END

    payment_method = query.data.split("|", 1)[1]
    if payment_method not in PAYMENT_METHODS:
        _clear_pending_receipt(context)
        await query.edit_message_text("That payment method is not valid.")
        return ConversationHandler.END

    pending["payment_method"] = payment_method
    receipt = pending["receipt"]
    transaction_date = (
        pending.get("transaction_date")
        or receipt["transaction_date"]
    )
    await query.edit_message_text(
        "Final review — still not saved\n\n"
        f"Amount: KES {receipt['total']}\n"
        f"Date: {transaction_date}\n"
        f"Description: {pending['description']}\n"
        f"Category: {pending['category'].title()}\n"
        f"Payment: {payment_method.title()}",
        reply_markup=_confirmation_keyboard(),
    )
    return RECEIPT_CONFIRM


async def receipt_save_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_receipt(context)
    token = context.user_data.get("receipt_access_token")
    if pending is None or not token:
        await query.edit_message_text(
            "This receipt preview expired. Send the photo again."
        )
        return ConversationHandler.END

    receipt = pending["receipt"]
    transaction_date = (
        pending.get("transaction_date")
        or receipt["transaction_date"]
    )
    try:
        result = await asyncio.to_thread(
            create_transaction,
            token,
            pending["description"],
            receipt["total"],
            pending["category"],
            "expense",
            transaction_date,
            pending["payment_method"],
            receipt.get("merchant"),
        )
    except requests.RequestException:
        await query.edit_message_text(
            "I can’t reach Finance Tracker. The receipt was not saved."
        )
        _clear_pending_receipt(context)
        return ConversationHandler.END
    except RuntimeError as error:
        await query.edit_message_text(f"Could not save receipt: {error}")
        _clear_pending_receipt(context)
        return ConversationHandler.END

    saved = result["data"]
    await query.edit_message_text(
        "✅ Receipt transaction saved\n\n"
        f"Amount: KES {saved['amount']}\n"
        f"Description: {saved['description']}\n"
        f"Category: {saved['category']}"
    )
    _clear_pending_receipt(context)
    return ConversationHandler.END


async def cancel_receipt_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    _clear_pending_receipt(context)
    await query.edit_message_text("Receipt import cancelled.")
    return ConversationHandler.END


async def cancel_receipt_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_pending_receipt(context)
    await update.message.reply_text("Receipt import cancelled.")
    return ConversationHandler.END
