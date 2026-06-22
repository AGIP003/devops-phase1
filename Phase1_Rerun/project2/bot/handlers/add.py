import asyncio
from datetime import date

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.api_client import (
    create_transaction,
    get_telegram_preferences,
    get_telegram_session,
    update_telegram_preferences,
)
from bot.transaction_parser import (
    CATEGORIES,
    PAYMENT_METHODS,
    TransactionInputError,
    normalize_payment_method,
    parse_transaction,
)


async def _linked_session(telegram_id):
    session = await asyncio.to_thread(get_telegram_session, telegram_id)
    return session if session.get("linked") else None


async def _save_transaction(message, transaction, token):
    try:
        result = await asyncio.to_thread(
            create_transaction,
            token,
            transaction["description"],
            transaction["amount"],
            transaction["category"],
            transaction["type"],
            date.today().isoformat(),
            transaction["payment_method"],
        )
    except requests.RequestException:
        await message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return
    except RuntimeError as error:
        await message.reply_text(f"Could not save the transaction: {error}")
        return

    saved = result.get("data", {})
    await message.reply_text(
        "✅ Transaction saved\n\n"
        f"Amount: KES {float(saved.get('amount', transaction['amount'])):,.2f}\n"
        f"Description: {saved.get('description', transaction['description'])}\n"
        f"Category: {saved.get('category', transaction['category'])}\n"
        f"Type: {saved.get('type', transaction['type'])}\n"
        f"Payment: {saved.get('payment_method', transaction['payment_method'])}"
    )


def _category_keyboard(candidates):
    rows = [
        [
            InlineKeyboardButton(
                candidate["category"].title(),
                callback_data=f"addcat|{candidate['type']}|{candidate['category']}",
            )
        ]
        for candidate in candidates[:3]
    ]
    rows.append(
        [
            InlineKeyboardButton("📂 All expenses", callback_data="addmore|expense"),
            InlineKeyboardButton("💰 All income", callback_data="addmore|income"),
        ]
    )
    rows.append([InlineKeyboardButton("Cancel", callback_data="addcancel")])
    return InlineKeyboardMarkup(rows)


def _all_categories_keyboard(transaction_type):
    rows = []
    categories = CATEGORIES[transaction_type]
    for index in range(0, len(categories), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    category.title(),
                    callback_data=f"addcat|{transaction_type}|{category}",
                )
                for category in categories[index:index + 2]
            ]
        )
    rows.append([InlineKeyboardButton("← Suggestions", callback_data="addmore|suggestions")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="addcancel")])
    return InlineKeyboardMarkup(rows)


def _payment_keyboard():
    rows = []
    for index in range(0, len(PAYMENT_METHODS), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    payment.title(),
                    callback_data=f"addpm|{payment}",
                )
                for payment in PAYMENT_METHODS[index:index + 2]
            ]
        )
    rows.append([InlineKeyboardButton("Cancel", callback_data="addcancel")])
    return InlineKeyboardMarkup(rows)


async def _request_payment(message, transaction):
    supplied = transaction.get("supplied_payment")
    heading = (
        f"“{supplied}” isn’t a supported payment method."
        if supplied
        else "Choose a payment method."
    )
    await message.reply_text(
        f"💳 {heading}\n\nSelect the method used for this transaction:",
        reply_markup=_payment_keyboard(),
    )


async def add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse, infer, validate, and save a transaction."""
    if not context.args:
        await update.message.reply_text(
            "Minimal format:\n"
            "/add AMOUNT DESCRIPTION\n\n"
            "Examples:\n"
            "/add 250 matatu fare\n"
            "/add KES 1,200 groceries via mpesa\n"
            "/add -5000 freelance payment\n\n"
            "A negative amount indicates income."
        )
        return

    try:
        session = await _linked_session(update.effective_user.id)
        if session is None:
            await update.message.reply_text(
                "Link your account first using /link YOUR_CODE."
            )
            return
        token = session["token"]
        preferences = await asyncio.to_thread(get_telegram_preferences, token)
        transaction = parse_transaction(" ".join(context.args), preferences)
    except TransactionInputError as error:
        await update.message.reply_text(f"❌ {error}")
        return
    except requests.RequestException:
        await update.message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return
    except RuntimeError as error:
        await update.message.reply_text(f"Could not prepare the transaction: {error}")
        return

    context.user_data["access_token"] = token
    if transaction["ambiguous"] or not transaction["category"]:
        candidates = transaction["candidates"][:3]
        if not candidates:
            candidates = [
                {"type": "expense", "category": "other expense"},
                {"type": "income", "category": "other income"},
            ]
        context.user_data["pending_transaction"] = transaction
        await update.message.reply_text(
            "🏷️ I’m not fully sure about the category.\n\n"
            f"Transaction: KES {transaction['amount']:,.2f}\n"
            f"Description: {transaction['description']}\n\n"
            "Choose the best match:",
            reply_markup=_category_keyboard(candidates),
        )
        return

    if transaction["invalid_payment"] or not transaction["payment_method"]:
        context.user_data["pending_transaction"] = transaction
        await _request_payment(update.message, transaction)
        return

    await _save_transaction(update.message, transaction, token)


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending = context.user_data.get("pending_transaction")
    token = context.user_data.get("access_token")
    if not pending or not token:
        await query.edit_message_text(
            "This transaction request expired. Please send /add again."
        )
        return

    _, transaction_type, category = query.data.split("|", 2)
    pending["type"] = transaction_type
    pending["category"] = category
    pending["ambiguous"] = False
    await query.edit_message_text(f"Category selected: {category.title()}")
    if pending.get("invalid_payment") or not pending.get("payment_method"):
        await _request_payment(query.message, pending)
        return

    context.user_data.pop("pending_transaction", None)
    await _save_transaction(query.message, pending, token)


async def category_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending = context.user_data.get("pending_transaction")
    if not pending:
        await query.edit_message_text(
            "This transaction request expired. Please send /add again."
        )
        return

    menu = query.data.split("|", 1)[1]
    if menu == "suggestions":
        candidates = pending.get("candidates") or [
            {"type": "expense", "category": "other expense"},
            {"type": "income", "category": "other income"},
        ]
        await query.edit_message_text(
            "🏷️ Choose the closest category:",
            reply_markup=_category_keyboard(candidates),
        )
        return

    await query.edit_message_text(
        f"🏷️ Choose a {menu} category:",
        reply_markup=_all_categories_keyboard(menu),
    )


async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending = context.user_data.get("pending_transaction")
    token = context.user_data.get("access_token")
    if not pending or not token:
        await query.edit_message_text(
            "This transaction request expired. Please send /add again."
        )
        return

    payment_method = query.data.split("|", 1)[1]
    pending["payment_method"] = payment_method
    pending["invalid_payment"] = False
    context.user_data.pop("pending_transaction", None)
    await query.edit_message_text(f"Payment selected: {payment_method.title()}")
    await _save_transaction(query.message, pending, token)


async def cancel_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("pending_transaction", None)
    await query.edit_message_text("Transaction cancelled.")


async def default_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Set your default payment method:\n"
            "/default mpesa\n\n"
            f"Options: {', '.join(PAYMENT_METHODS)}"
        )
        return

    payment_method = normalize_payment_method(" ".join(context.args))
    if not payment_method:
        await update.message.reply_text(
            f"Unknown payment method. Choose: {', '.join(PAYMENT_METHODS)}"
        )
        return

    try:
        session = await _linked_session(update.effective_user.id)
        if session is None:
            await update.message.reply_text("Link your account first using /link YOUR_CODE.")
            return
        await asyncio.to_thread(
            update_telegram_preferences,
            session["token"],
            default_payment_method=payment_method,
        )
    except (requests.RequestException, RuntimeError) as error:
        await update.message.reply_text(f"Could not update your default: {error}")
        return

    await update.message.reply_text(
        f"✅ Default payment method set to {payment_method}."
    )


async def category_alias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = " ".join(context.args).strip()
    if "=" not in raw:
        await update.message.reply_text(
            "Create a category alias like this:\n"
            "/alias matatu=transport\n"
            "/alias lunch=food"
        )
        return

    alias, category = [part.strip().lower() for part in raw.split("=", 1)]
    valid_categories = {item for values in CATEGORIES.values() for item in values}
    if not alias or category not in valid_categories:
        await update.message.reply_text(
            "That category is not valid. Use one of the Finance Tracker categories."
        )
        return

    try:
        session = await _linked_session(update.effective_user.id)
        if session is None:
            await update.message.reply_text("Link your account first using /link YOUR_CODE.")
            return
        token = session["token"]
        preferences = await asyncio.to_thread(get_telegram_preferences, token)
        aliases = dict(preferences.get("category_aliases") or {})
        aliases[alias] = category
        await asyncio.to_thread(
            update_telegram_preferences,
            token,
            category_aliases=aliases,
        )
    except (requests.RequestException, RuntimeError) as error:
        await update.message.reply_text(f"Could not save the alias: {error}")
        return

    await update.message.reply_text(
        f"✅ “{alias}” will now be categorized as {category}."
    )
