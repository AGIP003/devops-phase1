from flask import Flask, render_template, request, redirect, url_for
from finance_tracker.utils.storage import Storage
from app.routes import register_routes
from app.errors import register_error_handlers
from flask_cors import CORS
from app.extensions import bcrypt, mail, limiter
from app.auth_routes import auth_bp
from flask_talisman import Talisman
import logging
import os

def create_app():
    app = Flask(__name__)

    
    CORS(
        app, 
        resources= {r"/api/.*": {
                                    "origins":["http://localhost:3000", 
                                               "http://localhost:5173",
                                               "http://127.0.0.1:5173",
                                               "http://localhost:5174",
                                               "http://127.0.0.1:5174"],
                                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                    "allow_headers": ["Content-Type", "Authorization"],
                                    "expose_headers": ["Content-Type", "Authorization"],
                                    "supports_credentials": True,
                                    "max_age": 3600  # Cache preflight requests for 1 hour

                                }}
    )
    configure_logging(app)
    configure_mail(app)
    register_routes(app)
    register_error_handlers(app)
    bcrypt.init_app(app)

    Talisman(app,
             force_https=False,
             strict_transport_security=False,
             content_security_policy=False
             )
    # Register auth blueprint
    try:
        app.register_blueprint(auth_bp)
        app.logger.info(f"✓ Auth blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"✗ Failed to register auth blueprint: {e}")
        import traceback
        traceback.print_exc()
    mail.init_app(app)
    limiter.init_app(app)
    return app

def configure_mail(app):
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_APP_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("MAIL_USERNAME")

def configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    app.logger.info("Application started")
