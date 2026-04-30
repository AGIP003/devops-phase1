from app.extensions import bcrypt


def hash_password(password):
    return bcrypt.generate_password_hash(password, rounds=12).decode("utf-8")

def verify_password(password, hashed):
    return bcrypt.check_password_hash(hashed, password)

def validate_password_strength(password):
    #Password must be more than 8 characters 
    if  len(password) < 8:
        return "The password is short.Make sure it has 8 characters."
    
    #Password must contain a number
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number."

    # Password Must contain an uppercase letter
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."

    # Password Must contain a lowercase letter
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."