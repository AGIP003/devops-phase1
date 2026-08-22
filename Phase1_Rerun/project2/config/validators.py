from __future__ import annotations
import os

from decimal import Decimal, InvalidOperation

REQUIRED_VARS = [
    "DATABASE_URL",
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "MAIL_USERNAME",
    "MAIL_APP_PASSWORD",
    "GOOGLE_CLIENT_ID",
] 
 
def validate_environment(required_vars=None):
    required = required_vars or REQUIRED_VARS
    missing = [name for name in required if not os.getenv(name)]
    
    if os.getenv("FLASK_ENV", "development").lower() in {"production", "prod"}:
        if missing:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + "\nCheck your .env file locally or Railway variables in production."
            )
    else:
        pass

def get_env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_env_int(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def get_env_list(name, default=None, separator=","):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default or [])
    return [item.strip() for item in raw.split(separator) if item.strip()]

def get_env_decimal(name: str, default: str) -> Decimal:
    try:
        value = Decimal(os.getenv(name, default))
    except InvalidOperation as exc:
        raise RuntimeError(f"{name} must be a decimal number") from exc

    if not value.is_finite() or value < 0:
        raise RuntimeError(
            f"{name} must be a finite, non-negative decimal number"
        )

    return value
