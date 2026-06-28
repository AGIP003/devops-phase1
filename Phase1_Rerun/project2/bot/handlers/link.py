import requests
from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import verify_telegram_link


async def link_telegram_account(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str):
    telegram_user = update.effective_user

    try:
        result = verify_telegram_link(token, telegram_user.id)
    except requests.RequestException:
        await update.message.reply_text(
            "❌ I could not reach Finance Tracker. Please try again shortly."
        )
        return
    except RuntimeError as error:
        await update.message.reply_text(f"❌ {error}")
        return

    context.user_data["access_token"] = result["token"]
    context.user_data["linked_user"] = result.get("user", {})
    username = result.get("user", {}).get("username", "your account")

    await update.message.reply_text(
        f"✅ Telegram is now linked to {username}.\n\n"
        "You can use /add to record transactions and /balance to view your balance."
    )


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Link a Telegram user with a one-time code generated in the web app."""
    if not context.args:
        await update.message.reply_text(
            "Get your one-time code from your finance tracker dashboard:\n"
            "Click the below link to access your dashboard - https://moneytiqx.vercel.app\n\n"
            "/link YOUR_CODE\n\n"
            "The code expires after 10 minutes."
        )
        return

    token = context.args[0].strip()
    await link_telegram_account(update, context, token)
