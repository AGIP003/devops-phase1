import os

from .validators import get_env_bool, get_env_int, get_env_list
from sqlalchemy.engine import make_url


def normalize_database_url(url):
    """Railway gives postgres://, SQLAlchemy needs postgresql://"""
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Configure it for the current environment."
        )

    return normalize_database_url(database_url.strip())


def get_test_database_url():
    test_database_url = os.getenv("TEST_DATABASE_URL")

    if not test_database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL is missing. "
            "Tests require a separate PostgreSQL database."
        )
    test_database_url = normalize_database_url(test_database_url.strip())

    development_database_url = normalize_database_url(
        os.getenv("DATABASE_URL", "").strip()
    )

    if test_database_url == development_database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must not equal DATABASE_URL."
        )

    database_name = make_url(test_database_url).database

    if not database_name or not database_name.endswith("_test"):
        raise RuntimeError(
            "Refusing to run database tests: "
            "the test database name must end with '_test'."
        )
    return test_database_url


class BaseConfig:
    JWT_ALGORITHM = "HS256"
    JWT_ISSUER = os.getenv("JWT_ISSUER", "moneytiq-api")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "moneytiq-web")
    JWT_ACCESS_TOKEN_MINUTES = get_env_int(
        "JWT_ACCESS_TOKEN_MINUTES",
        60,
    )
    RECENT_AUTH_MAX_AGE_MINUTES = get_env_int(
        "RECENT_AUTH_MAX_AGE_MINUTES",
        10,
    )

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

    FOREX_API_BASE_URL = os.getenv(
        "FOREX_API_BASE_URL",
        "https://api.frankfurter.dev/v2",
    )
    FOREX_PROVIDER = os.getenv("FOREX_PROVIDER", "CBK")
    FOREX_CACHE_TTL_SECONDS = get_env_int(
        "FOREX_CACHE_TTL_SECONDS",
        21600,
    )
    FOREX_CONNECT_TIMEOUT_SECONDS = get_env_int(
        "FOREX_CONNECT_TIMEOUT_SECONDS",
        3,
    )
    FOREX_READ_TIMEOUT_SECONDS = get_env_int(
        "FOREX_READ_TIMEOUT_SECONDS",
        10,
    )

    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ENV = os.getenv("FLASK_ENV", "development").lower()

    JSON_SORT_KEYS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = get_env_int("MAIL_PORT", 587)
    MAIL_USE_TLS = get_env_bool("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_APP_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO") == "true"

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    _default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    env_origins = get_env_list("CORS_ORIGINS", default=_default_origins)
    if os.getenv("FLASK_ENV", "development").lower() not in {"production", "prod"}:
        # Always allow local development hosts alongside any configured origins.
        CORS_ORIGINS = list(dict.fromkeys(_default_origins + env_origins))
    else:
        CORS_ORIGINS = env_origins


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    JWT_SECRET_KEY = "testing-only-jwt-secret-never-use-in-production"
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_ECHO = False
    RATELIMIT_ENABLED = False
    GOOGLE_CLIENT_ID = "test-client.apps.googleusercontent.com"


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
