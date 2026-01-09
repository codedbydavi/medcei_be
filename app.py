from datetime import timedelta
import os
from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager
from routes.auth import auth_bp
from routes.simulate import simulate_bp
from routes.stats import stats_bp
from models import db
import firebase_admin
from firebase_admin import credentials
from flask_cors import CORS

# 1. Variáveis de ambiente 
load_dotenv()

app = Flask(__name__)

# 2. Configurações
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

# Configurações de Cookies e Segurança
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False 
app.config["JWT_COOKIE_SAMESITE"] = "Lax"

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})
db.init_app(app)
jwt = JWTManager(app)

# 4. Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# 5. Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(simulate_bp, url_prefix='/simulation')
app.register_blueprint(stats_bp, url_prefix='/stats')
 
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)