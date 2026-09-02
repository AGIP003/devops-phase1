import pytest


@pytest.mark.critical
def test_register_user_factory_creates_distinct_users(register_user):
    #Arrange + Act
    owner = register_user("owner", "owner@example.com")
    intruder = register_user("intruder", "intruder@example.com")

    #Assert
    assert owner["user"]["email"] == "owner@example.com"
    assert intruder["user"]["email"] == "intruder@example.com"
    assert owner["user"]["id"] != intruder["user"]["id"]
    assert owner["token"] != intruder["token"]
