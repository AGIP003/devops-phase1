from __future__ import annotations
from telegram import Message
from app.services.image_validation import ValidatedImage, validate_receipt_image


async def download_largest_receipt(message: Message) -> ValidatedImage:
    if not message.photo:
        raise ValueError("No photo was attached")
    largest = message.photo[-1]   # Telegram sends multiple sizes, last is largest
    telegram_file = await largest.get_file()
    content = await telegram_file.download_as_bytearray()
    return validate_receipt_image(bytes(content))