from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

MAX_RECEIPT_BYTES = 4 * 1024 * 1024
MAX_RECEIPT_PIXELS = 20_000_000


@dataclass(frozen=True, slots=True)
class ValidatedImage:
    data: bytes
    media_type: str


def validate_receipt_image(data: bytes) -> ValidatedImage:
    if not isinstance(data, bytes):
        raise TypeError("Receipt image must contain bytes")

    if not data:
        raise ValueError("The image is empty")

    if len(data) > MAX_RECEIPT_BYTES:
        raise ValueError("Receipt image exceeds 4 MB")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning,
            )

            with Image.open(BytesIO(data)) as image:
                image_format = image.format
                width, height = image.size

                if image_format not in ALLOWED_IMAGE_FORMATS:
                    raise ValueError(
                        f"Unsupported image type: {image_format}"
                    )

                if width <= 0 or height <= 0:
                    raise ValueError(
                        "Receipt image has invalid dimensions"
                    )

                if width * height > MAX_RECEIPT_PIXELS:
                    raise ValueError(
                        "Receipt image dimensions are too large"
                    )

                image.verify()

    except ValueError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ) as error:
        raise ValueError(
            "The uploaded file is not a valid receipt image"
        ) from error

    return ValidatedImage(
        data=data,
        media_type=ALLOWED_IMAGE_FORMATS[image_format],
    )