import asyncio
import re
import time

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import (
    UnsupportedProviderMessageError,
    get_telegram_preferences,
    get_telegram_session,
    import_transaction_message,
    preview_transaction_import,
)
from bot.transaction_parser import CATEGORIES, category_candidates
from bot.handlers.welcome import welcome_handler


IMPORT_DESCRIPTION, IMPORT_CATEGORY, IMPORT_CONFIRM = range(3)
IMPORT_TTL_SECONDS = 10 * 60
PROVIDER_MESSAGE_PREFIX = re.compile(
    r"^\s*(?:TID:\s*)?[A-Z0-9]{10,11}(?:\s+confirmed\.|\.\s+)",
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


def _confirmation_keyboard(can_remember: bool):
    rows = [[InlineKeyboardButton("Save once", callback_data="importsave|once")]]
    if can_remember:
        rows[0].append(
            InlineKeyboardButton(
                "Save & remember",
                callback_data="importsave|remember",
            )
        )
    rows.append([InlineKeyboardButton("Cancel", callback_data="importcancel")])
    return InlineKeyboardMarkup(rows)


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
    """Route provider-looking text to imports and ordinary text to welcome."""

    raw_message = " ".join(update.message.text.strip().split())
    if not PROVIDER_MESSAGE_PREFIX.match(raw_message):
        await welcome_handler(update, context)
        return ConversationHandler.END

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

    if not preview.get("importable"):
        if preview.get("kind") == "fuliza_notice":
            fee = preview.get("financingFee")
            fee_line = f"\nFinancing fee: KES {fee}" if fee is not None else ""
            await update.message.reply_text(
                "ℹ️ Fuliza notice recognized\n\n"
                f"Type: {preview.get('noticeType', 'notice').title()}\n"
                f"Amount: KES {preview['amount']}"
                f"{fee_line}\n\n"
                f"{preview['message']}"
            )
        else:
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
    await update.message.reply_text(
        "✅ Provider message recognized\n\n"
        f"Provider: {_provider_label(preview['provider'])}\n"
        f"Amount: {preview['currency']} {preview['amount']}\n"
        f"Type: {preview['direction'].title()}\n"
        f"When: {preview['occurredAt']}"
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
    preview = pending["preview"]
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
        forced_type=preview["direction"],
    )
    suggestions = [category for _, _, category in ranked]
    provider_suggestion = preview.get("suggestedCategory")
    if provider_suggestion:
        suggestions.insert(0, provider_suggestion)

    await update.message.reply_text(
        "Choose the category. Suggestions appear first, but you have the final say:",
        reply_markup=_categories_keyboard(preview["direction"], suggestions),
    )
    return IMPORT_CATEGORY


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
    if category not in CATEGORIES[pending["preview"]["direction"]]:
        await query.edit_message_text("That category is not valid.")
        _clear_pending_import(context)
        return ConversationHandler.END

    pending["category"] = category
    description = pending["description"]
    alias = description.casefold() if len(description) <= 100 else None
    pending["remember_alias"] = alias

    preview = pending["preview"]
    fee = preview.get("fee")
    fee_line = f"\nProvider fee: KES {fee}" if fee is not None else ""
    remember_line = (
        f"\n\nSave & remember will map “{alias}” to {category}."
        if alias
        else ""
    )
    await query.edit_message_text(
        "Review before saving\n\n"
        f"Amount: {preview['currency']} {preview['amount']}\n"
        f"Date: {preview['occurredAt'][:10]}\n"
        f"Description: {description}\n"
        f"Category: {category.title()}\n"
        f"Payment: {preview['paymentMethod']}"
        f"{fee_line}{remember_line}",
        reply_markup=_confirmation_keyboard(alias is not None),
    )
    return IMPORT_CONFIRM


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
            remember_alias,
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
    remembered = result.get("rememberedAlias")
    remembered_line = (
        f"\nRemembered: “{remembered}” → {saved['category']}"
        if remembered
        else ""
    )
    await query.edit_message_text(
        "✅ Imported safely\n\n"
        f"Amount: KES {saved['amount']}\n"
        f"Date: {saved['date']}\n"
        f"Description: {saved['description']}\n"
        f"Category: {saved['category']}\n"
        f"Payment: {saved['payment_method']}"
        f"{remembered_line}"
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
