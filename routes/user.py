from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies, set_refresh_cookies
from hooks.user_hook import current_user, current_user_role
from models import User, UserStatus, db
from firebase_admin import auth as firebase_auth


user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['POST'])
def profile():
    try:
        user = current_user()

        user_profile = User.query.filter_by(firebase_uid=user.firebase_uid).first()

        if not user_profile:
            return jsonify({"error": "Utilizador não encontrado"}), 404

        return jsonify({
            "message": "Utilizador encontrado com sucesso",
            "user": user_profile.to_json()
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/edit', methods=['PUT'])
def edit():
    try:
        user = current_user()

        user = User.query.filter_by(firebase_uid=user.firebase_uid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify({"message": "User updated successfully", "user": user.to_json()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/all_users', methods=['GET'])
@jwt_required(refresh=True)
def all_users():
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403
    try:
        users = User.query.all()
        users_list = [user.to_json() for user in users]
        return jsonify({"users": users_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_user(user_id):
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

    
@user_bp.route("/change_status/<int:user_id>", methods=["GET"])
@jwt_required()
def change_status(user_id):
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403

    active_status = UserStatus.query.filter_by(name='ACTIVE').first()
    inactive_status = UserStatus.query.filter_by(name='INACTIVE').first()

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilizador não encontrado"}), 404

    if user.user_status_id == active_status.id:
        user.user_status_id = inactive_status.id
    else:
        user.user_status_id = active_status.id

    db.session.commit()

    return jsonify({"msg": "Status do usuário atualizado com sucesso"}), 200