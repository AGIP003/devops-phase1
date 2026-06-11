import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE =  os.getenv('API_BASE_URL', 'http://localhost:5000/api')

def register_user(username, email, password):
    """
    Register a new user via Flask aPI
    Returns the JWT token on success
    Raises Exception with error message on failure
    """
    
    url = f"{API_BASE}/auth/register"
    payload = {
        "username": username,
        "email": email,
        "password": password
    }

    response = requests.post(url, json=payload)
    if response.status_code == 201:
        data = response.json()
        return data.get("token")
    elif response.status_code == 409:
        raise Exception("Email already registered")
    else:
        error_msg = response.json().get("message", "Registration failed")
        raise Exception(f"Registration failed: {error_msg}")
    
def login_user(email, password):
    """
    Login an existing usser via Flask API
    Returns the JWT token on success
    """

    url = f"{API_BASE}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    response = requests.get(url, json=payload)
    if response.status_code == 201:
        data = response.json()
        return data.get("token")
    elif response.status_code == 401:
        raise Exception("Invalid Email or Password")
    else:
        error_msg = response.json().get("message", "Login failed")
        raise Exception(f"Login failed: {error_msg}")

def create_transaction(token, description, amount, category, type, date, payment_method):
    """
    Create a new transaction via Flask API
    Requires bearer token
    Returns the created transaction dict.
    """
    if date is None:
        from datetime import date
        date = date.today().isoformat()
    url=f"{API_BASE}/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "description": description,
        "amount": amount,
        "category": category,
        "type": type,   # "income" or "expense"
        "date": date,
        "payment_method":  payment_method
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        error_msg = response.json().get("message", "Failed to create transaction")
        raise Exception(f"Create transaction failed: {error_msg}")
def get_transaction(token):
    url = f"{API_BASE}/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        error_msg = response.json().get("message", "Failed to fetch transactions")
        raise Exception(f"Fetch transactions failed: {error_msg}")