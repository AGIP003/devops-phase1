import asyncio

import requests
from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import get_telegram_session, get_transactions


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show income, expenses, and current balance for a linked user."""
    telegram_user = update.effective_user

    try:
        session = await asyncio.to_thread(get_telegram_session, telegram_user.id)
        if not session.get("linked"):
            await update.message.reply_text(
                "Your Telegram account is not linked yet.\n\n"
                "Generate a code in the web dashboard and send:\n"
                "/link YOUR_CODE"
            )
            return

        token = session["token"]
        context.user_data["access_token"] = token
        context.user_data["linked_user"] = session.get("user", {})
        transactions = await asyncio.to_thread(get_transactions, token)
    except requests.RequestException:
        await update.message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return
    except RuntimeError as error:
        await update.message.reply_text(f"Could not load your balance: {error}")
        return

    income = sum(
        float(transaction.get("amount", 0))
        for transaction in transactions
        if transaction.get("type") == "income"
    )
    expenses = sum(
        float(transaction.get("amount", 0))
        for transaction in transactions
        if transaction.get("type") == "expense"
    )
    balance = income - expenses

    await update.message.reply_text(
        "Your Finance Tracker summary\n\n"
        f"Income: KES {income:,.2f}\n"
        f"Expenses: KES {expenses:,.2f}\n"
        f"Balance: KES {balance:,.2f}"
    )
