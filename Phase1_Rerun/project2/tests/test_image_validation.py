from io import BytesIO

import pytest
from PIL import Image

import app.services.image_validation as image_validation
from app.services.image_validation import validate_receipt_image


pytestmark = pytest.mark.no_database


def create_image_bytes(image_format: str = "PNG", size: tuple[int, int] = (10, 10)) -> bytes:
    buffer = BytesIO()

    Image.new(
        "RGB",
        size,
        color="white",
    ).save(buffer, format=image_format)

    return buffer.getvalue()


def test_valid_png_is_accepted():
    data = create_image_bytes("PNG")

    result = validate_receipt_image(data)

    assert result.data == data
    assert result.media_type == "image/png"


def test_fake_image_is_rejected():
    with pytest.raises(
        ValueError,
        match="not a valid receipt image",
    ):
        validate_receipt_image(b"this is not an image")


def test_unsupported_image_format_is_rejected():
    gif_data = create_image_bytes("GIF")

    with pytest.raises(
        ValueError,
        match="Unsupported image type",
    ):
        validate_receipt_image(gif_data)


def test_excessive_pixel_count_is_rejected(monkeypatch):
    monkeypatch.setattr(
        image_validation,
        "MAX_RECEIPT_PIXELS",
        3,
    )

    data = create_image_bytes("PNG", size=(2, 2))

    with pytest.raises(
        ValueError,
        match="dimensions are too large",
    ):
        validate_receipt_image(data)


def test_oversized_file_is_rejected():
    oversized_data = b"x" * (
        image_validation.MAX_RECEIPT_BYTES + 1
    )

    with pytest.raises(
        ValueError,
        match="exceeds 4 MB",
    ):
        validate_receipt_image(oversized_data)