import asyncio
import re
import time
from datetime import date

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import (
    UnsupportedProviderMessageError,
    get_telegram_preferences,
    get_telegram_session,
    import_transaction_message,
    preview_transaction_import,
    record_financing_event,
)
from bot.transaction_parser import CATEGORIES, category_candidates
from bot.handlers.assistant import assistant_message_handler
from bot.handlers.welcome import welcome_handler


(
    IMPORT_DESCRIPTION,
    IMPORT_DATE,
    IMPORT_CLASSIFICATION,
    IMPORT_CATEGORY,
    IMPORT_CONFIRM,
) = range(5)
IMPORT_TTL_SECONDS = 10 * 60
PROVIDER_MESSAGE_PREFIX = re.compile(
    r"^\s*(?:TID:\s*)?[A-Z0-9]{10,11}"
    r"(?:\s+(?:confirmed|successful)\.|\.\s+)",
    re.IGNORECASE,
)
FAILED_TRANSACTION_NOTICE = re.compile(
    r"^Your transaction has failed\..*\bTID:\s*[A-Z0-9]{11}\s*$",
    re.IGNORECASE,
)


def _clear_pending_import(context: ContextTypes.DEFAULT_TYPE) -> None:
    # The raw provider message and JWT are temporary and leave memory as soon
    # as the conversation finishes or is cancelled.
    context.user_data.pop("pending_import", None)
    context.user_data.pop("import_access_token", None)


def _pending_import(context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get("pending_import")
    if not pending:
        return None
    if time.monotonic() - pending["started_at"] > IMPORT_TTL_SECONDS:
        _clear_pending_import(context)
        return None
    return pending


def _categories_keyboard(transaction_type: str, suggestions: list[str]):
    ordered = list(dict.fromkeys(suggestions + CATEGORIES[transaction_type]))
    rows = []
    for index in range(0, len(ordered), 2):
        rows.append([
            InlineKeyboardButton(
                category.title(),
                callback_data=f"importcat|{category}",
            )
            for category in ordered[index:index + 2]
        ])
    rows.append([InlineKeyboardButton("Cancel", callback_data="importcancel")])
    return InlineKeyboardMarkup(rows)


def _classification_keyboard(flow_direction: str):
    if flow_direction == "money_in":
        primary = InlineKeyboardButton(
            "Count as income",
            callback_data="importtype|income",
        )
    else:
        primary = InlineKeyboardButton(
            "Count as expense",
            callback_data="importtype|expense",
        )
    return InlineKeyboardMarkup([
        [primary],
        [InlineKeyboardButton(
            "Moved between my accounts",
            callback_data="importtype|transfer",
        )],
        [InlineKeyboardButton("Cancel", callback_data="importcancel")],
    ])


def _confirmation_keyboard(can_remember: bool):
    save_label = "Save once" if can_remember else "Save"
    rows = [[InlineKeyboardButton(save_label, callback_data="importsave|once")]]
    if can_remember:
        rows[0].append(
            InlineKeyboardButton(
                "Save & remember",
                callback_data="importsave|remember",
            )
        )
    rows.append([
        InlineKeyboardButton(
            "Choose a different category",
            callback_data="importedit|category",
        )
    ])
    rows.append([InlineKeyboardButton("Cancel", callback_data="importcancel")])
    return InlineKeyboardMarkup(rows)


def _financing_confirmation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "Save financing record",
            callback_data="importfinance|save",
        )],
        [InlineKeyboardButton("Cancel", callback_data="importcancel")],
    ])


async def _request_financing_confirmation(message, pending):
    preview = pending["preview"]
    financing_fee = preview.get("financingFee")
    daily_fee = preview.get("dailyMaintenanceFee")
    fee_lines = []
    if financing_fee is not None:
        fee_lines.append(f"Access fee: KES {financing_fee}")
    if daily_fee is not None:
        fee_lines.append(f"Daily fee: KES {daily_fee}")
    fee_text = "\n".join(fee_lines) or "No explicit fee in this notice"
    await message.reply_text(
        "Review financing record\n\n"
        f"Type: {preview.get('noticeType', 'notice').title()}\n"
        f"Principal: KES {preview['amount']}\n"
        f"Date: {pending['transaction_date']}\n"
        f"{fee_text}\n\n"
        "Principal stays separate from spending; only explicit fees affect "
        "expense analytics.",
        reply_markup=_financing_confirmation_keyboard(),
    )
    return IMPORT_CONFIRM


def _provider_label(provider: str) -> str:
    return {
        "mpesa": "M-Pesa",
        "airtel_money": "Airtel Money",
        "fuliza_mpesa": "Fuliza M-Pesa",
    }.get(provider, provider.replace("_", " ").title())


async def import_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Start an explicit, confirmation-based provider-message import."""

    if not context.args:
        await update.message.reply_text(
            "Paste the complete provider SMS after /import.\n\n"
            "Example:\n/import ABC123... Confirmed. Ksh...\n\n"
            "The raw SMS is used temporarily for parsing and is not stored."
        )
        return ConversationHandler.END

    raw_message = " ".join(context.args).strip()
    return await _start_import(update, context, raw_message)


async def automatic_import_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Route provider text to imports and ordinary text to the assistant."""

    raw_message = " ".join(update.message.text.strip().split())
    if FAILED_TRANSACTION_NOTICE.fullmatch(raw_message):
        return ConversationHandler.END
    if not PROVIDER_MESSAGE_PREFIX.match(raw_message):
        return await assistant_message_handler(update, context)

    return await _start_import(
        update,
        context,
        raw_message,
        fallback_to_welcome=True,
    )


async def _start_import(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    raw_message: str,
    *,
    fallback_to_welcome: bool = False,
):
    try:
        session = await asyncio.to_thread(
            get_telegram_session,
            update.effective_user.id,
        )
        if not session.get("linked"):
            await update.message.reply_text(
                "Link your account first using /link YOUR_CODE."
            )
            return ConversationHandler.END

        token = session["token"]
        preview, preferences = await asyncio.gather(
            asyncio.to_thread(preview_transaction_import, token, raw_message),
            asyncio.to_thread(get_telegram_preferences, token),
        )
    except requests.RequestException:
        await update.message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return ConversationHandler.END
    except UnsupportedProviderMessageError as error:
        if fallback_to_welcome:
            await welcome_handler(update, context)
        else:
            await update.message.reply_text(
                f"Could not read that message: {error}"
            )
        return ConversationHandler.END
    except RuntimeError as error:
        await update.message.reply_text(f"Could not read that message: {error}")
        return ConversationHandler.END

    if preview.get("kind") == "fuliza_notice":
        context.user_data["import_access_token"] = token
        context.user_data["pending_import"] = {
            "raw_message": raw_message,
            "preview": preview,
            "started_at": time.monotonic(),
        }
        await update.message.reply_text(
            "ℹ️ Fuliza notice recognized\n\n"
            f"Type: {preview.get('noticeType', 'notice').title()}\n"
            f"Principal: KES {preview['amount']}\n"
            "What date was this notice for? Use YYYY-MM-DD."
        )
        return IMPORT_DATE

    if not preview.get("importable"):
        await update.message.reply_text(
            f"ℹ️ Message recognized, but not saved.\n\n{preview['message']}"
        )
        return ConversationHandler.END

    context.user_data["import_access_token"] = token
    context.user_data["pending_import"] = {
        "raw_message": raw_message,
        "preview": preview,
        "aliases": dict(preferences.get("category_aliases") or {}),
        "started_at": time.monotonic(),
    }

    fee = preview.get("fee")
    fee_line = f"\nFee: KES {fee}" if fee is not None else ""
    counterparty = preview.get("counterparty")
    counterparty_line = f"\nMerchant/person: {counterparty}" if counterparty else ""
    occurred_at = preview.get("occurredAt")
    when_line = occurred_at or "Not included by provider — date required"
    recognition_line = (
        "🔎 Message interpreted with AI — check every field"
        if preview.get("parserStrategy") == "ai"
        else "✅ Provider message recognized"
    )
    await update.message.reply_text(
        f"{recognition_line}\n\n"
        f"Provider: {_provider_label(preview['provider'])}\n"
        f"Amount: {preview['currency']} {preview['amount']}\n"
        f"Movement: {preview['flowDirection'].replace('_', ' ').title()}\n"
        f"Suggested: {preview['suggestedType'].title()}\n"
        f"When: {when_line}"
        f"{counterparty_line}{fee_line}\n\n"
        "What was this transaction for? Your description is required."
    )
    return IMPORT_DESCRIPTION


async def import_description_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    pending = _pending_import(context)
    if pending is None:
        await update.message.reply_text(
            "This import expired. Send /import with the SMS again."
        )
        return ConversationHandler.END

    description = " ".join(update.message.text.strip().split())
    if not description:
        await update.message.reply_text("Please describe what the transaction was for.")
        return IMPORT_DESCRIPTION
    if len(description) > 200:
        await update.message.reply_text(
            "Keep the description to 200 characters or fewer."
        )
        return IMPORT_DESCRIPTION

    pending["description"] = description
    if pending["preview"].get("requiresDate"):
        await update.message.reply_text(
            "This provider message has no transaction date.\n\n"
            "When did it happen? Use YYYY-MM-DD."
        )
        return IMPORT_DATE

    return await _request_classification_or_category(update.message, pending)


async def import_date_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    pending = _pending_import(context)
    if pending is None:
        await update.message.reply_text(
            "This import expired. Paste the provider SMS again."
        )
        return ConversationHandler.END

    try:
        transaction_date = date.fromisoformat(update.message.text.strip())
    except (TypeError, ValueError):
        await update.message.reply_text(
            "Enter a valid date in YYYY-MM-DD format, for example 2026-08-20."
        )
        return IMPORT_DATE

    if transaction_date > date.today():
        await update.message.reply_text("The transaction date cannot be in the future.")
        return IMPORT_DATE

    pending["transaction_date"] = transaction_date.isoformat()
    if pending["preview"].get("kind") == "fuliza_notice":
        return await _request_financing_confirmation(update.message, pending)
    return await _request_classification_or_category(update.message, pending)


async def _request_classification_or_category(message, pending):
    preview = pending["preview"]
    if preview.get("requiresClassification"):
        await message.reply_text(
            "How should this movement count in your reports?\n\n"
            "Choose income or expense only when it genuinely changed your "
            "money. Choose transfer when you moved it between accounts you use.",
            reply_markup=_classification_keyboard(preview["flowDirection"]),
        )
        return IMPORT_CLASSIFICATION

    pending["transaction_type"] = preview["suggestedType"]
    return await _request_import_category(message, pending)


async def import_classification_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_import(context)
    if pending is None:
        await query.edit_message_text(
            "This import expired. Paste the provider SMS again."
        )
        return ConversationHandler.END

    transaction_type = query.data.split("|", 1)[1]
    flow_direction = pending["preview"]["flowDirection"]
    allowed = (
        {"income", "transfer"}
        if flow_direction == "money_in"
        else {"expense", "transfer"}
    )
    if transaction_type not in allowed:
        await query.edit_message_text(
            "That classification does not match the movement."
        )
        _clear_pending_import(context)
        return ConversationHandler.END

    pending["transaction_type"] = transaction_type
    await query.edit_message_text(
        f"This will count as {transaction_type.replace('_', ' ')}."
    )
    return await _request_import_category(query.message, pending)


async def _request_import_category(message, pending):
    preview = pending["preview"]
    transaction_type = pending["transaction_type"]
    if transaction_type == "transfer":
        pending["category"] = "internal transfer"
        pending["remember_alias"] = None
        text, keyboard = _import_confirmation_view(pending)
        await message.reply_text(text, reply_markup=keyboard)
        return IMPORT_CONFIRM

    description = pending["description"]
    normalized_description = " ".join(description.casefold().split())
    remembered_category = pending["aliases"].get(normalized_description)

    if remembered_category in CATEGORIES[transaction_type]:
        pending["category"] = remembered_category
        pending["remember_alias"] = None
        text, keyboard = _import_confirmation_view(
            pending,
            remembered_alias=normalized_description,
        )
        await message.reply_text(text, reply_markup=keyboard)
        return IMPORT_CONFIRM

    suggestions = _import_category_suggestions(pending)

    await message.reply_text(
        "Choose the category. Suggestions appear first, but you have the final say:",
        reply_markup=_categories_keyboard(transaction_type, suggestions),
    )
    return IMPORT_CATEGORY


def _import_category_suggestions(pending):
    preview = pending["preview"]
    description = pending["description"]
    search_text = " ".join(
        value
        for value in (
            description,
            preview.get("counterparty"),
            preview.get("providerTransactionType"),
        )
        if value
    )
    ranked = category_candidates(
        search_text,
        pending["aliases"],
        forced_type=pending["transaction_type"],
    )
    suggestions = [category for _, _, category in ranked]
    provider_suggestion = preview.get("suggestedCategory")
    if provider_suggestion:
        suggestions.insert(0, provider_suggestion)
    return suggestions


def _import_confirmation_view(pending, *, remembered_alias=None):
    preview = pending["preview"]
    description = pending["description"]
    category = pending["category"]
    fee = preview.get("fee")
    fee_line = f"\nProvider fee: KES {fee}" if fee is not None else ""

    if pending["transaction_type"] == "transfer":
        category_note = "\nTransfers stay outside income and spending totals."
        remember_line = ""
        can_remember = False
    elif remembered_alias:
        category_note = (
            f"\nRemembered category: {category.title()} "
            f"for “{remembered_alias}”."
        )
        remember_line = ""
        can_remember = False
    else:
        category_note = ""
        alias = (
            " ".join(description.casefold().split())
            if len(description) <= 100
            else None
        )
        pending["remember_alias"] = alias
        remember_line = (
            f"\n\nSave & remember will map “{alias}” to {category}."
            if alias
            else ""
        )
        can_remember = alias is not None

    transaction_date = (
        pending.get("transaction_date")
        or preview["occurredAt"][:10]
    )
    text = (
        "Review before saving\n\n"
        f"Amount: {preview['currency']} {preview['amount']}\n"
        f"Date: {transaction_date}\n"
        f"Description: {description}\n"
        f"Count as: {pending['transaction_type'].title()}\n"
        f"Category: {category.title()}\n"
        f"Payment: {preview['paymentMethod']}"
        f"{fee_line}{category_note}{remember_line}"
    )
    return text, _confirmation_keyboard(can_remember)


async def import_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_import(context)
    if pending is None:
        await query.edit_message_text(
            "This import expired. Send /import with the SMS again."
        )
        return ConversationHandler.END

    category = query.data.split("|", 1)[1]
    if category not in CATEGORIES[pending["transaction_type"]]:
        await query.edit_message_text("That category is not valid.")
        _clear_pending_import(context)
        return ConversationHandler.END

    pending["category"] = category
    text, keyboard = _import_confirmation_view(pending)
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
    )
    return IMPORT_CONFIRM


async def import_change_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_import(context)
    if pending is None:
        await query.edit_message_text(
            "This import expired. Send /import with the SMS again."
        )
        return ConversationHandler.END

    preview = pending["preview"]
    suggestions = _import_category_suggestions(pending)
    await query.edit_message_text(
        "Choose a different category:",
        reply_markup=_categories_keyboard(pending["transaction_type"], suggestions),
    )
    return IMPORT_CATEGORY


async def import_save_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_import(context)
    token = context.user_data.get("import_access_token")
    if pending is None or not token:
        await query.edit_message_text(
            "This import expired. Send /import with the SMS again."
        )
        return ConversationHandler.END

    action = query.data.split("|", 1)[1]
    remember_alias = (
        pending.get("remember_alias") if action == "remember" else None
    )
    try:
        result = await asyncio.to_thread(
            import_transaction_message,
            token,
            pending["raw_message"],
            pending["description"],
            pending["category"],
            pending["transaction_type"],
            transaction_date=pending.get("transaction_date"),
            remember_alias=remember_alias,
            preview_token=pending["preview"].get("previewToken"),
        )
    except requests.RequestException:
        await query.edit_message_text(
            "I can’t reach Finance Tracker right now. The transaction was not "
            "confirmed as saved. Send /import again when the service is available."
        )
        _clear_pending_import(context)
        return ConversationHandler.END
    except RuntimeError as error:
        await query.edit_message_text(f"Could not import transaction: {error}")
        _clear_pending_import(context)
        return ConversationHandler.END

    saved = result["data"]
    restored = result.get("restored", False)
    remembered = result.get("rememberedAlias")
    remembered_line = (
        f"\nRemembered: “{remembered}” → {saved['category']}"
        if remembered
        else ""
    )
    success_heading = (
        "✅ Re-added with your corrected details"
        if restored
        else "✅ Imported safely"
    )
    await query.edit_message_text(
        f"{success_heading}\n\n"
        f"Amount: KES {saved['amount']}\n"
        f"Date: {saved['date']}\n"
        f"Description: {saved['description']}\n"
        f"Counted as: {saved['type'].title()}\n"
        f"Category: {saved['category']}\n"
        f"Payment: {saved['payment_method']}"
        f"{remembered_line}"
    )
    _clear_pending_import(context)
    return ConversationHandler.END


async def import_financing_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    pending = _pending_import(context)
    token = context.user_data.get("import_access_token")
    if pending is None or not token:
        await query.edit_message_text(
            "This financing preview expired. Paste the notice again."
        )
        return ConversationHandler.END

    try:
        result = await asyncio.to_thread(
            record_financing_event,
            token,
            pending["raw_message"],
            pending["transaction_date"],
        )
    except requests.RequestException:
        await query.edit_message_text(
            "I can’t reach Finance Tracker. The financing notice was not saved."
        )
        _clear_pending_import(context)
        return ConversationHandler.END
    except RuntimeError as error:
        await query.edit_message_text(f"Could not save financing notice: {error}")
        _clear_pending_import(context)
        return ConversationHandler.END

    saved = result["data"]
    fee = saved.get("financingFee") or saved.get("dailyMaintenanceFee")
    fee_line = f"\nRecorded fee: KES {fee}" if fee is not None else ""
    await query.edit_message_text(
        "✅ Financing record saved\n\n"
        f"Type: {saved['eventType'].title()}\n"
        f"Principal: KES {saved['principalAmount']}"
        f"{fee_line}"
    )
    _clear_pending_import(context)
    return ConversationHandler.END


async def cancel_import_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    _clear_pending_import(context)
    await query.edit_message_text("Transaction import cancelled.")
    return ConversationHandler.END


async def cancel_import_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_pending_import(context)
    await update.message.reply_text("Transaction import cancelled.")
    return ConversationHandler.END
