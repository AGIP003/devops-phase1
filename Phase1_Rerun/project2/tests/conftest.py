import pytest
from sqlalchemy import select, text

from app import create_app
from app.extensions import db
from app.models.user import User

DATABASE_TABLES = (
    "forex_rates",
    "budget_items",
    "budgets",
    "transactions",
    "categories",
    "telegram_user_preferences",
    "telegram_link_tokens",
    "payment_methods",
    "payment_method_groups",
    "auth_identities",
    "users",
)


def assert_safe_test_database():
    database_name = db.session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if not database_name.endswith("_test"):
        raise RuntimeError(
            "Refusing destructive test cleanup: "
            "connected database does not end with '_test'."
        )


@pytest.fixture(scope="session")
def app():
    test_app = create_app("testing")

    if not test_app.config["TESTING"]:
        raise RuntimeError("Testing mode is not enabled.")

    return test_app


@pytest.fixture(autouse=True)
def clean_database(app):
    with app.app_context():
        assert_safe_test_database()
        table_names = ", ".join(DATABASE_TABLES)

        db.session.execute(
            text(
                f"TRUNCATE TABLE {table_names} "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.session.commit()

        yield

        db.session.rollback()
        assert_safe_test_database()

        db.session.execute(
            text(
                f"TRUNCATE TABLE {table_names} "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def register_user(client):
    def register(
        username: str,
        email: str,
        password: str = "StrongPass123!",
    ):
        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )

        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return register


@pytest.fixture()
def internal_user_id(app):
    """Resolve the private database ID from the public API user ID."""
    def resolve(authentication_response: dict) -> int:
        public_id = authentication_response["user"]["id"]

        with app.app_context():
            user = db.session.scalar(
                select(User).where(User.public_id == public_id)
            )

            assert user is not None
            return user.id

    return resolve


@pytest.fixture()
def payment_method(app):
    from app.models.payment_method import PaymentMethod

    with app.app_context():
        method = PaymentMethod(name="m-pesa")

        db.session.add(method)
        db.session.commit()

        return method.id
