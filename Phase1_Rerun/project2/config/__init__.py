import os
from dotenv import load_dotenv

load_dotenv()

from .settings import (
    BaseConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    get_test_database_url,
)
from .validators import validate_environment

__all__ = [
    "BaseConfig",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "validate_environment",
    "get_config",
    "get_test_database_url",
]


def get_config(env=None):
    env = (env or os.getenv("FLASK_ENV", "development")).lower()
    if env == "testing":
        return TestingConfig
    if env in {"production", "prod"}:
        return ProductionConfig

    return DevelopmentConfig
