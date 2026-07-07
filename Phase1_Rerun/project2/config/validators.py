import os

REQUIRED_VARS = [
    "SECRET_KEY",
    "MAIL_USERNAME",
    "MAIL_APP_PASSWORD",
] 
 
def validate_environment(required_vars=None):
    required = required_vars or REQUIRED_VARS
    missing = [name for name in required if not os.getenv(name)]
    if os.getenv("FLASK_ENV", "development").lower() in {"production", "prod"}:
        has_database_url = any(
            os.getenv(name)
            for name in (
                "DATABASE_URL",
                "DATABASE_PRIVATE_URL",
                "DATABASE_PUBLIC_URL",
                "POSTGRES_URL",
            )
        )
        has_database_parts = bool(os.getenv("DB_NAME") and os.getenv("DB_USER"))
        if not has_database_url and not has_database_parts:
            missing.append(
                "DATABASE_URL or DATABASE_PRIVATE_URL or DB_NAME+DB_USER"
            )

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
