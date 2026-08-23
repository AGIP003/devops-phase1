from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import logging
from time import perf_counter
from typing import Any

from flask import current_app, g, has_request_context
from openai import OpenAI


LUNA_INPUT_COST_PER_MILLION = Decimal("0.20")
LUNA_CACHED_INPUT_COST_PER_MILLION = Decimal("0.02")
LUNA_OUTPUT_COST_PER_MILLION = Decimal("1.20")
ONE_MILLION = Decimal("1000000")

SUPPORTED_AI_MODELS = {"gpt-5.6-luna"}


class AIConfigurationError(RuntimeError):
    """AI cannot run because application configuration is invalid."""


class AIServiceUnavailableError(RuntimeError):
    """The configured AI provider could not complete the request."""


class AIInvalidResponseError(RuntimeError):
    """The provider responded, but its result could not be safely used."""


@dataclass(frozen=True, slots=True)
class AIUsageMetadata:
    model: str
    latency_ms: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal
    provider_request_ids: tuple[str, ...] = ()


def current_request_id() -> str:
    if has_request_context():
        return str(getattr(g, "request_id", "unavailable"))
    return "outside-request"


def _provider_error_code(error: Exception) -> str | None:
    code = getattr(error, "code", None)
    if code:
        return str(code)
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return None
    details = body.get("error", body)
    if isinstance(details, dict) and details.get("code"):
        return str(details["code"])
    return None


def log_ai_provider_failure(
    logger: logging.Logger,
    *,
    operation: str,
    error: Exception,
) -> None:
    """Record provider diagnostics without prompts, credentials, or finance data."""

    logger.warning(
        "ai_provider_failure request_id=%s operation=%s error_type=%s "
        "status_code=%s provider_request_id=%s error_code=%s",
        current_request_id(),
        operation,
        type(error).__name__,
        getattr(error, "status_code", None),
        getattr(error, "request_id", None),
        _provider_error_code(error),
    )


def log_ai_invalid_response(
    logger: logging.Logger,
    *,
    operation: str,
    reason: str,
    provider_request_id: str | None = None,
) -> None:
    logger.warning(
        "ai_invalid_response request_id=%s operation=%s reason=%s "
        "provider_request_id=%s",
        current_request_id(),
        operation,
        reason,
        provider_request_id,
    )


def get_ai_model() -> str:
    model = str(
        current_app.config.get("OPENAI_TRANSACTION_MODEL", "")
    ).strip()

    if model not in SUPPORTED_AI_MODELS:
        raise AIConfigurationError(
            f"Unsupported AI model configuration: {model!r}"
        )

    return model


def get_openai_api_key() -> str:
    api_key = str(
        current_app.config.get("OPENAI_API_KEY") or ""
    ).strip()

    if not api_key:
        raise AIConfigurationError(
            "OPENAI_API_KEY is not configured"
        )

    return api_key


def create_openai_client() -> OpenAI:
    api_key = get_openai_api_key()

    return OpenAI(
        api_key=api_key,
        timeout=current_app.config["AI_REQUEST_TIMEOUT_SECONDS"],
        max_retries=0,
    )


def estimate_luna_cost(
    *,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
) -> Decimal:
    uncached_input_tokens = max(
        input_tokens - cached_input_tokens,
        0,
    )

    input_cost = (
        Decimal(uncached_input_tokens)
        * LUNA_INPUT_COST_PER_MILLION
        / ONE_MILLION
    )
    cached_input_cost = (
        Decimal(cached_input_tokens)
        * LUNA_CACHED_INPUT_COST_PER_MILLION
        / ONE_MILLION
    )
    output_cost = (
        Decimal(output_tokens)
        * LUNA_OUTPUT_COST_PER_MILLION
        / ONE_MILLION
    )

    return (
        input_cost + cached_input_cost + output_cost
    ).quantize(Decimal("0.00000001"))


def build_usage_metadata(
    response: Any,
    *,
    model: str,
    started_at: float,
) -> AIUsageMetadata:
    usage = response.usage

    input_tokens = int(
        getattr(usage, "input_tokens", 0) or 0
    )
    output_tokens = int(
        getattr(usage, "output_tokens", 0) or 0
    )

    input_details = getattr(
        usage,
        "input_tokens_details",
        None,
    )
    cached_input_tokens = int(
        getattr(input_details, "cached_tokens", 0) or 0
    )

    return AIUsageMetadata(
        model=model,
        latency_ms=round(
            (perf_counter() - started_at) * 1000
        ),
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimate_luna_cost(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
        ),
        provider_request_ids=(
            (str(response._request_id),)
            if getattr(response, "_request_id", None)
            else ()
        ),
    )


def combine_usage_metadata(*items: AIUsageMetadata) -> AIUsageMetadata:
    if not items:
        raise ValueError("At least one usage item is required")
    models = {item.model for item in items}
    if len(models) != 1:
        raise ValueError("Cannot combine usage from different models")
    return AIUsageMetadata(
        model=items[0].model,
        latency_ms=sum(item.latency_ms for item in items),
        input_tokens=sum(item.input_tokens for item in items),
        cached_input_tokens=sum(item.cached_input_tokens for item in items),
        output_tokens=sum(item.output_tokens for item in items),
        estimated_cost_usd=sum(
            (item.estimated_cost_usd for item in items),
            Decimal("0"),
        ),
        provider_request_ids=tuple(
            request_id
            for item in items
            for request_id in item.provider_request_ids
        ),
    )
