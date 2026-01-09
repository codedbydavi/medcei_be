from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import EpidemiologicalModel, SimulationParameter, SimulationStatus, SimulationSummaryResult, SimulationTimeSeries, db
from sqlalchemy import func
from models import Simulation, User
from decorator import simulations_logs
from simulation_engine import SIMULATION_FUNCTIONS


simulate_bp = Blueprint('simulate', __name__)

@simulate_bp.route("/start", methods=["POST"])
@jwt_required()
@simulations_logs(event_type="START SIMULATION")
def start_simulation():
    data = request.get_json()
    current_user = User.query.filter_by(id=get_jwt_identity()).first()

    model_id = data.get("model_id")
    name = data.get("name")

    n_total = data.get('population')
    s0 = data.get('s_initial')
    i0 = data.get('i_initial')
    r0 = data.get('r_initial')
    beta = data.get('beta')
    gamma = data.get('gamma')
    mu = data.get('mu')
    duration_days = data.get('duration_days', 100)
    
    parameters = {
        "population": n_total,
        "s_initial": s0,
        "i_initial": i0,
        "r_initial": r0,
        "beta": beta,
        "gamma": gamma,
        "mu": mu,
        "duration_days" :duration_days
    }

    if duration_days > 110:
        return jsonify({"msg": "Limite máximo de 100 dias atingido"}), 400
    
    running_status = SimulationStatus.query.filter_by(name='RUNNING').first()
    if not running_status:
        return jsonify({"msg": "Status RUNNING não encontrado"}), 500
    
    new_sim = Simulation(
        user_id=current_user.id,
        model_id=model_id,
        name=name,
        simulation_status_id=running_status.id,
        duration_days=duration_days
    )

    db.session.add(new_sim)
    db.session.commit()

    # Guarda os paramêtros utilizados
    for key, value in parameters.items():
        db.session.add(SimulationParameter(
            simulation_id=new_sim.id,
            param_key=key,
            param_value=value if isinstance(value, (int, float)) else None
        ))
    db.session.commit()

    return jsonify({"msg": "Simulação criada!", "simulation_id": new_sim.id})

@simulate_bp.route("/run_chunk/<sim_id>", methods=["POST"])
@jwt_required()
def run_simulation_chunk(sim_id):
    sim = Simulation.query.get_or_404(sim_id)

    batch_size = request.json.get('batch_size', 10)

    # 1. Verificação de Status (Early Return)
    if sim.status and sim.status.name in ["PAUSED", "FINISHED"]:
        return jsonify({
            "msg": f"Simulação está {sim.status.name}",
            "status": sim.status.name
        }), 200

    # 2. Preparação de Parâmetros
    last_point = SimulationTimeSeries.query.filter_by(simulation_id=sim.id).order_by(SimulationTimeSeries.time_step.desc()).first()
    # Recupa os paramêtros
    params = {p.param_key: p.param_value for p in sim.parameters}
    model_name = sim.model.name

    if not last_point:
        current_state = {
            'day': -1, 
            'S': float(params['s_initial']),
            'I': float(params['i_initial']),
            'R': float(params.get('r_initial', 0)),
            'D': float(params.get('d_initial', 0))
        }
    else:
        current_state = {
            'day': last_point.time_step,
            'S': last_point.susceptible_count,
            'I': last_point.infected_count,
            'R': last_point.recovered_count,
            'D': getattr(last_point, 'dead_count', 0)
        }

    new_points_buffer = []
    limit_days = int(sim.duration_days)
    simulation_finished = False

    for _ in range(batch_size):
        try:
            next_step = SIMULATION_FUNCTIONS[model_name](current_state, params)
        except KeyError:
            return jsonify({"msg": f"Modelo {model_name} não implementado"})
        
        new_entry = SimulationTimeSeries(
            simulation_id=sim.id,
            time_step=next_step['day'],
            susceptible_count=round(next_step['S']),
            infected_count=round(next_step['I']),
            recovered_count=round(next_step['R']),
            dead_count=round(next_step['D'])
        )

        new_points_buffer.append(new_entry)
        current_state = next_step

        is_last_day = (next_step['day'] + 1) >= limit_days
        is_eradicated = next_step['I'] < 0.5 # Se não houver mais comtaminação

        if is_last_day or is_eradicated:
            simulation_finished = True
            break

    db.session.add_all(new_points_buffer)

    if simulation_finished:
        finished_status = SimulationStatus.query.filter_by(name="FINISHED").first()
        if finished_status:
            sim.simulation_status_id = finished_status.id

        max_in_db = db.session.query(func.max(SimulationTimeSeries.infected_count))\
            .filter_by(simulation_id=sim.id).scalar() or 0
        
        max_in_buffer = max(p.infected_count for p in new_points_buffer) if new_points_buffer else 0
        peak_infected_count = max(max_in_db, max_in_buffer)
        
        if new_points_buffer:
            last_point = new_points_buffer[-1]
            final_S = last_point.susceptible_count
            final_I = last_point.infected_count
            final_R = last_point.recovered_count
            final_D = last_point.dead_count
            final_day = last_point.time_step
        else:
            final_S = current_state['S']
            final_I = current_state['I']
            final_R = current_state['R']
            final_D = current_state['D']
            final_day = current_state['day']

        total_population = final_S + final_I + final_R + final_D

        if total_population > 0:
            # Attack Rate: (Quem já passou pela doença / População Total)
            attack_rate_val = ((final_R + final_D) / total_population) * 100
                
            # Peak Prevalence: (Máximo de Infetados / População Total)
            peak_prevalence_val = (peak_infected_count / total_population) * 100
        else:
            attack_rate_val = 0
            peak_prevalence_val = 0

        # Salva os Resumos
        results_to_save = [
            # Contagens Absolutas
            SimulationSummaryResult(simulation_id=sim.id, result_key='peak_infected', result_value=peak_infected_count),
            SimulationSummaryResult(simulation_id=sim.id, result_key='final_recovered', result_value=final_R),
            SimulationSummaryResult(simulation_id=sim.id, result_key='final_deaths', result_value=final_D),
                
            # Métricas Epidemiológicas
            SimulationSummaryResult(simulation_id=sim.id, result_key='epidemic_duration', result_value=final_day),
            SimulationSummaryResult(simulation_id=sim.id, result_key='attack_rate', result_value=round(attack_rate_val, 2)),      # Ex: 50.40 (%)
            SimulationSummaryResult(simulation_id=sim.id, result_key='peak_prevalence', result_value=round(peak_prevalence_val, 2)) # Ex: 12.50 (%)
            ]
            
        db.session.add_all(results_to_save)
        
    db.session.commit()

    return jsonify({
        "status": sim.status.name if sim.status else "RUNNING",
        "new_data": [p.to_json() for p in new_points_buffer],
        "finished": simulation_finished
    })



@simulate_bp.route("/pause/<int:sim_id>", methods=["POST"])
@jwt_required()
@simulations_logs(event_type="PAUSE SIMULATION")
def pause(sim_id):
    sim = Simulation.query.get_or_404(sim_id)
    paused_status = SimulationStatus.query.filter_by(name="PAUSED").first()

    if not paused_status:
        return jsonify({"msg": "Status PAUSED não encontrado"}), 500
    
    sim.simulation_status_id = paused_status.id
    db.session.commit()
    return jsonify({"msg": "Simulação pausada"})

@simulate_bp.route("/resume/<int:sim_id>", methods=["POST"])
@jwt_required()
@simulations_logs(event_type="RESUME SIMULATION")
def resume(sim_id):
    sim = Simulation.query.get_or_404(sim_id)
    resume_status = SimulationStatus.query.filter_by(name="RUNNING").first()

    if not resume_status:
        return jsonify({"msg": "Status RESUME não encontrado"}), 500
    
    sim.simulation_status_id = resume_status.id
    db.session.commit()
    return jsonify({"msg": "Simulação retomada"})