from datetime import UTC, datetime

from sqlalchemy import inspect, select, update
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.telegram_link import TelegramLink
from app.models.telegram_preferences import TelegramUserPreferences
from app.models.user import User


def telegram_linking_schema_ready() -> bool:
    inspector = inspect(db.engine)
    if not inspector.has_table("telegram_link_tokens"):
        return False
    if not inspector.has_table("users"):
        return False

    user_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }
    return "telegram_id" in user_columns


def create_telegram_link_token(
    user_id: int,
    token: str,
    expires_at: datetime,
) -> TelegramLink:
    try:
        db.session.execute(
            update(TelegramLink)
            .where(
                TelegramLink.user_id == user_id,
                TelegramLink.used.is_(False),
            )
            .values(used=True)
        )
        link = TelegramLink(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False,
        )
        db.session.add(link)
        db.session.commit()
        return link
    except Exception:
        db.session.rollback()
        raise


def get_telegram_link_status(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def unlink_telegram_account(user_id: int) -> User | None:
    try:
        user = db.session.get(User, user_id)
        if user is None:
            return None

        user.telegram_id = None
        db.session.execute(
            update(TelegramLink)
            .where(
                TelegramLink.user_id == user_id,
                TelegramLink.used.is_(False),
            )
            .values(used=True)
        )
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise


def get_user_by_telegram_id(telegram_id: int) -> User | None:
    statement = select(User).where(User.telegram_id == telegram_id)
    return db.session.scalar(statement)


def _get_or_create_preferences(
    user_id: int,
) -> TelegramUserPreferences:
    preferences = db.session.get(TelegramUserPreferences, user_id)
    if preferences is not None:
        return preferences

    preferences = TelegramUserPreferences(user_id=user_id)
    db.session.add(preferences)
    db.session.flush()
    return preferences


def get_telegram_preferences(
    user_id: int,
) -> TelegramUserPreferences:
    try:
        preferences = _get_or_create_preferences(user_id)
        db.session.commit()
        return preferences
    except Exception:
        db.session.rollback()
        raise


def update_telegram_preferences(
    user_id: int,
    default_payment_method: str | None = None,
    category_aliases: dict[str, str] | None = None,
) -> TelegramUserPreferences:
    try:
        preferences = _get_or_create_preferences(user_id)

        if default_payment_method is not None:
            preferences.default_payment_method = default_payment_method
        if category_aliases is not None:
            preferences.category_aliases = category_aliases

        db.session.commit()
        return preferences
    except Exception:
        db.session.rollback()
        raise


def consume_telegram_link_token(
    token: str,
    telegram_id: int,
) -> tuple[User | None, str | None]:
    """Atomically consume a valid link token and bind its user."""
    try:
        statement = (
            select(TelegramLink)
            .where(TelegramLink.token == token)
            .with_for_update()
        )
        link = db.session.scalar(statement)

        if link is None:
            db.session.rollback()
            return None, "invalid"
        if link.used:
            db.session.rollback()
            return None, "used"
        if link.expires_at <= datetime.now(UTC):
            link.used = True
            db.session.commit()
            return None, "expired"

        user = db.session.get(User, link.user_id)
        if user is None:
            db.session.rollback()
            return None, "invalid"

        telegram_owner = db.session.scalar(
            select(User).where(
                User.telegram_id == telegram_id,
                User.id != user.id,
            )
        )
        if telegram_owner is not None:
            db.session.rollback()
            return None, "telegram_in_use"

        user.telegram_id = telegram_id
        link.used = True
        db.session.commit()
        return user, None
    except IntegrityError:
        db.session.rollback()
        return None, "telegram_in_use"
    except Exception:
        db.session.rollback()
        raise
