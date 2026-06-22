import os
from hashlib import sha256

import requests
from dotenv import load_dotenv


load_dotenv()
API_BASE = os.getenv("API_BASE_URL", "http://localhost:5000/api").rstrip("/")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
REQUEST_TIMEOUT = 12


def _error_message(response, fallback):
    try:
        payload = response.json()
    except ValueError:
        return fallback
    return payload.get("message") or payload.get("error") or fallback


def verify_telegram_link(token, telegram_id):
    """Exchange a one-time web code for a JWT and link the Telegram account."""
    response = requests.post(
        f"{API_BASE}/telegram/verify",
        json={"token": token, "telegram_id": telegram_id},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        payload = response.json()
        if not payload.get("token"):
            raise RuntimeError("The server linked the account but returned no access token")
        return payload

    raise RuntimeError(_error_message(response, "Unable to link Telegram account"))


def get_telegram_session(telegram_id):
    """Resolve a linked Telegram user and obtain a fresh short-lived JWT."""
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured for the bot")

    bot_auth = sha256(TELEGRAM_BOT_TOKEN.encode("utf-8")).hexdigest()
    response = requests.post(
        f"{API_BASE}/telegram/session",
        json={"telegram_id": telegram_id},
        headers={"X-Telegram-Bot-Auth": bot_auth},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        return response.json()

    raise RuntimeError(_error_message(response, "Unable to check Telegram link status"))


def create_transaction(
    token,
    description,
    amount,
    category,
    transaction_type,
    date,
    payment_method,
):
    response = requests.post(
        f"{API_BASE}/transactions",
        json={
            "description": description,
            "amount": amount,
            "category": category,
            "type": transaction_type,
            "date": date,
            "payment_method": payment_method,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 201:
        return response.json()

    raise RuntimeError(_error_message(response, "Failed to create transaction"))


def get_transactions(token):
    response = requests.get(
        f"{API_BASE}/transactions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        return response.json()

    raise RuntimeError(_error_message(response, "Failed to fetch transactions"))


def get_telegram_preferences(token):
    response = requests.get(
        f"{API_BASE}/telegram/preferences",
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        return response.json()
    raise RuntimeError(_error_message(response, "Failed to load Telegram preferences"))


def update_telegram_preferences(token, **updates):
    response = requests.put(
        f"{API_BASE}/telegram/preferences",
        json=updates,
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        return response.json()
    raise RuntimeError(_error_message(response, "Failed to update Telegram preferences"))
