from flask import current_app
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.services.external_identity_service import (
    VerifiedExternalIdentity,
)


class InvalidGoogleCredentialError(ValueError):
    """Raised when Google rejects the supplied identity token."""


class GoogleIdentityProviderUnavailableError(RuntimeError):
    """Raised when Google token verification cannot reach Google."""


def verify_google_credential(credential: str) -> VerifiedExternalIdentity:
    if not isinstance(credential, str) or not credential.strip():
        raise InvalidGoogleCredentialError(
            "A Google credential is required."
        )

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID is not configured.")

    try:
        claims = google_id_token.verify_oauth2_token(
            credential.strip(),
            google_requests.Request(),
            client_id,
        )
    except google_exceptions.TransportError as error:
        raise GoogleIdentityProviderUnavailableError(
            "Google authentication is temporarily unavailable."
        ) from error
    except (ValueError, google_exceptions.GoogleAuthError) as error:
        raise InvalidGoogleCredentialError(
            "The Google credential is invalid."
        ) from error

    subject = claims.get("sub")
    email = claims.get("email")
    email_verified = claims.get("email_verified")
    display_name = claims.get("name")

    if not isinstance(subject, str) or not subject.strip():
        raise InvalidGoogleCredentialError(
            "Google did not provide a valid subject."
        )

    if not isinstance(email, str) or not email.strip():
        raise InvalidGoogleCredentialError(
            "Google did not provide an email address."
        )

    if email_verified is not True:
        raise InvalidGoogleCredentialError(
            "Google has not verified this email address."
        )

    if isinstance(display_name, str):
        display_name = display_name.strip() or None
    else:
        display_name = None

    return VerifiedExternalIdentity(
        provider="google",
        subject=subject.strip(),
        email=email.strip().lower(),
        display_name=display_name,
    )
