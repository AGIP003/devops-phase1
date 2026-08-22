from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from time import perf_counter
from typing import Any

from flask import current_app
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
    )
