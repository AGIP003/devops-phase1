
from app.extensions import bcrypt

def hash_password(password):
    return bcrypt.generate_password_hash(password, rounds=12).decode("utf-8")

def verify_password(password, hashed):
    return bcrypt.check_password_hash(hashed, password)


