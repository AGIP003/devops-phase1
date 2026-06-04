import os

from .validators import get_env_bool, get_env_int, get_env_list


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

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    CORS_ORIGINS = get_env_list(
        "CORS_ORIGINS",
        default=["http://localhost:5173"],
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False