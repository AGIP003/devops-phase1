from bot.handlers.link import link_telegram_account
from bot.handlers.welcome import welcome_handler


async def start_handler(update, context):
    if context.args:
        await link_telegram_account(update, context, context.args[0].strip())
        return

    await welcome_handler(update, context)
