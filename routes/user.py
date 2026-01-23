from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies, set_refresh_cookies
from hooks.user_hook import current_user, current_user_role
from models import User, UserStatus, UserType, db
from firebase_admin import auth as firebase_auth


user_bp = Blueprint('user', __name__)

@user_bp.route('/me', methods=['GET'])
@jwt_required(optional=True)
def get_current_user_data():
    uid = get_jwt_identity()

    if not uid:
        return jsonify({"user": None}), 200

    user = User.query.get(uid)
    if not user:
        return jsonify({"user": None}), 200

    return jsonify({
        "user": user.to_json()
    }), 200


@user_bp.route('/profile', methods=['POST'])
@jwt_required()
def profile():
    try:
        user_id = current_user()

        user_profile = User.query.get(user_id)

        if not user_profile:
            return jsonify({"error": "Utilizador não encontrado"}), 404

        return jsonify({
            "message": "Utilizador encontrado com sucesso",
            "user": user_profile.to_json()
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/edit', methods=['PATCH'])
@jwt_required()
def edit():
    try:
        user_id = current_user()

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        user.first_name = data.get('firstName', user.first_name)
        user.last_name = data.get('lastName', user.last_name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify({"message": "User updated successfully", "user": user.to_json()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/all_users', methods=['GET'])
@jwt_required()
def all_users():
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403
    try:
        users = User.query.filter(User.user_type_id).all()
        users_list = [user.to_json() for user in users]
        return jsonify({"users": users_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/delete/<string:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        firebase_auth.delete_user(user.firebase_uid)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route("/change_status/<string:user_id>", methods=["PATCH"])
@jwt_required()
def change_status(user_id):
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilizador não encontrado"}), 404

    active = UserStatus.query.filter_by(name='ACTIVE').first()
    inactive = UserStatus.query.filter_by(name='INACTIVE').first()

    if user.user_status_id == active.id:
        user.user_status_id = inactive.id
        new_label = 'INACTIVE'
    else:
        user.user_status_id = active.id
        new_label = 'ACTIVE'
    
    try:
        db.session.commit()
        db.session.refresh(user) 
        
        return jsonify({
            "msg": "Status atualizado", 
            "new_status": new_label 
        }), 200

    except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@user_bp.route("/change_role/<string:user_id>", methods=["PATCH"])
@jwt_required()
def change_role(user_id):

    try:
        if current_user_role() != 'admin':
            return jsonify({"error": "Acesso proibido: Admins apenas"}), 403

        data = request.get_json()
        new_role_name = data.get("role")

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Utilizador não encontrado"}), 404

        target_role = UserType.query.filter_by(name=new_role_name).first()
        if not target_role:
            return jsonify({"error": "Cargo inválido"}), 400

        user.user_type_id = target_role.id
        db.session.commit()

        return jsonify({"msg": f"Cargo de {user.first_name} alterado para {new_role_name}"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500