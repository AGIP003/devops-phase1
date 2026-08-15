import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.auth_identity import AuthIdentity


def test_provider_subject_can_belong_to_only_one_user(
    app,
    register_user,
    internal_user_id,
):
    owner = register_user("owner", "owner@example.com")
    intruder = register_user("intruder", "intruder@example.com")

    with app.app_context():
        db.session.add(
            AuthIdentity(
                user_id=internal_user_id(owner),
                provider="google",
                provider_subject="google-subject-123",
            )
        )
        db.session.commit()

        db.session.add(
            AuthIdentity(
                user_id=internal_user_id(intruder),
                provider="google",
                provider_subject="google-subject-123",
            )
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_user_can_have_only_one_identity_per_provider(
    app,
    register_user,
    internal_user_id,
):
    owner = register_user("owner", "owner@example.com")

    with app.app_context():
        user_id = internal_user_id(owner)
        db.session.add(
            AuthIdentity(
                user_id=user_id,
                provider="google",
                provider_subject="first-google-subject",
            )
        )
        db.session.commit()

        db.session.add(
            AuthIdentity(
                user_id=user_id,
                provider="google",
                provider_subject="second-google-subject",
            )
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
