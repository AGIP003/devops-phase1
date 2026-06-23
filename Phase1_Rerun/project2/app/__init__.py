from flask import Flask
from app.routes import register_routes
from app.errors import register_error_handlers
from flask_cors import CORS
from app.extensions import bcrypt, mail, limiter
from app.auth_routes import auth_bp
from app.telegram_routes import telegram_bp
from flask_talisman import Talisman
from app.docs import api 
from config import get_config, validate_environment
from flask import g, request
import logging
import os
import sys
import time


def create_app():
    validate_environment()
    app = Flask(__name__)
    app.config.from_object(get_config())

    allowed_origins = app.config.get(
        "CORS_ORIGINS",
        ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174",
        "http://127.0.0.1:5174"],
    )

    CORS(
        app,
        resources={
            r"/api/.*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
                "max_age": 3600,
            }
        },
    )
    configure_logging(app)
    register_request_logging(app)
    register_routes(app)
    register_error_handlers(app)
    bcrypt.init_app(app)

    Talisman(
        app,
        force_https=False,
        strict_transport_security=False,
        content_security_policy=False,
    )
    # Register auth blueprint
    try:
        app.register_blueprint(auth_bp)
        app.logger.info("✓ Auth blueprint registered successfully")
        app.register_blueprint(telegram_bp)
        app.logger.info("✓ Telegram blueprint registered successfully")
    except Exception as e:
        app.logger.error("✗ Failed to register auth blueprint: %s", e)
        import traceback
        traceback.print_exc()

    # Register documentation-only Flask-RESTX routes after the real routes.
    # Several docs resources intentionally share the same URL paths as the
    # application. Registering them first causes their empty `post`/`get`
    # methods to handle requests and return `null` instead of real API data.
    api.init_app(app)

    mail.init_app(app)
    limiter.init_app(app)
    return app


def configure_logging(app):
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    app.logger.info("Application started")


def register_request_logging(app):
    slow_request_ms = int(os.getenv("SLOW_REQUEST_MS", "1000"))

    @app.before_request
    def start_request_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - g.request_started_at) * 1000
        log_method = app.logger.warning if duration_ms >= slow_request_ms else app.logger.info
        log_method(
            "request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
