import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserType(db.Model):
    __tablename__ = 'user_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class UserStatus(db.Model):
    __tablename__ = 'user_statuses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    user_type_id = db.Column(
        db.Integer,
        db.ForeignKey('user_types.id'),
        nullable=False,
        default=2
    )

    user_status_id = db.Column(
        db.Integer,
        db.ForeignKey('user_statuses.id'),
        nullable=False,
        default=1
    )

    user_type = db.relationship('UserType', backref='users')
    user_status = db.relationship('UserStatus', backref='users')

    def to_json(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "fullName": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "role": self.user_type.name,
            "status": self.user_status.name
        }

class EpidemiologicalModel(db.Model):
    __tablename__ = 'epidemiological_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    version = db.Column(db.String(50), nullable=False)

class SimulationStatus(db.Model):
    __tablename__ = 'simulation_statuses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Simulation(db.Model):
    __tablename__ = 'simulations'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id'),
        nullable=False
    )

    simulation_status_id = db.Column(
        db.Integer,
        db.ForeignKey('simulation_statuses.id'),
        nullable=False
    )

    model_id = db.Column(
        db.Integer,
        db.ForeignKey('epidemiological_models.id'),
        nullable=False
    )

    name = db.Column(db.String(150), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('simulations', cascade="all, delete-orphan"))
    status = db.relationship('SimulationStatus')
    model = db.relationship('EpidemiologicalModel')

    parameters = db.relationship(
        'SimulationParameter', 
        backref='simulation', 
        cascade="all, delete-orphan"
    )
    summary_results = db.relationship(
        'SimulationSummaryResult', 
        backref='simulation', 
        cascade="all, delete-orphan"
    )
    time_series = db.relationship(
        'SimulationTimeSeries', 
        backref='simulation', 
        cascade="all, delete-orphan"
    )
    logs = db.relationship(
        'SystemLog', 
        backref='simulation', 
        cascade="all, delete-orphan"
    )

class SimulationParameter(db.Model):
    __tablename__ = 'simulation_parameters'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    simulation_id = db.Column(
        db.String(36),
        db.ForeignKey('simulations.id'),
        nullable=False
    )

    param_key = db.Column(db.String(100), nullable=False)
    param_value = db.Column(db.Float)


class SimulationSummaryResult(db.Model):
    __tablename__ = 'simulation_summary_results'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    simulation_id = db.Column(
        db.String(36),
        db.ForeignKey('simulations.id'),
        nullable=False
    )

    result_key = db.Column(db.String(100), nullable=False)
    result_value = db.Column(db.Float)


class SimulationTimeSeries(db.Model):
    __tablename__ = 'simulation_time_series'

    simulation_id = db.Column(
        db.String(36),
        db.ForeignKey('simulations.id'),
        primary_key=True
    )

    time_step = db.Column(db.Integer, primary_key=True)

    susceptible_count = db.Column(db.Integer, nullable=False)
    infected_count = db.Column(db.Integer, nullable=False)
    recovered_count = db.Column(db.Integer, nullable=False)
    dead_count = db.Column(db.Integer, nullable=False, default=0)

    def to_json(self):
        return {
            "day": self.time_step,
            "S": self.susceptible_count,
            "I": self.infected_count,
            "R": self.recovered_count,
            "D": self.dead_count
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    log_level = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id')
    )

    simulation_id = db.Column(
        db.String(36),
        db.ForeignKey('simulations.id')
    )
