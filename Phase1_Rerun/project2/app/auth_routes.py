from flask import Blueprint, current_app, request, jsonify, abort, g

from app.extensions import bcrypt, mail, limiter
from app.auth import hash_password, verify_password, validate_password_strength
from app.services.user_service import (
    DuplicateUserError,
    create_user,
    get_user_by_email,
    update_user_display_name,
    update_user_password,
)
from app.middleware import (
    login_required,
    recent_authentication_required,
)
from app.serializers import authenticated_user_to_dict
from app.services.external_identity_service import (
    ExternalAccountLinkRequiredError,
    ExternalIdentityConflictError,
    authenticate_external_identity,
    link_external_identity,
)
from app.services.google_identity_service import (
    GoogleIdentityProviderUnavailableError,
    InvalidGoogleCredentialError,
    verify_google_credential,
)
from app.services.token_service import issue_access_token
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from config import get_config

config = get_config()
SECRET_KEY = config.SECRET_KEY
FRONTEND_URL = config.FRONTEND_URL.rstrip("/")

if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY not found in configuration")

def get_serializer():
    return URLSafeTimedSerializer(SECRET_KEY)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route("/google", methods=["POST"])
@limiter.limit("5 per minute")
def google_login():
    data=request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="Invalid JSON")

    credential = data.get("credential")

    if not isinstance(credential, str) or not credential.strip():
        abort(400, description="Google credential is required")

    try:
        verified_identity = verify_google_credential(credential)
        user = authenticate_external_identity(verified_identity)
    except InvalidGoogleCredentialError:
        abort(401, description="Invalid Google credential")
    except ExternalAccountLinkRequiredError:
        return jsonify(
            {
                "error": "account_link_required",
                "message": (
                    "Sign in to the existing MoneyTiq account before linking Google."
                ),
            }
        ), 409
    except GoogleIdentityProviderUnavailableError:
        current_app.logger.warning(
            "Google identity verification is temporarily unavailable"
        )
        abort(
            503,
            description="Google authentication is temporarily unavailable",
        )

    token = issue_access_token(user)

    return jsonify(
        {
            "message": "Google sign-in successful",
            "token": token,
            "user": authenticated_user_to_dict(user),
        }
    ), 200

@auth_bp.route("/google/link", methods=["POST"])
@limiter.limit("5 per hour")
@login_required
@recent_authentication_required
def link_google_identity():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="Invalid JSON")

    credential = data.get("credential")

    if not isinstance(credential, str) or not credential.strip():
        abort(400, description="Google credential is required")

    try:
        verified_identity = verify_google_credential(credential)
        link_external_identity(
            g.authenticated_user,
            verified_identity,
        )
    except InvalidGoogleCredentialError:
        abort(401, description="Invalid Google credential")
    except ExternalIdentityConflictError:
        return jsonify(
            {
                "error": "external_identity_conflict",
                "message": "This Google identity cannot be linked.",
            }
        ), 409
    except GoogleIdentityProviderUnavailableError:
        current_app.logger.warning(
            "Google identity verification is temporarily unavailable"
        )
        abort(
            503,
            description="Google authentication is temporarily unavailable",
        )

    return jsonify(
        {
            "message": "Google account linked successfully",
            "user": authenticated_user_to_dict(
                g.authenticated_user
            ),
        }
    ), 200

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

    try:
        new_user = create_user(email, username, password_hash)
    except DuplicateUserError:
        abort(409, description="The email or username is already in use.")

    token = issue_access_token(new_user)

    return jsonify(
        {
            "message": "User registered",
            "token": token,
            "user": authenticated_user_to_dict(new_user),
        }), 201


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

    stored_hash = user.password_hash

    if stored_hash is None or not verify_password(password, stored_hash):
        abort(401, description="Invalid email or password")

    token = issue_access_token(user)

    return jsonify({"message": "Login successful", "token": token,  'user': authenticated_user_to_dict(user) }), 200


@auth_bp.route('/profile', methods=['PATCH'])
@login_required
def update_profile():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="Invalid JSON")

    display_name = data.get("display_name")

    if not isinstance(display_name, str):
        abort(400, description="Display name must be text")

    display_name = display_name.strip()

    if not display_name:
        abort(400, description="Display name is required")

    if len(display_name) > 100:
        abort(
            400,
            description="Display name must be 100 characters or fewer",
        )

    user = update_user_display_name(
        g.authenticated_user,
        display_name,
    )

    return jsonify(
        {
            "message": "Profile updated",
            "user": authenticated_user_to_dict(user),
        }
    ), 200

@auth_bp.route('/password_reset_request', methods=['POST'])
@limiter.limit("5 per hour")
def password_reset_request():
    if not current_app.config.get("PASSWORD_RESET_ENABLED", False):
        abort(
            503,
            description="Password reset is temporarily unavailable",
        )

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
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

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
        current_app.logger.exception("Failed to send password reset email")
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
    #hash password
    password_hash = hash_password(new_password)

    #Store in db
    update_user_password(user, password_hash)

    return jsonify({"message": "Password reset succesfully"}), 200
