from flask_jwt_extended import get_jwt_identity, get_jwt

def current_user():
    return get_jwt_identity()

def current_user_role():
    return get_jwt().get("role")