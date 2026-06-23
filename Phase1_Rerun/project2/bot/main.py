import os
import logging
import sys
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.handlers.start import start_handler
from bot.handlers.add import (
    add_handler,
    category_alias_handler,
    category_callback,
    category_menu_callback,
    cancel_add_callback,
    default_payment_handler,
    payment_callback,
)
from bot.handlers.link import link_handler
from bot.handlers.welcome import welcome_handler
from bot.handlers.balance import balance_handler
from bot.handlers.help import help_handler
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    update_info = None
    if update and getattr(update, "effective_chat", None):
        update_info = {
            "chat_id": update.effective_chat.id,
            "user_id": update.effective_user.id if update.effective_user else None,
        }
    logger.exception("Unhandled bot error update=%s", update_info, exc_info=context.error)

    if update and getattr(update, "effective_message", None):
        await update.effective_message.reply_text(
            "Something went wrong while handling that message. I logged the error."
        )

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Telegram token not set")
        raise RuntimeError('TELEGRAM_BOT_TOKEN not set')
        
    
    #Build the app
    app = Application.builder().token(token).build()

    #Register command handlers
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('add', add_handler))
    app.add_handler(CommandHandler('default', default_payment_handler))
    app.add_handler(CommandHandler('alias', category_alias_handler))
    app.add_handler(CommandHandler('link', link_handler))
    app.add_handler(CommandHandler('balance', balance_handler))
    app.add_handler(CommandHandler('help', help_handler))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^addcat\|"))
    app.add_handler(CallbackQueryHandler(category_menu_callback, pattern=r"^addmore\|"))
    app.add_handler(CallbackQueryHandler(payment_callback, pattern=r"^addpm\|"))
    app.add_handler(CallbackQueryHandler(cancel_add_callback, pattern=r"^addcancel$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_handler))
    app.add_error_handler(error_handler)

    print('Bot is running...')
    logger.info("Bot is running")

    #Start polling
    app.run_polling()



if __name__ == '__main__':
    main()
