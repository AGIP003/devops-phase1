import asyncio

import requests
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from bot.api_client import get_telegram_session


LINKED_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["/add", "/balance"],
        ["/default", "/help"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option or type a command",
)


async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome any normal message according to the user's link status."""
    telegram_user = update.effective_user
    message = update.effective_message

    try:
        session = await asyncio.to_thread(get_telegram_session, telegram_user.id)
    except requests.RequestException:
        await message.reply_text(
            "I can’t reach Finance Tracker right now. Please try again shortly."
        )
        return
    except RuntimeError as error:
        await message.reply_text(f"I couldn’t check your account: {error}")
        return

    if not session.get("linked"):
        context.user_data.clear()
        await message.reply_text(
            f"Hello {telegram_user.first_name}! 👋\n\n"
            "Your Telegram account is not linked to Finance Tracker yet.\n\n"
            "https://moneytiqx.vercel.app/dashboard\n"
            "Open the web dashboard, select Telegram, generate a link code, "
            "then send:\n\n"
            "/link YOUR_CODE",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    user = session.get("user", {})
    username = user.get("username") or telegram_user.first_name
    context.user_data["access_token"] = session["token"]
    context.user_data["linked_user"] = user

    await message.reply_text(
        f"Hello {username}! 👋\n\n"
        "What would you like to do today?\n\n"
        "➕ /add — Add a transaction\n"
        "💰 /balance — Check your balance\n"
        "⚙️ /default — Set your payment method\n"
        "❓ /help — View help",
        reply_markup=LINKED_KEYBOARD,
    )
