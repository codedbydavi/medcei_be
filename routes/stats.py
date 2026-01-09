from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import EpidemiologicalModel, Simulation, db
from models import User
from sqlalchemy import func

stats_bp = Blueprint('stats', __name__)

@stats_bp.route("summary", methods=["GET"])
@jwt_required()
def stats_summary():
    current_user = User.query.filter_by(id=get_jwt_identity()).first()

    if current_user.role != "admin":
        return jsonify("Permissão negada: Utilizado precisa ser admin", 403)
    
    try:
        total_simulations = Simulation.query.count()
        most_used_model = db.session.query(
                EpidemiologicalModel.name, 
                func.count(Simulation.id).label('total')
            ).join(Simulation, Simulation.model_id == EpidemiologicalModel.id)\
            .group_by(EpidemiologicalModel.name)\
            .order_by(func.count(Simulation.id).desc())\
            .first()
        
        return jsonify({
            "total_users": User.query.count(),
            "total_simulations": total_simulations,
            "most_used_model": most_used_model[0] if most_used_model else "Nenhum",
            "model_usage_count": most_used_model[1] if most_used_model else 0
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    
