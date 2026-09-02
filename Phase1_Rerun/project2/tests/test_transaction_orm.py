from datetime import date
from app.extensions import db
from app.models.transaction import Transaction
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.services.transaction_service import create_transaction_for_user

pytestmark = pytest.mark.integration

def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def transaction_payload(description: str) -> dict[str, str]:
    return {
        "amount": "300.00",
        "category": "food",
        "type": "expense",
        "date": date.today().isoformat(),
        "description": description,
        "payment_method": "m-pesa",
    }


@pytest.mark.critical
def test_authenticated_user_can_create_transaction(
    client,
    register_user,
    payment_method,
):
    owner = register_user("creator", "creator@example.com")

    response = client.post(
        "/api/transactions",
        headers=authorization(owner["token"]),
        json=transaction_payload("created through the API"),
    )

    assert response.status_code == 201, response.get_json()
    payload = response.get_json()
    transaction = payload["data"]
    assert payload["status"] == "success"
    assert isinstance(transaction["id"], int)
    assert isinstance(transaction["user_id"], int)
    assert transaction["date"] == date.today().isoformat()
    assert transaction["description"] == "created through the api"
    assert transaction["type"] == "expense"
    assert transaction["category"] == "Food"
    assert transaction["amount"] == "300.00"
    assert transaction["payment_method"] == "m-pesa"


@pytest.mark.critical
def test_transaction_list_contains_only_authenticated_users_transactions(
    client,
    register_user,
    payment_method,
):
    owner = register_user("list-owner", "list-owner@example.com")
    intruder = register_user("list-intruder", "list-intruder@example.com")

    owner_create = client.post(
        "/api/transactions",
        headers=authorization(owner["token"]),
        json=transaction_payload("owner-only transaction"),
    )
    intruder_create = client.post(
        "/api/transactions",
        headers=authorization(intruder["token"]),
        json=transaction_payload("intruder-only transaction"),
    )
    assert owner_create.status_code == 201, owner_create.get_json()
    assert intruder_create.status_code == 201, intruder_create.get_json()

    response = client.get(
        "/api/transactions",
        headers=authorization(owner["token"]),
    )

    assert response.status_code == 200
    listed_ids = {transaction["id"] for transaction in response.get_json()}
    assert listed_ids == {owner_create.get_json()["data"]["id"]}
    assert intruder_create.get_json()["data"]["id"] not in listed_ids


@pytest.mark.critical
def test_user_cannot_read_another_users_transaction(client, register_user, payment_method):
    # Arrange
    owner = register_user("owner", "owner@example.com")
    intruder = register_user("intruder", "intruder@example.com")

    transaction_data = {
        "amount": "300.00",
        "category": "food",
        "type": "expense",
        "date": date.today().isoformat(),
        "description": "private lunch",
        "payment_method": "m-pesa",
    }

    # Act: owner creates the transaction
    create_response = client.post(
        "/api/transactions",
        json=transaction_data,
        headers=authorization(owner["token"]),
    )

    # Assert creation before using its response
    assert create_response.status_code == 201, create_response.get_json()
    transaction_id = create_response.get_json()["data"]["id"]

    # Act: another authenticated user guesses its ID
    intruder_response = client.get(
        f"/api/transactions/{transaction_id}",
        headers=authorization(intruder["token"]),
    )

    # The intruder cannot read it.
    assert intruder_response.status_code == 404

    # The intruder cannot modify it.
    intruder_update = client.put(
        f"/api/transactions/{transaction_id}",
        headers=authorization(intruder["token"]),
        json={"amount": "900.00"},
    )
    assert intruder_update.status_code == 404

    # The intruder cannot delete it.
    intruder_delete = client.delete(
        f"/api/transactions/{transaction_id}",
        headers=authorization(intruder["token"]),
    )
    assert intruder_delete.status_code == 404

    # Make a fresh request after both attacks.
    owner_response = client.get(
        f"/api/transactions/{transaction_id}",
        headers=authorization(owner["token"]),
    )

    assert owner_response.status_code == 200
    assert owner_response.get_json()["amount"] == "300.00"

def test_soft_delete_hides_but_preserves_transaction(app, client, register_user, payment_method):
    owner = register_user("owner", "owner@example.com")
    headers = authorization(owner["token"])

    create_response = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "amount": "300.00",
            "category": "food",
            "type": "expense",
            "date": date.today().isoformat(),
            "description": "soft delete test",
            "payment_method": "m-pesa",
        },
    )
    assert create_response.status_code == 201, create_response.get_json()
    transaction_id = create_response.get_json()["data"]["id"]

    delete_response = client.delete(
        f"/api/transactions/{transaction_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    hidden_response = client.get(
        f"/api/transactions/{transaction_id}",
        headers=headers,
    )
    assert hidden_response.status_code == 404

    with app.app_context():
        stored_transaction = db.session.get(Transaction, transaction_id)

        assert stored_transaction is not None
        assert stored_transaction.deleted_at is not None

def test_failed_transaction_rolls_back_and_session_recovers(
    app,
    register_user,
    internal_user_id,
    payment_method,
):
    owner = register_user("owner", "owner@example.com")
    user_id = internal_user_id(owner)

    with app.app_context():
        with pytest.raises(IntegrityError):
            create_transaction_for_user(
                user_id=user_id,
                category_name="food",
                transaction_type="expense",
                payment_method_name="m-pesa",
                amount=None,
                transaction_date=date.today(),
                description="must fail",
            )

        rolled_back_category = db.session.scalar(
            select(Category).where(
                Category.user_id == user_id,
                Category.name == "food",
            )
        )
        assert rolled_back_category is None
        saved_transaction = create_transaction_for_user(
            user_id=user_id,
            category_name="food",
            transaction_type="expense",
            payment_method_name="m-pesa",
            amount=Decimal("300.00"),
            transaction_date=date.today(),
            description="session recovered",
        )
        assert saved_transaction.id is not None
