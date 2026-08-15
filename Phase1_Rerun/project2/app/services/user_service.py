from sqlalchemy import select
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User



class DuplicateUserError(ValueError):
    """Raised when a username or email is already registered."""


def get_user_by_email(email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.session.scalar(statement)


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)

def get_user_by_public_id(public_id: UUID) -> User  | None:
    statement = select(User).where(User.public_id == public_id)
    return db.session.scalar(statement)

def create_user(
    email: str,
    username: str,
    password_hash: str,
) -> User:
    try:
        user = User(
            email=email,
            username=username,
            display_name=username,
            password_hash=password_hash,
            role="user",
        )
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateUserError(
            "The email or username is already in use."
        ) from error
    except Exception:
        db.session.rollback()
        raise


def update_user_password(user: User, password_hash: str) -> None:
    try:
        user.password_hash = password_hash
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def update_user_display_name(user: User, display_name: str) -> User:
    """Persist the authenticated user's chosen display name."""
    try:
        user.display_name = display_name
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise


def delete_user(user: User) -> None:
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
