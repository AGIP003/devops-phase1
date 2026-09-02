import pytest
from google.auth import exceptions as google_exceptions

from app.services.google_identity_service import (
    GoogleIdentityProviderUnavailableError,
    InvalidGoogleCredentialError,
    verify_google_credential,
)


pytestmark = [pytest.mark.no_database, pytest.mark.external]


def test_google_verifier_builds_identity_from_verified_claims(app, monkeypatch):
    captured = {}

    def verify(credential, request_adapter, audience):
        captured["credential"] = credential
        captured["audience"] = audience
        return {
            "sub": "google-subject-123",
            "email": "Person@Example.com",
            "email_verified": True,
            "name": "  Person Name  ",
        }

    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        verify,
    )

    with app.app_context():
        identity = verify_google_credential(" signed-google-token ")

    assert captured == {
        "credential": "signed-google-token",
        "audience": "test-client.apps.googleusercontent.com",
    }
    assert identity.provider == "google"
    assert identity.subject == "google-subject-123"
    assert identity.email == "person@example.com"
    assert identity.display_name == "Person Name"


def test_google_verifier_rejects_unverified_email(app, monkeypatch):
    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        lambda credential, request_adapter, audience: {
            "sub": "google-subject-123",
            "email": "person@example.com",
            "email_verified": False,
        },
    )

    with app.app_context(), pytest.raises(InvalidGoogleCredentialError):
        verify_google_credential("signed-google-token")


def test_google_verifier_distinguishes_network_failure(app, monkeypatch):
    def fail_to_reach_google(credential, request_adapter, audience):
        raise google_exceptions.TransportError("network unavailable")

    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        fail_to_reach_google,
    )

    with app.app_context(), pytest.raises(
        GoogleIdentityProviderUnavailableError
    ):
        verify_google_credential("signed-google-token")
