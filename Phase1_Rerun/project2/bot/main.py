import os
import logging
import sys
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
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
from bot.handlers.balance import balance_handler
from bot.handlers.help import help_handler
from bot.handlers.import_message import (
    IMPORT_CATEGORY,
    IMPORT_CONFIRM,
    IMPORT_DATE,
    IMPORT_DESCRIPTION,
    cancel_import_callback,
    cancel_import_command,
    automatic_import_handler,
    import_category_callback,
    import_description_handler,
    import_date_handler,
    import_message_handler,
    import_save_callback,
)
from bot.handlers.receipts import (
    RECEIPT_CATEGORY,
    RECEIPT_CONFIRM,
    RECEIPT_DATE,
    RECEIPT_DESCRIPTION,
    RECEIPT_PAYMENT,
    cancel_receipt_callback,
    cancel_receipt_command,
    handle_receipt_photo,
    receipt_category_callback,
    receipt_date_handler,
    receipt_description_handler,
    receipt_payment_callback,
    receipt_save_callback,
)
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
    app.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.PHOTO, handle_receipt_photo),
            ],
            states={
                RECEIPT_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        receipt_description_handler,
                    )
                ],
                RECEIPT_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        receipt_date_handler,
                    )
                ],
                RECEIPT_CATEGORY: [
                    CallbackQueryHandler(
                        receipt_category_callback,
                        pattern=r"^receiptcat\|",
                    ),
                    CallbackQueryHandler(
                        cancel_receipt_callback,
                        pattern=r"^receiptcancel$",
                    ),
                ],
                RECEIPT_PAYMENT: [
                    CallbackQueryHandler(
                        receipt_payment_callback,
                        pattern=r"^receiptpm\|",
                    ),
                    CallbackQueryHandler(
                        cancel_receipt_callback,
                        pattern=r"^receiptcancel$",
                    ),
                ],
                RECEIPT_CONFIRM: [
                    CallbackQueryHandler(
                        receipt_save_callback,
                        pattern=r"^receiptsave$",
                    ),
                    CallbackQueryHandler(
                        cancel_receipt_callback,
                        pattern=r"^receiptcancel$",
                    ),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_receipt_command),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("import", import_message_handler),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    automatic_import_handler,
                ),
            ],
            states={
                IMPORT_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        import_description_handler,
                    )
                ],
                IMPORT_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        import_date_handler,
                    )
                ],
                IMPORT_CATEGORY: [
                    CallbackQueryHandler(
                        import_category_callback,
                        pattern=r"^importcat\|",
                    ),
                    CallbackQueryHandler(
                        cancel_import_callback,
                        pattern=r"^importcancel$",
                    ),
                ],
                IMPORT_CONFIRM: [
                    CallbackQueryHandler(
                        import_save_callback,
                        pattern=r"^importsave\|(?:once|remember)$",
                    ),
                    CallbackQueryHandler(
                        cancel_import_callback,
                        pattern=r"^importcancel$",
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_import_command)],
        )
    )
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^addcat\|"))
    app.add_handler(CallbackQueryHandler(category_menu_callback, pattern=r"^addmore\|"))
    app.add_handler(CallbackQueryHandler(payment_callback, pattern=r"^addpm\|"))
    app.add_handler(CallbackQueryHandler(cancel_add_callback, pattern=r"^addcancel$"))
    app.add_error_handler(error_handler)

    print('Bot is running...')
    logger.info("Bot is running")

    #Start polling
    app.run_polling()



if __name__ == '__main__':
    main()
