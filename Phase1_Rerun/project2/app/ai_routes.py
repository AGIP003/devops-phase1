from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from app.extensions import limiter
from app.middleware import login_required
from app.services.ai_budget_service import (
    AIBudgetExceededError,
    run_receipt_ai,
    run_transaction_ai,
)
from app.services.ai_support import (
    AIConfigurationError,
    AIInvalidResponseError,
    AIServiceUnavailableError,
)
from app.services.image_validation import validate_receipt_image


ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


def _authenticated_user_limit_key() -> str:
    return f"ai-user:{g.current_user['user_id']}"


def _private_json(payload: dict, status_code: int = 200):
    response = jsonify(payload)
    response.headers["Cache-Control"] = "private, no-store"
    return response, status_code


def _ai_error_response(error: Exception):
    if isinstance(error, AIBudgetExceededError):
        return _private_json(
            {"error": "AI daily budget reached", "message": str(error)},
            429,
        )
    if isinstance(error, AIConfigurationError):
        return _private_json(
            {
                "error": "AI is not configured",
                "message": "AI assistance is currently unavailable",
            },
            503,
        )
    if isinstance(error, AIServiceUnavailableError):
        return _private_json(
            {"error": "AI provider unavailable", "message": str(error)},
            503,
        )
    if isinstance(error, AIInvalidResponseError):
        return _private_json(
            {"error": "Invalid AI response", "message": str(error)},
            502,
        )
    raise error


@ai_bp.post("/transactions/preview")
@login_required
@limiter.limit("10 per hour", key_func=_authenticated_user_limit_key)
def preview_ai_transaction():
    if not current_app.config["AI_FALLBACK_ENABLED"]:
        return _private_json(
            {
                "error": "AI assistance disabled",
                "message": "AI assistance is currently unavailable",
            },
            503,
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _private_json(
            {"error": "Invalid request", "message": "Payload must be an object"},
            400,
        )

    text = data.get("text")
    try:
        result = run_transaction_ai(text)
    except ValueError as error:
        return _private_json(
            {"error": "Invalid request", "message": str(error)},
            400,
        )
    except (
        AIBudgetExceededError,
        AIConfigurationError,
        AIServiceUnavailableError,
        AIInvalidResponseError,
    ) as error:
        return _ai_error_response(error)

    return _private_json(result.extraction.model_dump(mode="json"))


@ai_bp.post("/receipts/preview")
@login_required
@limiter.limit("5 per hour", key_func=_authenticated_user_limit_key)
def preview_ai_receipt():
    if not current_app.config["AI_FALLBACK_ENABLED"]:
        return _private_json(
            {
                "error": "AI assistance disabled",
                "message": "AI assistance is currently unavailable",
            },
            503,
        )

    uploaded_image = request.files.get("image")
    if uploaded_image is None:
        return _private_json(
            {
                "error": "Invalid request",
                "message": "A receipt image is required",
            },
            400,
        )

    image_bytes = uploaded_image.stream.read(4 * 1024 * 1024 + 1)
    try:
        image = validate_receipt_image(image_bytes)
        result = run_receipt_ai(image)
    except ValueError as error:
        return _private_json(
            {"error": "Invalid receipt image", "message": str(error)},
            400,
        )
    except (
        AIBudgetExceededError,
        AIConfigurationError,
        AIServiceUnavailableError,
        AIInvalidResponseError,
    ) as error:
        return _ai_error_response(error)

    return _private_json(result.extraction.model_dump(mode="json"))
