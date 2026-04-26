from flask import Blueprint, request, jsonify, abort
from app.extensions import bcrypt
from app.auth import hash_password, verify_password
from app.db import get_db_connection,get_user_by_email, insert_user_hashed_pw
import jwt
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY not found in environment variables")
    
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register_auth_route():
    data = request.get_json()

    if data is None:
        abort(400, description="Invalid Json")

    #Fetch for the trio
    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    #Check if the fields have been filled
    if not all([username, email, password]):
        abort(400, description="Missing required fields")
    
    #Password must be more than 8 characters 
    if  len(password) < 8:
        abort(400, description="The password is short.Make sure it has 8 characters.")
    
    #Password must contain a number
    if not any(char.isdigit() for char in password):
        abort(400, description="Password must contain at least one number.")

    # Password Must contain an uppercase letter
    if not any(char.isupper() for char in password):
        abort(400, description="Password must contain at least one uppercase letter.")

    # Password Must contain a lowercase letter
    if not any(char.islower() for char in password):
        abort(400, description="Password must contain at least one lowercase letter.")

    #Checking if the user exists in the db
    if get_user_by_email(email):
        abort(409, description="The email is already in use.")

    #hashing the password
    password_hash = hash_password(password)

    new_user = insert_user_hashed_pw(email, username, password_hash)

    return jsonify({"message": "User registered", "user": new_user}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if data is None:
        abort(400, description="Invalid Json")

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not all([email, password]):
        abort(400, description="Missing field!")

    user = get_user_by_email(email)
    if not user:
        abort(401, description="Invalid email or password")

    stored_hash = user["password_hash"]

    if not verify_password(password, stored_hash):
        abort(401, description="Invalid email or password")

    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({"message": "Login successful", "token": token,  'user': {
            'user_id': user["id"],
            'username': user["username"],
            'email': user["email"],
            'role': user["role"]}}), 200