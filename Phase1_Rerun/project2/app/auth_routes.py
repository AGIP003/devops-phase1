from flask import Blueprint, request, jsonify, abort
from app.extensions import bcrypt, mail, limiter
from app.auth import hash_password, verify_password, validate_password_strength
from app.db import get_db_connection,get_user_by_email, insert_user_hashed_pw, update_reset_password
import jwt
from datetime import datetime, timezone, timedelta
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask_cors import CORS
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY not found in environment variables")

def get_serializer():
    return URLSafeTimedSerializer(SECRET_KEY)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
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
    
    #Validate password
    error = validate_password_strength(password)
    if error:
        abort(400, description=error)
    
    #Checking if the user exists in the db
    if get_user_by_email(email):
        abort(409, description="The email is already in use.")

    #hashing the password
    password_hash = hash_password(password)

    new_user = insert_user_hashed_pw(email, username, password_hash)

    return jsonify({"message": "User registered", "user": new_user}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute") #Max 5 login attempts per minute per IP
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
        "role": user.get("role", "user"),  # Default role is 'user'
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({"message": "Login successful", "token": token,  'user': {
            'user_id': user["id"],
            'username': user["username"],
            'email': user["email"],
            'role': user.get("role", "user")}}), 200

@auth_bp.route('/password_reset_request', methods=['POST'])
@limiter.limit("3 per hour")
def password_reset_request():
    data =request.get_json()

    if data is None:
        abort(400, description="Invalid json")    
    #Get email
    email = data.get("email", "").strip().lower()
    
    #Validate
    if not email:
        abort(400, description="Missing field")
    
    #Check user in db
    user = get_user_by_email(email)

    #Validate
    if not user:
        return jsonify({"message": "A reset link has been sent"}), 200
    
    #Reset token(expires in 1hr)
    serializer = get_serializer()
    token = serializer.dumps(email, salt='password-reset-salt')

    #Reset URL
    reset_url = f"http://localhost:3000/reset-password?token={token}"

    #Send email
    msg = Message('Password Reset Request',
                  recipients=[email])
    msg.body = f"""Hi, you requested a password reset for your Financial Tracker account. 
                Click the link below to reset your password(expires in 1 hour)
                {reset_url}

                If you didn't request this. Ignore this email.

                Financial Tracker Team
                """
    try:
        mail.send(msg)
    except Exception as e:
        abort(500, description="Failed to send email")

    return jsonify({"message": "A reset link has been sent"}), 200

@auth_bp.route('/password-reset-verify', methods=['POST'])
def password_reset_verify():
    data = request.get_json()

    if data is None:
        abort(400, description="Invalid Json")

    token = data.get('token', '')
    new_password=data.get('new_password', '')

    if not all([token, new_password]):
        abort(400, description="Missing field!")

    #Validate password
    error = validate_password_strength(new_password)
    if error:
        abort(400, description=error)

    #Verify token
    serializer = get_serializer()

    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        abort(400, description="expired")
    except BadSignature:
        abort(400, description="invalid")

    #Get the user through email
    user = get_user_by_email(email)

    if not user:
        abort(404, description="user not found")

    #get user_id
    user_id = user["id"]

    #hash password
    password_hash = hash_password(new_password)

    #Store in db
    update_reset_password(user_id, password_hash)

    return jsonify({"message": "Password reset succesfully"}), 200




