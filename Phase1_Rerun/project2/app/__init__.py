from flask import Flask, render_template, request, redirect, url_for
from finance_tracker.utils.storage import Storage
from app.routes import register_routes
from app.errors import register_error_handlers
from flask_cors import CORS
from app.extensions import bcrypt
from app.auth_routes import auth_bp
import logging

def create_app():
    app = Flask(__name__)
    CORS(
        app, 
        resources= {r"/*": {"origins":"http://localhost:3000"}}
    )
    configure_logging(app)
    register_routes(app)
    register_error_handlers(app)
    bcrypt.init_app(app)
    
    # Register auth blueprint
    try:
        app.register_blueprint(auth_bp)
        app.logger.info(f"✓ Auth blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"✗ Failed to register auth blueprint: {e}")
        import traceback
        traceback.print_exc()
    
    return app

def configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    app.logger.info("Application started")

