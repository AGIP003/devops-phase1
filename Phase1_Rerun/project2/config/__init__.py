import os
from dotenv import load_dotenv

load_dotenv()

from .settings import BaseConfig, DevelopmentConfig, ProductionConfig
from .validators import validate_environment

__all__ = [
    "BaseConfig",
    "DevelopmentConfig",
    "ProductionConfig",
    "validate_environment",
    "get_config",
]


def get_config(env=None):
    env = (env or os.getenv("FLASK_ENV", "development")).lower()
    if env in {"production", "prod"}:
        return ProductionConfig
    return DevelopmentConfig
