from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Is called when the user sends /start"""
    user = update.effective_user

    await update.message.reply_text(
        f" Hey {user.first_name}! Welcome to Pesatiq Bot. \n\n"
        f"I can help you track your finances directly from Telegram. \n\n"
        f"Commands: \n"
        f"/link - Link your Pesatiq account\n"
        f"/add - Add a transaction\n"
        f"/balance - Check your balance\n"
        f"/help - Show this message again\n"
    )

    