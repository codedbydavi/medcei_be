from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Simulation, SimulationTimeSeries, db
from sqlalchemy.orm import joinedload

history_bp = Blueprint('history', __name__)

@history_bp.route("/details/<sim_id>", methods=["GET"])
@jwt_required()
def get_simulation_details(sim_id):
    user_id = get_jwt_identity()

    try:
        simulation = (
            Simulation.query
            .options(
                joinedload(Simulation.parameters),
                joinedload(Simulation.model)
            )
            .filter_by(id=sim_id, user_id=user_id)
            .first()
        )

        if not simulation:
            return jsonify({"msg": "Simulação não encontrada"}), 404

        time_series = (
            SimulationTimeSeries.query
            .filter_by(simulation_id=sim_id)
            .order_by(SimulationTimeSeries.time_step.asc())
            .all()
        )

        params_dict = {p.param_key: p.param_value for p in simulation.parameters}

        return jsonify({
            "id": simulation.id,
            "name": simulation.name,
            "model_id": simulation.model_id,
            "duration_days": simulation.duration_days,
            "parameters": params_dict,
            "history": [ts.to_json() for ts in time_series],
            "status": simulation.status.name,
            "created_at": simulation.created_at,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route("/delete/<string:sim_id>", methods=["DELETE"])
@jwt_required()
def delete_simulation(sim_id):

    try:
        user_id = get_jwt_identity()

        simulation = Simulation.query.filter_by(id=sim_id, user_id=user_id).first()
        if not simulation:
            return jsonify({"msg": "Simulação não encontrada"}), 404

        db.session.delete(simulation)
        db.session.commit()

        return jsonify({"msg": "Simulação eliminada com sucesso"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500