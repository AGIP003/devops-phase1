import time
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select

from app.auth import verify_password
from app.auth_routes import get_serializer
from app.extensions import db
from app.models.user import User
from app.services.user_service import update_user_password


OLD_PASSWORD = "StrongPass123!"
NEW_PASSWORD = "NewStrongPass456!"


def _capture_reset_email(monkeypatch):
    sent_messages = []
    monkeypatch.setattr(
        "app.auth_routes.mail.send",
        sent_messages.append,
    )
    return sent_messages


def _reset_token_from(message) -> str:
    reset_url = next(
        line.strip()
        for line in message.body.splitlines()
        if "/reset-password?token=" in line
    )
    return parse_qs(urlparse(reset_url).query)["token"][0]


def _signed_reset_token(app, email: str) -> str:
    with app.app_context():
        return get_serializer().dumps(
            email,
            salt="password-reset-salt",
        )


def test_disabled_password_reset_returns_before_email_or_database_lookup(
    app,
    client,
    monkeypatch,
):
    email_calls = []
    database_calls = []
    monkeypatch.setattr(
        "app.auth_routes.mail.send",
        email_calls.append,
    )
    monkeypatch.setattr(
        "app.auth_routes.get_user_by_email",
        lambda email: database_calls.append(email),
    )

    app.config["PASSWORD_RESET_ENABLED"] = False
    try:
        response = client.post(
            "/api/auth/password_reset_request",
            json={"email": "person@example.com"},
        )
    finally:
        app.config["PASSWORD_RESET_ENABLED"] = True

    assert response.status_code == 503
    assert response.get_json()["message"] == (
        "Password reset is temporarily unavailable"
    )
    assert database_calls == []
    assert email_calls == []


@pytest.mark.external
def test_reset_request_does_not_reveal_whether_email_exists(
    client,
    register_user,
    monkeypatch,
):
    register_user("reset-owner", "reset-owner@example.com")
    sent_messages = _capture_reset_email(monkeypatch)

    existing_response = client.post(
        "/api/auth/password_reset_request",
        json={"email": "reset-owner@example.com"},
    )
    unknown_response = client.post(
        "/api/auth/password_reset_request",
        json={"email": "unknown@example.com"},
    )

    assert existing_response.status_code == 200
    assert unknown_response.status_code == 200
    assert existing_response.get_json() == unknown_response.get_json()
    assert existing_response.get_json() == {
        "message": "A reset link has been sent"
    }

    assert len(sent_messages) == 1
    assert sent_messages[0].recipients == ["reset-owner@example.com"]
    assert "/reset-password?token=" in sent_messages[0].body


@pytest.mark.critical
@pytest.mark.external
def test_valid_reset_token_changes_password(
    client,
    register_user,
    monkeypatch,
):
    registration = register_user(
        "password-owner",
        "password-owner@example.com",
        OLD_PASSWORD,
    )
    original_access_token = registration["token"]
    sent_messages = _capture_reset_email(monkeypatch)

    request_response = client.post(
        "/api/auth/password_reset_request",
        json={"email": "password-owner@example.com"},
    )
    assert request_response.status_code == 200
    assert len(sent_messages) == 1
    reset_token = _reset_token_from(sent_messages[0])

    reset_response = client.post(
        "/api/auth/password-reset-verify",
        json={
            "token": reset_token,
            "new_password": NEW_PASSWORD,
        },
    )
    assert reset_response.status_code == 200, reset_response.get_json()
    assert reset_response.get_json() == {
        "message": "Password reset succesfully"
    }

    old_login = client.post(
        "/api/auth/login",
        json={
            "email": "password-owner@example.com",
            "password": OLD_PASSWORD,
        },
    )
    new_login = client.post(
        "/api/auth/login",
        json={
            "email": "password-owner@example.com",
            "password": NEW_PASSWORD,
        },
    )

    assert old_login.status_code == 401
    assert new_login.status_code == 200, new_login.get_json()
    assert new_login.get_json()["token"] != original_access_token


def test_invalid_reset_token_is_rejected(client):
    response = client.post(
        "/api/auth/password-reset-verify",
        json={
            "token": "not-a-valid-reset-token",
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "invalid"


def test_expired_reset_token_is_rejected(
    app,
    client,
    monkeypatch,
):
    current_time = time.time()

    with monkeypatch.context() as token_clock:
        token_clock.setattr(
            "itsdangerous.timed.time.time",
            lambda: current_time - 3601,
        )
        token = _signed_reset_token(
            app,
            "expired-reset@example.com",
        )

    response = client.post(
        "/api/auth/password-reset-verify",
        json={
            "token": token,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "expired"


def test_password_update_rolls_back_when_commit_fails(
    app,
    register_user,
    monkeypatch,
):
    register_user("rollback-owner", "rollback-owner@example.com")

    with app.app_context():
        user = db.session.scalar(
            select(User).where(
                User.email == "rollback-owner@example.com"
            )
        )
        assert user is not None
        original_hash = user.password_hash
        rollback_calls = []
        real_rollback = db.session.rollback

        def fail_commit():
            raise RuntimeError("simulated database failure")

        def record_rollback():
            rollback_calls.append(True)
            real_rollback()

        with monkeypatch.context() as database_failure:
            database_failure.setattr(db.session, "commit", fail_commit)
            database_failure.setattr(
                db.session,
                "rollback",
                record_rollback,
            )

            with pytest.raises(
                RuntimeError,
                match="simulated database failure",
            ):
                update_user_password(user, "replacement-hash")

        db.session.expire_all()
        stored_user = db.session.scalar(
            select(User).where(
                User.email == "rollback-owner@example.com"
            )
        )

        assert rollback_calls == [True]
        assert stored_user is not None
        assert stored_user.password_hash == original_hash
        assert verify_password(OLD_PASSWORD, stored_user.password_hash)
