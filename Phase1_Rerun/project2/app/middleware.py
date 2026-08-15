import jwt
from functools import wraps
from flask import jsonify, request, g, current_app, abort
from uuid import UUID
from datetime import UTC, datetime, timedelta

from app.services.token_service import decode_access_token
from app.services.user_service import get_user_by_public_id

def recent_authentication_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        payload = getattr(g, "token_payload", None)

        if not isinstance(payload, dict):
            abort(401, description="Recent authentication required")

        auth_time = payload.get("auth_time")

        if not isinstance(auth_time, (int, float)):
            abort(401, description="Recent authentication required")

        authenticated_at = datetime.fromtimestamp(auth_time, UTC)
        now = datetime.now(UTC)
        maximum_age = timedelta(
            minutes=current_app.config[
                "RECENT_AUTH_MAX_AGE_MINUTES"
            ]
        )

        if authenticated_at > now:
            abort(401, description="Invalid authentication time")

        if now - authenticated_at > maximum_age:
            abort(401, description="Recent authentication required")

        return function(*args, **kwargs)

    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get("Authorization", "")

        #Check if it starts  with Bearer
        if not auth or not auth.startswith("Bearer "):
            abort(401, description = "Invalid or missing Authorization")

        #Extract the token
        parts = auth.split(" ")
        if len(parts) != 2:
            abort(401, description="Invalid Authorization header format")

        token = parts[1]
        
        try:
            payload = decode_access_token(token)
            public_id = UUID(str(payload["sub"]))
        except jwt.ExpiredSignatureError:
            abort(401, description="Token has expired")
        except (jwt.InvalidTokenError, TypeError, ValueError):
            abort(401, description="Invalid token") 

        user = get_user_by_public_id(public_id)

        if user is None:
            abort(401, description="Invalid token")

        if payload["token_version"] != user.token_version:
            abort(401, description="Invalid token")

        g.authenticated_user = user
        g.token_payload = payload

        g.current_user = {
            "user_id": user.id,
            "public_id": str(user.public_id),
            "email": user.email,
            "role": user.role or "user",
        }   

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorators to restrict routes to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not hasattr(g, 'current_user'):
            abort(401, "Authentication required")

        if  not isinstance(g.current_user, dict):
            abort(403, description="Invalid data format")

        user_role = g.current_user.get("role")
        if user_role != "admin":
            abort(403, description="Admin access required")

        return f(*args, **kwargs)
    return decorated_function
        