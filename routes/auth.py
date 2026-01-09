from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies, set_refresh_cookies
from hooks.user_hook import current_user, current_user_role
from models import User, db
from firebase_admin import auth as firebase_auth


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    header = request.headers.get('Authorization')
    if not header or not header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    id_token = header.split(' ')[1]
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        data = request.get_json()
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if User.query.filter_by(firebase_uid=firebase_uid).first() or User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        new_user = User(firebase_uid=firebase_uid, email=email, first_name=first_name, last_name=last_name)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User registered successfully",
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@auth_bp.route('/login', methods=['POST'])
def login():
    header = request.headers.get('Authorization')
    if not header or not header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    id_token = header.split(' ')[1]
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']

        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        access_token = create_access_token(identity=user.id, additional_claims={"role": user.user_type.name})
        refresh_token = create_refresh_token(identity=user.id, additional_claims={"role": user.user_type.name})
        response = jsonify({
            "msg": "Login realizado com sucesso",
            "user": user.to_json()
        })

        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = current_user()
    role = current_user_role()
    access_token = create_access_token(identity=identity, additional_claims={"role": role})
    response = jsonify({"msg": "Novo token de acesso gerado"})
    set_access_cookies(response, access_token)
    return response, 200