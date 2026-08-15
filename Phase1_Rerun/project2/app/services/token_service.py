from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from flask import current_app

from app.models.user import User


def issue_access_token(
    user: User,
    *,
    authenticated_at: datetime | None = None,
) -> str:
    now = datetime.now(UTC)
    auth_time = authenticated_at or now
    configured_lifetime = timedelta(
        minutes=current_app.config["JWT_ACCESS_TOKEN_MINUTES"]
    )

    secret_key = current_app.config["JWT_SECRET_KEY"]
    algorithm = current_app.config["JWT_ALGORITHM"]
    issuer = current_app.config["JWT_ISSUER"]
    audience = current_app.config["JWT_AUDIENCE"]

    payload = {
        "sub": str(user.public_id),
        "token_version": user.token_version,
        "token_type": "access",
        "iat": now,
        "auth_time": int(auth_time.timestamp()),
        "exp": now + configured_lifetime,
        "jti": str(uuid4()),
        "iss": issuer,
        "aud": audience,
    }

    return jwt.encode(payload, secret_key, algorithm=algorithm)

def decode_access_token(token: str) -> dict[str, object]:
    secret_key = current_app.config["JWT_SECRET_KEY"]
    algorithm = current_app.config["JWT_ALGORITHM"]
    issuer = current_app.config["JWT_ISSUER"]
    audience = current_app.config["JWT_AUDIENCE"]

    options = {
        "require": [
            "sub",
            "exp",
            "iat",
            "auth_time",
            "jti",
            "iss",
            "aud",
            "token_version",
            "token_type",
        ]
    }
    # Verify signature, intended issuer/audience, lifetime, and required claims.
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        issuer=issuer,
        audience=audience,
        options=options,
    )
    if payload.get("token_type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload
