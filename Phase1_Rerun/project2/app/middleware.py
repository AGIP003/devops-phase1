import jwt
import os
from functools import wraps
from flask import jsonify, request, g, current_app, abort
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY not found in environment variables")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get("Authorization", "")

        #Check if it starts  with Bearer
        if not auth or not auth.startswith("Bearer "):
            abort(401, description = "Invalid or missing Authorization")

        #Extract the token
        parts = auth.split(" ")
        if len(parts) != 2:
            abort(401, description="Invalid Authorization header format")

        token = parts[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        except jwt.ExpiredSignatureError as e:
            abort(401, description="Token has expired")
        except jwt.InvalidTokenError as e:
            abort(401, description="Invalid token") 

        g.current_user = {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "role": payload["role"]
        }   

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorators to restrict routes to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not hasattr(g, 'current_user'):
            abort(401, "Authentication required")

        
        user_role = g.current_user.get("role")
        if  not isinstance(g.current_user, dict):
            abort(403, description="Invalid data format")
                 
        if user_role != "admin":
            abort(403, description="Admin access required")

        return f(*args, **kwargs)
    return decorated_function
        