from datetime import date, timedelta


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_transaction(client, headers, *, amount: str, category: str, kind: str):
    response = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "amount": amount,
            "category": category,
            "type": kind,
            "date": date.today().isoformat(),
            "description": f"Analytics {kind}",
            "payment_method": "m-pesa",
        },
    )
    assert response.status_code == 201, response.get_json()


def test_summary_aggregates_real_domains_and_enforces_ownership(
    client,
    register_user,
    payment_method,
):
    owner = register_user("analytics-owner", "analytics-owner@example.com")
    other = register_user("analytics-other", "analytics-other@example.com")
    owner_headers = authorization(owner["token"])
    other_headers = authorization(other["token"])

    create_transaction(
        client,
        owner_headers,
        amount="10000.00",
        category="Salary",
        kind="income",
    )
    create_transaction(
        client,
        owner_headers,
        amount="2500.00",
        category="Food",
        kind="expense",
    )
    create_transaction(
        client,
        other_headers,
        amount="900000.00",
        category="Food",
        kind="expense",
    )

    bill_response = client.post(
        "/api/commitments",
        headers=owner_headers,
        json={
            "kind": "bill",
            "name": "Electricity",
            "provider": "Kenya Power",
            "category": "Utilities",
            "amount": "1200.00",
            "amountKind": "estimated",
            "nextDueDate": (date.today() + timedelta(days=7)).isoformat(),
            "frequency": "monthly",
            "currencyCode": "KES",
        },
    )
    assert bill_response.status_code == 201, bill_response.get_json()

    goal_response = client.post(
        "/api/goals",
        headers=owner_headers,
        json={
            "name": "Emergency fund",
            "targetAmount": "6000.00",
            "currentSavings": "3000.00",
            "targetDate": (date.today() + timedelta(days=60)).isoformat(),
            "contributionFrequency": "monthly",
            "currencyCode": "KES",
        },
    )
    assert goal_response.status_code == 201, goal_response.get_json()

    response = client.get(
        "/api/analytics/summary?period=30-days",
        headers=owner_headers,
    )

    assert response.status_code == 200, response.get_json()
    summary = response.get_json()
    assert summary["cashFlow"] == {
        "income": "10000.00",
        "expenses": "2500.00",
        "transactionFees": None,
        "net": "7500.00",
        "savingsRate": "75.00",
    }
    assert summary["commitments"]["monthlyBills"] == "1200.00"
    assert summary["goals"]["saved"] == "3000.00"
    assert summary["expenseCategories"] == [
        {"amount": "2500.00", "category": "Food"}
    ]
    assert summary["dailyActivity"][0]["transactionCount"] == 2
    assert summary["coverage"]["transactionFees"] is False
    assert response.headers["Cache-Control"] == "private, no-store"

    other_response = client.get(
        "/api/analytics/summary?period=30-days",
        headers=other_headers,
    )
    assert other_response.status_code == 200
    other_summary = other_response.get_json()
    assert other_summary["cashFlow"]["income"] == "0.00"
    assert other_summary["cashFlow"]["expenses"] == "900000.00"
    assert other_summary["commitments"]["monthlyBills"] == "0.00"
    assert other_summary["goals"]["activeCount"] == 0


def test_summary_rejects_invalid_period_and_requires_authentication(
    client,
    register_user,
):
    owner = register_user("period-owner", "period-owner@example.com")

    invalid = client.get(
        "/api/analytics/summary?period=forever-ish",
        headers=authorization(owner["token"]),
    )
    assert invalid.status_code == 400
    assert "Unsupported period" in invalid.get_json()["message"]

    unauthenticated = client.get("/api/analytics/summary?period=12-months")
    assert unauthenticated.status_code == 401
