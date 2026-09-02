import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.user import User

pytestmark = pytest.mark.integration

def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.critical
def test_authenticated_user_can_persist_display_name(
    app,
    client,
    register_user,
):
    owner = register_user("owner", "owner@example.com")

    response = client.patch(
        "/api/auth/profile",
        headers=authorization(owner["token"]),
        json={"display_name": "  Owner Name  "},
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["user"]["display_name"] == "Owner Name"

    with app.app_context():
        stored_user = db.session.scalar(
            select(User).where(User.email == "owner@example.com")
        )
        assert stored_user is not None
        assert stored_user.display_name == "Owner Name"

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "owner@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200

    login_payload = login_response.get_json()
    assert login_payload["user"]["display_name"] == "Owner Name"
    assert login_payload.get("token") or login_payload.get("access_token")


def test_profile_update_uses_authenticated_user_not_client_user_id(
    app,
    client,
    register_user,
    internal_user_id,
):
    owner = register_user("owner", "owner@example.com")
    other_user = register_user("other", "other@example.com")

    response = client.patch(
        "/api/auth/profile",
        headers=authorization(owner["token"]),
        json={
            "display_name": "Owner Updated",
            "user_id": internal_user_id(other_user),
        },
    )

    assert response.status_code == 200

    with app.app_context():
        stored_owner = db.session.get(User, internal_user_id(owner))
        stored_other_user = db.session.get(User, internal_user_id(other_user))

        assert stored_owner.display_name == "Owner Updated"
        assert stored_other_user.display_name == "other"


@pytest.mark.parametrize(
    "display_name",
    [None, 42, "", "   ", "x" * 101],
)
def test_profile_update_rejects_invalid_display_name(
    client,
    register_user,
    display_name,
):
    owner = register_user("owner", "owner@example.com")

    response = client.patch(
        "/api/auth/profile",
        headers=authorization(owner["token"]),
        json={"display_name": display_name},
    )

    assert response.status_code == 400


def test_profile_update_requires_authentication(client):
    response = client.patch(
        "/api/auth/profile",
        json={"display_name": "Anonymous Update"},
    )

    assert response.status_code == 401
