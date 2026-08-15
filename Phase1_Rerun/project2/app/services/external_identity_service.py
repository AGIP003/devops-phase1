from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.auth_identity import AuthIdentity
from app.models.user import User

@dataclass(frozen=True, slots=True)
class VerifiedExternalIdentity:
    provider: str
    subject: str
    email: str
    display_name: str | None = None

class ExternalAccountLinkRequiredError(ValueError):
    """Raised when an email exists but the provider is not safely linked."""

class ExternalIdentityConflictError(ValueError):
    """Raised when an external identity cannot be linked safely."""

def _get_auth_identity(
    provider: str,
    subject: str,
) -> AuthIdentity | None:
    statement = (
        select(AuthIdentity)
        .options(joinedload(AuthIdentity.user))
        .where(
            AuthIdentity.provider == provider,
            AuthIdentity.provider_subject == subject,
        )
    )

    return db.session.scalar(statement)

def authenticate_external_identity(verified_identity: VerifiedExternalIdentity) -> User:
    now = datetime.now(UTC)

    try:
        stored_identity = _get_auth_identity(
            verified_identity.provider,
            verified_identity.subject,
        )

        #Existing provider identity - normal login
        if stored_identity is not None:
            user = stored_identity.user

            stored_identity.last_authenticated_at = now
            user.last_login=now

            db.session.commit()
            return user

        # No provider identity: prevent unsafe email auto-linking.
        existing_user = db.session.scalar(
            select(User).where(
                User.email == verified_identity.email
            )
        )

        if existing_user is not None:
            raise ExternalAccountLinkRequiredError(
                "Sign in to the existing account before linking Google."
            )

        # Completely new user: create both rows atomically.
        user = User(
            username=f"user_{uuid4().hex}",
            display_name=verified_identity.display_name,
            email=verified_identity.email,
            password_hash=None,
            role="user",
            last_login=now,
        )

        provider_identity = AuthIdentity(
            provider=verified_identity.provider,
            provider_subject=verified_identity.subject,
            last_authenticated_at=now,
            user=user,
        )

        db.session.add_all([user, provider_identity])
        db.session.commit()

        return user

    except ExternalAccountLinkRequiredError:
        db.session.rollback()
        raise

    except IntegrityError as error:
        db.session.rollback()

        # Another simultaneous request may have created it first.
        stored_identity = _get_auth_identity(
            verified_identity.provider,
            verified_identity.subject,
        )

        if stored_identity is not None:
            return stored_identity.user

        # The collision may instead be an existing local email.
        existing_user = db.session.scalar(
            select(User).where(
                User.email == verified_identity.email
            )
        )

        if existing_user is not None:
            raise ExternalAccountLinkRequiredError(
                "Sign in to the existing account before linking Google."
            ) from error

        raise

    except Exception:
        db.session.rollback()
        raise

def _get_user_provider_identity(user_id: int, provider: str) -> AuthIdentity | None:
    statement = select(AuthIdentity).where(
        AuthIdentity.user_id == user_id,
        AuthIdentity.provider == provider,
    )

    return db.session.scalar(statement)

def link_external_identity(user: User, verified_identity: VerifiedExternalIdentity) -> AuthIdentity:
    now = datetime.now(UTC)

    try:
        stored_identity = _get_auth_identity(
            verified_identity.provider,
            verified_identity.subject,
        )

        # Repeating the same link request is safe and idempotent.
        if stored_identity is not None:
            if stored_identity.user_id != user.id:
                raise ExternalIdentityConflictError(
                    "This external identity belongs to another account."
                )

            stored_identity.last_authenticated_at = now

            if (
                user.display_name is None
                and verified_identity.display_name is not None
            ):
                user.display_name = verified_identity.display_name

            db.session.commit()
            return stored_identity

        user_provider_identity = _get_user_provider_identity(
            user.id,
            verified_identity.provider,
        )

        if user_provider_identity is not None:
            raise ExternalIdentityConflictError(
                "This account already has a different identity "
                "for this provider."
            )

        provider_identity = AuthIdentity(
            provider=verified_identity.provider,
            provider_subject=verified_identity.subject,
            last_authenticated_at=now,
            user=user,
        )

        if (
            user.display_name is None
            and verified_identity.display_name is not None
        ):
            user.display_name = verified_identity.display_name

        db.session.add(provider_identity)
        db.session.commit()

        return provider_identity

    except ExternalIdentityConflictError:
        db.session.rollback()
        raise

    except IntegrityError as error:
        db.session.rollback()

        # Re-check after a possible concurrent linking request.
        stored_identity = _get_auth_identity(
            verified_identity.provider,
            verified_identity.subject,
        )

        if (
            stored_identity is not None
            and stored_identity.user_id == user.id
        ):
            return stored_identity

        raise ExternalIdentityConflictError(
            "This external identity cannot be linked."
        ) from error

    except Exception:
        db.session.rollback()
        raise
