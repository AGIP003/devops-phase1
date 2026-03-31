from flask import Flask, render_template, request, redirect, url_for
from finance_tracker.utils.storage import Storage
from app.routes import register_routes
from app.errors import register_error_handlers
from flask_cors import CORS
import logging

def create_app():
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:3000"])
    
    configure_logging(app)
    register_routes(app)
    register_error_handlers(app)

    return app

def configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    app.logger.info("Application started")

