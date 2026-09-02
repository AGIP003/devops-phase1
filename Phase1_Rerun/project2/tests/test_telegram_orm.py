from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from app.extensions import db
from app.models.telegram_link import TelegramLink

def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_telegram_link_token_is_single_use(client, register_user):
    owner = register_user("owner", "owner@example.com")
    headers = authorization(owner["token"])

    token_response = client.post(
        "/api/telegram/link-token",
        headers=headers,
    )
    assert token_response.status_code == 201, token_response.get_json()

    link_token = token_response.get_json()["token"]

    verify_response = client.post(
        "/api/telegram/verify",
        json={
            "token": link_token,
            "telegram_id": 123456789,
        },
    )
    assert verify_response.status_code == 200, verify_response.get_json()
    assert verify_response.get_json()["user"]["telegram_id"] == 123456789
    telegram_access_token = verify_response.get_json()["token"]

    reused_response = client.post(
        "/api/telegram/verify",
        json={
            "token": link_token,
            "telegram_id": 123456789,
        },
    )
    assert reused_response.status_code == 400

    status_response = client.get(
        "/api/telegram/status",
        headers=authorization(telegram_access_token),
    )
    assert status_response.status_code == 200
    assert status_response.get_json() == {
        "linked": True,
        "telegram_id": 123456789,
    }


@pytest.mark.critical
def test_telegram_session_issues_a_token_accepted_by_middleware(
    client,
    register_user,
    monkeypatch,
):
    owner = register_user("owner", "owner@example.com")
    link_response = client.post(
        "/api/telegram/link-token",
        headers=authorization(owner["token"]),
    )
    link_token = link_response.get_json()["token"]
    telegram_id = 24681012
    verify_response = client.post(
        "/api/telegram/verify",
        json={"token": link_token, "telegram_id": telegram_id},
    )
    assert verify_response.status_code == 200

    bot_token = "test-telegram-bot-token"
    monkeypatch.setattr(
        "app.telegram_routes.TELEGRAM_BOT_TOKEN",
        bot_token,
    )
    session_response = client.post(
        "/api/telegram/session",
        json={"telegram_id": telegram_id},
        headers={
            "X-Telegram-Bot-Auth": sha256(
                bot_token.encode("utf-8")
            ).hexdigest()
        },
    )

    assert session_response.status_code == 200
    session_token = session_response.get_json()["token"]
    status_response = client.get(
        "/api/telegram/status",
        headers=authorization(session_token),
    )
    assert status_response.status_code == 200

def test_expired_telegram_link_token_is_rejected(
    app,
    client,
    register_user,
    internal_user_id,
):
    owner = register_user("owner", "owner@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        expired_link = TelegramLink(
            user_id=user_id,
            token="expired-test-token",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            used=False,
        )

        db.session.add(expired_link)
        db.session.commit()

    response = client.post(
        "/api/telegram/verify",
        json={
            "token": "expired-test-token",
            "telegram_id": 987654321,
        },
    )

    assert response.status_code == 400
    assert "expired" in response.get_json()["message"].lower()

def test_telegram_preferences_round_trip(client, register_user):
    owner = register_user("owner", "owner@example.com")
    headers = authorization(owner["token"])

    update_response = client.put(
        "/api/telegram/preferences",
        headers=headers,
        json={
            "default_payment_method": "m-pesa",
            "category_aliases": {
                "mat": "transport",
            },
        },
    )

    assert update_response.status_code == 200, update_response.get_json()

    get_response = client.get(
        "/api/telegram/preferences",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.get_json() == {
        "default_payment_method": "m-pesa",
        "category_aliases": {
            "mat": "transport",
        },
    }
