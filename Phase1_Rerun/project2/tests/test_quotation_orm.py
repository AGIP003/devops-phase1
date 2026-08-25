def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client, token, title="Office chairs"):
    response = client.post(
        "/api/quotation-projects",
        headers=authorization(token),
        json={
            "title": title,
            "category": "Equipment",
            "notes": "Compare delivered prices",
            "currencyCode": "KES",
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def add_item(client, token, project_id, name, quantity, unit="pcs"):
    response = client.post(
        f"/api/quotation-projects/{project_id}/items",
        headers=authorization(token),
        json={"name": name, "quantity": quantity, "unit": unit},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def add_quote(client, token, project, supplier, prices, **overrides):
    payload = {
        "supplier": supplier,
        "contact": "supplier@example.com",
        "validUntil": "2026-09-30",
        "deliveryCost": "100.00",
        "discount": "50.00",
        "taxMode": "excluded",
        "taxRate": "16.00",
        "deliveryDays": 3,
        "paymentTerms": "Payment on delivery",
        "prices": prices,
        **overrides,
    }
    response = client.post(
        f"/api/quotation-projects/{project['id']}/quotes",
        headers=authorization(token),
        json=payload,
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_quotation_comparison_calculates_landed_cost_and_flags_missing_prices(
    client,
    register_user,
):
    owner = register_user("quote-owner", "quote-owner@example.com")
    token = owner["token"]
    project = create_project(client, token)
    project = add_item(client, token, project["id"], "Chair", "2")
    project = add_item(client, token, project["id"], "Delivery setup", "1", "job")
    chair, setup = project["items"]

    project = add_quote(
        client,
        token,
        project,
        "Complete Supplier",
        [
            {"itemId": chair["id"], "unitPrice": "100.00"},
            {"itemId": setup["id"], "unitPrice": "1000.00"},
        ],
    )
    project = add_quote(
        client,
        token,
        project,
        "Incomplete Supplier",
        [{"itemId": chair["id"], "unitPrice": "1.00"}],
        deliveryCost="0",
        discount="0",
        taxMode="included",
    )

    complete, incomplete = project["quotations"]
    assert complete["breakdown"] == {
        "complete": True,
        "coverage": 100,
        "pricedItemCount": 2,
        "itemCount": 2,
        "subtotal": "1200.00",
        "deliveryCost": "100.00",
        "tax": "192.00",
        "discount": "50.00",
        "total": "1442.00",
    }
    assert incomplete["breakdown"]["complete"] is False
    assert incomplete["breakdown"]["coverage"] == 50
    assert incomplete["breakdown"]["total"] == "2.00"


def test_quotation_records_are_ownership_filtered(client, register_user):
    owner = register_user("quote-private", "quote-private@example.com")
    intruder = register_user("quote-intruder", "quote-intruder@example.com")
    project = create_project(client, owner["token"], "Private purchase")

    intruder_list = client.get(
        "/api/quotation-projects",
        headers=authorization(intruder["token"]),
    )
    intruder_get = client.get(
        f"/api/quotation-projects/{project['id']}",
        headers=authorization(intruder["token"]),
    )
    intruder_item = client.post(
        f"/api/quotation-projects/{project['id']}/items",
        headers=authorization(intruder["token"]),
        json={"name": "Injected item", "quantity": "1", "unit": "pcs"},
    )

    assert intruder_list.status_code == 200
    assert intruder_list.get_json() == []
    assert intruder_get.status_code == 404
    assert intruder_item.status_code == 404


def test_only_one_supplier_can_be_preferred(client, register_user):
    owner = register_user("quote-choice", "quote-choice@example.com")
    token = owner["token"]
    project = create_project(client, token, "Preferred supplier test")
    project = add_item(client, token, project["id"], "Desk", "1")
    item = project["items"][0]
    project = add_quote(
        client,
        token,
        project,
        "Supplier One",
        [{"itemId": item["id"], "unitPrice": "1000"}],
    )
    project = add_quote(
        client,
        token,
        project,
        "Supplier Two",
        [{"itemId": item["id"], "unitPrice": "900"}],
    )
    first, second = project["quotations"]

    first_choice = client.patch(
        f"/api/quotation-projects/{project['id']}/quotes/{first['id']}/preference",
        headers=authorization(token),
        json={"preferred": True},
    )
    second_choice = client.patch(
        f"/api/quotation-projects/{project['id']}/quotes/{second['id']}/preference",
        headers=authorization(token),
        json={"preferred": True},
    )

    assert first_choice.status_code == 200
    assert second_choice.status_code == 200
    selected = second_choice.get_json()["data"]
    assert selected["preferredQuoteId"] == second["id"]
    assert selected["status"] == "supplier_selected"
    assert [quote["preferred"] for quote in selected["quotations"]] == [False, True]


def test_supplier_validity_date_is_optional(client, register_user):
    owner = register_user("quote-no-date", "quote-no-date@example.com")
    token = owner["token"]
    project = create_project(client, token, "Quote without expiry")
    project = add_item(client, token, project["id"], "Consulting", "1", "job")
    item = project["items"][0]

    project = add_quote(
        client,
        token,
        project,
        "No-expiry Supplier",
        [{"itemId": item["id"], "unitPrice": "5000.00"}],
        validUntil=None,
    )

    assert project["quotations"][0]["validUntil"] is None


def test_new_item_prices_are_updated_across_owned_supplier_quotes(
    client,
    register_user,
):
    owner = register_user("quote-bulk-owner", "quote-bulk-owner@example.com")
    intruder = register_user(
        "quote-bulk-intruder",
        "quote-bulk-intruder@example.com",
    )
    token = owner["token"]
    project = create_project(client, token, "Renovation materials")
    project = add_item(client, token, project["id"], "Cement", "10", "bags")
    cement = project["items"][0]
    project = add_quote(
        client,
        token,
        project,
        "Supplier One",
        [{"itemId": cement["id"], "unitPrice": "800"}],
    )
    project = add_quote(
        client,
        token,
        project,
        "Supplier Two",
        [{"itemId": cement["id"], "unitPrice": "790"}],
    )
    project = add_item(client, token, project["id"], "Sand", "2", "loads")
    sand = project["items"][1]
    first_quote, second_quote = project["quotations"]

    intruder_response = client.patch(
        f"/api/quotation-projects/{project['id']}/items/{sand['id']}/prices",
        headers=authorization(intruder["token"]),
        json={
            "prices": [
                {"quotationId": first_quote["id"], "unitPrice": "5000"},
            ]
        },
    )
    assert intruder_response.status_code == 404

    response = client.patch(
        f"/api/quotation-projects/{project['id']}/items/{sand['id']}/prices",
        headers=authorization(token),
        json={
            "prices": [
                {"quotationId": first_quote["id"], "unitPrice": "5000"},
                {"quotationId": second_quote["id"], "unitPrice": "5100"},
            ]
        },
    )

    assert response.status_code == 200, response.get_json()
    updated = response.get_json()["data"]
    assert [quote["breakdown"]["coverage"] for quote in updated["quotations"]] == [
        100,
        100,
    ]
    assert updated["quotations"][0]["prices"][-1] == {
        "itemId": sand["id"],
        "unitPrice": "5000.00",
    }
