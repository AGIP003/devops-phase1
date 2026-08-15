from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.extensions import db
from app.models.auth_identity import AuthIdentity
from app.models.user import User
from app.services.external_identity_service import (
    VerifiedExternalIdentity,
    authenticate_external_identity,
)
from app.services.google_identity_service import (
    GoogleIdentityProviderUnavailableError,
    InvalidGoogleCredentialError,
)
from app.services.token_service import issue_access_token


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def google_identity(
    *,
    subject: str = "google-subject-123",
    email: str = "new.user@example.com",
    display_name: str = "New User",
) -> VerifiedExternalIdentity:
    return VerifiedExternalIdentity(
        provider="google",
        subject=subject,
        email=email,
        display_name=display_name,
    )


def test_google_login_creates_one_oauth_user_and_is_idempotent(
    app,
    client,
    monkeypatch,
):
    identity = google_identity()
    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        lambda credential: identity,
    )

    first_response = client.post(
        "/api/auth/google",
        json={"credential": "first-google-credential"},
    )
    second_response = client.post(
        "/api/auth/google",
        json={"credential": "second-google-credential"},
    )

    assert first_response.status_code == 200, first_response.get_json()
    assert second_response.status_code == 200, second_response.get_json()
    assert first_response.get_json()["user"] == second_response.get_json()["user"]
    assert first_response.get_json()["token"]

    with app.app_context():
        assert db.session.scalar(select(func.count(User.id))) == 1
        assert db.session.scalar(select(func.count(AuthIdentity.id))) == 1

        user = db.session.scalar(select(User))
        assert user is not None
        assert user.password_hash is None
        assert user.display_name == "New User"
        assert str(user.public_id) == first_response.get_json()["user"]["id"]


def test_google_login_does_not_auto_link_an_existing_email(
    client,
    register_user,
    monkeypatch,
):
    register_user("existing", "existing@example.com")
    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        lambda credential: google_identity(email="existing@example.com"),
    )

    response = client.post(
        "/api/auth/google",
        json={"credential": "valid-google-credential"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "account_link_required"


def test_google_login_maps_invalid_and_unavailable_provider_errors(
    client,
    monkeypatch,
):
    def reject_credential(credential):
        raise InvalidGoogleCredentialError

    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        reject_credential,
    )
    invalid_response = client.post(
        "/api/auth/google",
        json={"credential": "invalid"},
    )

    def provider_unavailable(credential):
        raise GoogleIdentityProviderUnavailableError

    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        provider_unavailable,
    )
    unavailable_response = client.post(
        "/api/auth/google",
        json={"credential": "temporarily-unverifiable"},
    )

    assert invalid_response.status_code == 401
    assert unavailable_response.status_code == 503


def test_authenticated_user_can_link_google_identity(
    app,
    client,
    register_user,
    internal_user_id,
    monkeypatch,
):
    owner = register_user("owner", "owner@example.com")
    identity = google_identity(
        email="owner@example.com",
        display_name="Owner Name",
    )
    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        lambda credential: identity,
    )

    response = client.post(
        "/api/auth/google/link",
        headers=authorization(owner["token"]),
        json={"credential": "valid-google-credential"},
    )

    assert response.status_code == 200, response.get_json()

    with app.app_context():
        stored_identity = db.session.scalar(
            select(AuthIdentity).where(
                AuthIdentity.user_id == internal_user_id(owner),
                AuthIdentity.provider == "google",
            )
        )
        assert stored_identity is not None
        assert stored_identity.provider_subject == identity.subject


def test_google_link_requires_recent_authentication(
    app,
    client,
    register_user,
    internal_user_id,
    monkeypatch,
):
    owner = register_user("owner", "owner@example.com")
    monkeypatch.setattr(
        "app.auth_routes.verify_google_credential",
        lambda credential: google_identity(email="owner@example.com"),
    )

    with app.app_context():
        user = db.session.get(User, internal_user_id(owner))
        old_token = issue_access_token(
            user,
            authenticated_at=datetime.now(UTC) - timedelta(hours=1),
        )

    response = client.post(
        "/api/auth/google/link",
        headers=authorization(old_token),
        json={"credential": "valid-google-credential"},
    )

    assert response.status_code == 401


def test_failed_oauth_user_creation_rolls_back_and_session_recovers(app):
    invalid_identity = google_identity(
        subject="x" * 256,
        email="rollback@example.com",
    )

    with app.app_context():
        try:
            authenticate_external_identity(invalid_identity)
        except Exception:
            pass
        else:
            raise AssertionError("The oversized provider subject should fail")

        assert db.session.scalar(
            select(User).where(User.email == "rollback@example.com")
        ) is None

        recovered_user = authenticate_external_identity(
            google_identity(
                subject="valid-subject-after-rollback",
                email="recovered@example.com",
            )
        )
        assert recovered_user.id is not None
