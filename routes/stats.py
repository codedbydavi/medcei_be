from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from hooks.user_hook import current_user_role
from models import EpidemiologicalModel, Simulation, SystemLog, User, db
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
    
@stats_bp.route('/dashboard-charts', methods=['GET'])
@jwt_required()
def get_dashboard_charts():
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403

    seven_days_ago = datetime.now() - timedelta(days=7)
    
    daily_simulations = db.session.query(
        func.date(Simulation.created_at).label('date'),
        func.count(Simulation.id).label('count')
    ).filter(Simulation.created_at >= seven_days_ago)\
     .group_by(func.date(Simulation.created_at))\
     .order_by(func.date(Simulation.created_at)).all()

    model_distribution = db.session.query(
        EpidemiologicalModel.name,
        func.count(Simulation.id).label('count')
    ).join(Simulation, Simulation.model_id == EpidemiologicalModel.id)\
     .group_by(EpidemiologicalModel.name).all()

    return jsonify({
        "lineChart": [{"date": str(d.date), "count": d.count} for d in daily_simulations],
        "pieChart": [{"name": m.name, "value": m.count} for m in model_distribution]
    })

@stats_bp.route('/logs/<int:limit>', methods=['GET'])
@jwt_required()
def getSystemLogs(limit):
    if current_user_role() != 'admin':
        return jsonify({"error": "Acesso proibido: Admins apenas"}), 403

    if limit > 100:
        limit = 100

    try:
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(limit).all()

        return jsonify([{
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "log_level": log.log_level,
            "event_type": log.event_type,
            "message": log.message,
            "user_id": log.user_id,
            "simulation_id": log.simulation_id
        } for log in logs]), 200
    
    except Exception as e:
        print(f"Erro ao buscar logs: {e}") 
        return jsonify({"error": "Erro interno ao processar logs"}), 500

@stats_bp.route("/user_stats", methods=["GET"])
@jwt_required()
def user_stats():
    user_id = get_jwt_identity()
    
    try:
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_simulations = Simulation.query.filter_by(user_id=user_id).count()

        simulation_this_month = Simulation.query.filter(
            Simulation.user_id == user_id,
            Simulation.created_at >= first_day_of_month
        ).count()

        average_duration = db.session.query(
            func.avg(Simulation.duration_days)
        ).filter_by(user_id=user_id).scalar() or 0

        average_sim_per_month = db.session.query(
            func.count(func.distinct(func.date_format(Simulation.created_at, "%Y-%m")))
        ).filter_by(user_id=user_id).scalar() or 0

        return jsonify({
            "total_simulations": total_simulations,
            "simulations_this_month": simulation_this_month,
            "average_duration_days": round(float(average_duration), 2),
            "average_simulations_per_month": round(float(average_sim_per_month), 2)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/recent_user_sim", methods=["GET"])
@jwt_required()
def recent_user_sim():
    user_id = get_jwt_identity()
    
    try:
        user_simulations = Simulation.query.options(joinedload(Simulation.model))\
                                           .filter_by(user_id=user_id)\
                                           .order_by(Simulation.created_at.desc())\
                                           .limit(5)\
                                           .all()

        if not user_simulations:
            return jsonify({"simulations": []}), 200

        simulations_list = []
        for sim in user_simulations:
            simulations_list.append({
                "id": sim.id,
                "name": sim.name,
                "model": sim.model.name if sim.model else None,
                "status": sim.status.name if sim.status else None,
                "created_at": sim.created_at.isoformat(),
                "duration_days": sim.duration_days,
            })
        return jsonify({"simulations": simulations_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@stats_bp.route("/all_user_sim", methods=["GET"])
@jwt_required()
def all_user_sim():
    user_id = get_jwt_identity()
    
    try:
        user_simulations = Simulation.query.options(joinedload(Simulation.model))\
                                           .filter_by(user_id=user_id)\
                                           .order_by(Simulation.created_at.desc())\
                                           .all()

        if not user_simulations:
            return jsonify({"simulations": []}), 200

        simulations_list = []
        for sim in user_simulations:
            simulations_list.append({
                "id": sim.id,
                "name": sim.name,
                "model": sim.model.name if sim.model else None,
                "status": sim.status.name if sim.status else None,
                "created_at": sim.created_at.isoformat(),
                "duration_days": sim.duration_days,
            })
        return jsonify({"simulations": simulations_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500