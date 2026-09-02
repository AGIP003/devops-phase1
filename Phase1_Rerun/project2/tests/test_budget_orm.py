import pytest


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.critical
def test_user_cannot_access_another_users_budget(client, register_user):
    #Arrange
    owner = register_user("owner", "owner@example.com")
    intruder = register_user("intruder", "intruder@example.com")

    owner_headers = authorization(owner["token"])
    intruder_headers = authorization(intruder["token"])

    #Act
    create_response = client.post(
        "api/budgets",
        headers=owner_headers,
        json={
            "name": "Private budget",
            "category": "Learning",
            "targetAmount": "1200.00",
            "items": [
                {
                    "name": "SQLAlchemy book",
                    "estimatedAmount": "700.00",
                }
            ],
        },
    )

    assert create_response.status_code == 201, create_response.get_json()

    budget = create_response.get_json()["data"]
    budget_id = budget["id"]
    item_id = budget["items"][0]["id"]

    intruder_list = client.get(
        "api/budgets",
        headers=intruder_headers,
    )
    assert intruder_list.status_code == 200
    assert intruder_list.get_json() == []

    intruder_item_update = client.patch(
        f"/api/budget-items/{item_id}",
        headers=intruder_headers,
        json={"checked": True},
    )
    assert intruder_item_update.status_code == 404

    intruder_delete = client.delete(
        f"/api/budgets/{budget_id}",
        headers=intruder_headers,
    )
    assert intruder_delete.status_code == 404

    owner_list = client.get(
        "/api/budgets",
        headers=owner_headers,
    )
    assert owner_list.status_code == 200
    assert owner_list.get_json()[0]["id"] == budget_id
    assert owner_list.get_json()[0]["items"][0]["checked"] is False
