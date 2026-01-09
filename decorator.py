import time
from functools import wraps
from models import db
from flask_jwt_extended import get_jwt_identity
from flask import request, Flask, jsonify
import firebase_admin
from firebase_admin import credentials, auth
import os

from models import SystemLog, User


def simulations_logs(event_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            identity = get_jwt_identity()
            user = User.query.filter_by(id=identity).first()
            sim_id = kwargs.get('sim_id')
            
            log_level = "INFO"
            message = f"Operação {event_type} realizada com sucesso"

            try:
                # Executamos a função original
                response = func(*args, **kwargs)

                if isinstance(response, tuple) and len(response) > 1:
                    status_code = response[1]
                    if status_code >= 400:
                        log_level = "WARNING"
                        data = response[0].get_json() if hasattr(response[0], 'get_json') else {}
                        message = data.get('msg', f"Falha na validação: Status {status_code}")

                return response

            except Exception as e:
                log_level = "ERROR"
                message = f"Erro crítico: {str(e)}"
                raise e
            
            finally:
                if user:
                    log_entry = SystemLog(
                        user_id=user.id,
                        simulation_id=sim_id,
                        event_type=event_type,
                        log_level=log_level,
                        message=message,
                    )
                    db.session.add(log_entry)
                    db.session.commit()
        return wrapper
    return decorator

