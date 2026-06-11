from telegram import Update
from telegram.ext import ContextTypes

async def add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /add command
    Expected format: /add <amount> <category> <description>
    Example: /add 200 transport matatu fare
    """
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌   Usage: /add <amount> <category> <description>\n"
            "Example: /add 200 transport matatu fare"
        )
        return

    try:
        amount = float(context.args[0])
        category = context.args[1].lower()
        description = ' '.join(context.args[2:])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number.")
        return

    # For now, just echo back the parsed values
    await update.message.reply_text(
        f"📝 Transaction parsed:\n"
        f"Amount: KES {amount:.2f}\n"
        f"Category: {category}\n"
        f"Description: {description}\n\n"
        "Parsing successful. (Saving to your account will be added after linking.)"
    )