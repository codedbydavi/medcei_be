from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from hooks.user_hook import current_user_role
from models import EpidemiologicalModel, Simulation, User, db
from sqlalchemy import func
from sqlalchemy.orm import joinedload

stats_bp = Blueprint('stats', __name__)

@stats_bp.route("/summary", methods=["GET"])
@jwt_required()
def stats_summary():
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403
    
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
        
@stats_bp.route("/user_simulations", methods=["GET"])
@jwt_required()
def user_simulations():
    user_id = get_jwt_identity()
    
    simulations = Simulation.query.options(joinedload(Simulation.model))\
                                  .filter_by(user_id=user_id).all()

    simulations_data = [{
        "id": sim.id,
        "name": sim.name,
        "model": sim.model.name if sim.model else None,
        "status": sim.status.name if sim.status else None,
        "created_at": sim.created_at.isoformat(),
        "duration_days": sim.duration_days,
    } for sim in simulations]

    return jsonify({
        "simulations": simulations_data, 
        "total_simulations": len(simulations_data)
    }), 200

@stats_bp.route("/user_stats", methods=["GET"])
@jwt_required()
def user_stats():
    user_id = get_jwt_identity()
    
    try:
        total_simulations = Simulation.query.filter_by(user_id=user_id).count()
        
        simulation_this_month = Simulation.query.filter(
            Simulation.user_id == user_id,
            func.date_format("%Y-%m", Simulation.created_at) == func.date_format("%Y-%m", func.current_date())
        ).count()

        average_duration = db.session.query(
            func.avg(Simulation.duration_days)
        ).filter(Simulation.user_id == user_id).scalar() or 0

        return jsonify({
            "total_simulations": total_simulations,
            "simulations_this_month": simulation_this_month,
            "average_duration_days": round(float(average_duration), 2)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500