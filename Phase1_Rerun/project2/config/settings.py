import os
from urllib.parse import quote_plus

from .validators import get_env_bool, get_env_int, get_env_list

def normalize_database_url(url):
    """Railway gives postgres://, SQLAlchemy needs postgresql://"""
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def get_database_url():
    direct_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_PRIVATE_URL")
        or os.getenv("DATABASE_PUBLIC_URL")
        or os.getenv("POSTGRES_URL")
    )
    if direct_url:
        return normalize_database_url(direct_url)

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    if db_name and db_user:
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = get_env_int("DB_PORT", 5432)
        db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
        auth = quote_plus(db_user)
        if db_password:
            auth = f"{auth}:{db_password}"
        return f"postgresql://{auth}@{db_host}:{db_port}/{quote_plus(db_name)}"

    if os.getenv("FLASK_ENV", "development").lower() not in {"production", "prod"}:
        return "sqlite:///:memory:"

    return None

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_USE_URL = get_env_bool("DB_USE_URL", False)
    ENV = os.getenv("FLASK_ENV", "development").lower()

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = get_env_int("DB_PORT", 5432)
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    JSON_SORT_KEYS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = get_env_int("MAIL_PORT", 587)
    MAIL_USE_TLS = get_env_bool("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_APP_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    #SQLALCHEMY
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


class ProductionConfig(BaseConfig):
    DEBUG = False
