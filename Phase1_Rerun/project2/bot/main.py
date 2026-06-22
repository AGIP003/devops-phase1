import os
import logging
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    print('Bot is running...')
    logger.info("Bot is running")

    #Start polling
    app.run_polling()



if __name__ == '__main__':
    main()
