import secrets
import os
import json
from hashlib import sha256
from hmac import compare_digest
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, abort, g, jsonify, request

from app.db import (
    consume_telegram_link_token,
    create_telegram_link_token,
    get_user_by_telegram_id,
    get_telegram_link_status,
    get_telegram_preferences,
    telegram_linking_schema_ready,
    update_telegram_preferences,
)
from app.extensions import limiter
from app.middleware import login_required
from config import get_config
from finance_tracker.utils.validations import (
    ValidationError,
    validate_category,
    validate_payment_method,
)


telegram_bp = Blueprint("telegram", __name__, url_prefix="/api/telegram")
config = get_config()
SECRET_KEY = config.SECRET_KEY
LINK_TOKEN_TTL_MINUTES = 10
SCHEMA_SETUP_MESSAGE = (
    "Telegram linking is temporarily unavailable. Please try again shortly."
)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def schema_not_ready_response():
    if telegram_linking_schema_ready():
        return None
    return jsonify({"error": "Telegram unavailable", "message": SCHEMA_SETUP_MESSAGE}), 503


def issue_access_token(user):
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def require_bot_auth():
    supplied_auth = request.headers.get("X-Telegram-Bot-Auth", "")
    if not TELEGRAM_BOT_TOKEN:
        return jsonify(
            {
                "error": "Telegram bot setup incomplete",
                "message": "Telegram is temporarily unavailable. Please try again shortly.",
            }
        ), 503

    expected_auth = sha256(TELEGRAM_BOT_TOKEN.encode("utf-8")).hexdigest()
    if not supplied_auth or not compare_digest(supplied_auth, expected_auth):
        abort(401, description="Invalid Telegram bot credentials")
    return None


@telegram_bp.route("/link-token", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def generate_link_token():
    setup_error = schema_not_ready_response()
    if setup_error:
        return setup_error

    user_id = g.current_user["user_id"]
    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        minutes=LINK_TOKEN_TTL_MINUTES
    )
    link = create_telegram_link_token(user_id, token, expires_at)

    return jsonify(
        {
            "message": "Telegram link code generated",
            "token": link["token"],
            "expires_at": link["expires_at"].isoformat() + "Z",
            "expires_in_seconds": LINK_TOKEN_TTL_MINUTES * 60,
        }
    ), 201


@telegram_bp.route("/verify", methods=["POST"])
@limiter.limit("10 per minute")
def verify_link_token():
    setup_error = schema_not_ready_response()
    if setup_error:
        return setup_error

    data = request.get_json(silent=True) or {}
    token = str(data.get("token", "")).strip()
    telegram_id = data.get("telegram_id")

    if not token or telegram_id is None:
        abort(400, description="Token and telegram_id are required")

    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        abort(400, description="telegram_id must be an integer")

    if telegram_id <= 0:
        abort(400, description="telegram_id must be a positive integer")

    user, error = consume_telegram_link_token(token, telegram_id)
    if error == "invalid":
        abort(400, description="Invalid Telegram link code")
    if error == "used":
        abort(400, description="Telegram link code has already been used")
    if error == "expired":
        abort(400, description="Telegram link code has expired")
    if error == "telegram_in_use":
        abort(409, description="This Telegram account is linked to another user")

    return jsonify(
        {
            "message": "Telegram account linked successfully",
            "token": issue_access_token(user),
            "user": {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "telegram_id": user["telegram_id"],
            },
        }
    ), 200


@telegram_bp.route("/status", methods=["GET"])
@login_required
def telegram_link_status():
    setup_error = schema_not_ready_response()
    if setup_error:
        return setup_error

    status = get_telegram_link_status(g.current_user["user_id"])
    if status is None:
        abort(404, description="User not found")

    return jsonify(
        {
            "linked": status["telegram_id"] is not None,
            "telegram_id": status["telegram_id"],
        }
    ), 200


@telegram_bp.route("/session", methods=["POST"])
@limiter.limit("30 per minute")
def telegram_session():
    bot_auth_error = require_bot_auth()
    if bot_auth_error:
        return bot_auth_error

    setup_error = schema_not_ready_response()
    if setup_error:
        return setup_error

    data = request.get_json(silent=True) or {}
    telegram_id = data.get("telegram_id")
    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        abort(400, description="telegram_id must be an integer")

    user = get_user_by_telegram_id(telegram_id)
    if user is None:
        return jsonify({"linked": False}), 200

    return jsonify(
        {
            "linked": True,
            "token": issue_access_token(user),
            "user": {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user.get("role", "user"),
                "telegram_id": user["telegram_id"],
            },
        }
    ), 200


@telegram_bp.route("/preferences", methods=["GET", "PUT"])
@login_required
def telegram_preferences():
    user_id = g.current_user["user_id"]

    if request.method == "GET":
        preferences = get_telegram_preferences(user_id)
        return jsonify(preferences), 200

    data = request.get_json(silent=True) or {}
    payment_method = data.get("default_payment_method")
    aliases = data.get("category_aliases")

    if aliases is not None and not isinstance(aliases, dict):
        abort(400, description="category_aliases must be an object")

    try:
        if payment_method is not None:
            payment_method = validate_payment_method(payment_method)
        if aliases is not None:
            clean_aliases = {}
            for alias, category in aliases.items():
                clean_alias = str(alias).strip().lower()
                clean_category = str(category).strip().lower()
                if not clean_alias or len(clean_alias) > 40:
                    abort(400, description="Aliases must be between 1 and 40 characters")

                category_type = None
                for candidate_type in ("income", "expense"):
                    try:
                        validate_category(candidate_type, clean_category)
                        category_type = candidate_type
                        break
                    except ValidationError:
                        continue
                if category_type is None:
                    abort(400, description=f"Invalid category for alias: {clean_category}")
                clean_aliases[clean_alias] = clean_category
            aliases = clean_aliases
    except ValidationError as error:
        abort(400, description=str(error))

    preferences = update_telegram_preferences(
        user_id,
        default_payment_method=payment_method,
        category_aliases=json.dumps(aliases) if aliases is not None else None,
    )
    return jsonify(preferences), 200
