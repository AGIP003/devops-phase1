from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from time import perf_counter

from flask import current_app
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from pydantic import ValidationError

from app.schemas import ReceiptParseResult
from app.services.ai_support import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
    AIUsageMetadata,
    build_usage_metadata,
    create_openai_client,
    get_ai_model,
    log_ai_invalid_response,
    log_ai_provider_failure,
)
from app.services.image_validation import ValidatedImage
from finance_tracker.utils.validations import (
    ALLOWED_TRANSACTION_CATEGORIES,
)


logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES = ", ".join(
    ALLOWED_TRANSACTION_CATEGORIES["expense"]
)

RECEIPT_PROMPT = f"""
Extract one purchase receipt for a personal-finance application.

Allowed expense categories:
{EXPENSE_CATEGORIES}

Rules:
- Extract the merchant, final amount paid, currency and date when visible.
- Include line items only when they are legible.
- Use only one of the allowed expense categories.
- Preserve an explicitly shown three-letter currency.
- Use KES only when no other currency is shown.
- Never convert currencies.
- Never invent hidden digits or missing values.
- If totals conflict, use the clearly labelled final amount and set
  needs_review=true.
- If the image is unreadable or is not a receipt, return can_parse=false,
  receipt=null and a short reason.
- If parsing succeeds, return can_parse=true, reason=null and the receipt.
""".strip()


@dataclass(frozen=True, slots=True)
class AIReceiptParseResult:
    extraction: ReceiptParseResult
    usage: AIUsageMetadata


def parse_receipt_image(
    image: ValidatedImage,
) -> AIReceiptParseResult:
    if not isinstance(image, ValidatedImage):
        raise TypeError(
            "Receipt image must be validated before AI parsing"
        )

    if not image.data:
        raise ValueError("Receipt image cannot be empty")

    model = get_ai_model()
    client = create_openai_client()

    encoded_image = base64.b64encode(
        image.data
    ).decode("ascii")

    started_at = perf_counter()

    try:
        response = client.responses.parse(
            model=model,
            instructions=RECEIPT_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": (
                                f"data:{image.media_type};"
                                f"base64,{encoded_image}"
                            ),
                            "detail": "auto",
                        }
                    ],
                }
            ],
            text_format=ReceiptParseResult,
            reasoning={
                "effort": current_app.config[
                    "AI_REASONING_EFFORT"
                ],
            },
            max_output_tokens=current_app.config[
                "AI_RECEIPT_MAX_OUTPUT_TOKENS"
            ],
            store=False,
        )
    except (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
    ) as error:
        log_ai_provider_failure(
            logger,
            operation="receipt_parse",
            error=error,
        )
        raise AIServiceUnavailableError(
            "AI receipt parsing is temporarily unavailable"
        ) from error
    except APIStatusError as error:
        log_ai_provider_failure(
            logger,
            operation="receipt_parse",
            error=error,
        )
        raise AIServiceUnavailableError(
            "AI receipt parsing is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        log_ai_invalid_response(
            logger,
            operation="receipt_parse",
            reason=type(error).__name__,
        )
        raise AIInvalidResponseError(
            "AI returned an invalid receipt response"
        ) from error

    if response.status != "completed":
        log_ai_invalid_response(
            logger,
            operation="receipt_parse",
            reason=f"status_{response.status}",
            provider_request_id=getattr(response, "_request_id", None),
        )
        raise AIInvalidResponseError(
            f"AI receipt response ended with status "
            f"{response.status!r}"
        )

    extraction = response.output_parsed

    if extraction is None:
        log_ai_invalid_response(
            logger,
            operation="receipt_parse",
            reason="missing_parsed_output",
            provider_request_id=getattr(response, "_request_id", None),
        )
        raise AIInvalidResponseError(
            "AI receipt response contained no parsed output"
        )

    if (
        extraction.can_parse
        and extraction.receipt is not None
        and extraction.receipt.suggested_category
        not in ALLOWED_TRANSACTION_CATEGORIES["expense"]
    ):
        log_ai_invalid_response(
            logger,
            operation="receipt_parse",
            reason="unsupported_category",
            provider_request_id=getattr(response, "_request_id", None),
        )
        raise AIInvalidResponseError(
            "AI returned an unsupported receipt category"
        )

    return AIReceiptParseResult(
        extraction=extraction,
        usage=build_usage_metadata(
            response,
            model=model,
            started_at=started_at,
        ),
    )
