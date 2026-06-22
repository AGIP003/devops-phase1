from telegram import Update
from telegram.ext import ContextTypes


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Finance Tracker bot commands\n\n"
        "/link CODE — Connect your web account\n"
        "/add AMOUNT DESCRIPTION — Add a transaction\n"
        "/balance — View your financial summary\n"
        "/default PAYMENT — Set your default payment method\n"
        "/alias WORD=CATEGORY — Create a category alias\n"
        "/help — Show this guide"
    )
