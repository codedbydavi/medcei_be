from datetime import timedelta
import os
from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager
from routes.auth import auth_bp
from routes.simulate import simulate_bp
from routes.stats import stats_bp
from routes.user import user_bp
from routes.history import history_bp
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
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False 

# Mude para False enquanto estiver em desenvolvimento (HTTP)
# Mude para True apenas em produção (HTTPS)
app.config["JWT_COOKIE_SECURE"] = False 

# Com Lax e Secure=False, o Chrome aceita cookies entre portas do localhost
app.config["JWT_COOKIE_SAMESITE"] = "Lax"
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token_cookie"

CORS(app, 
     resources={r"/*": {"origins": "http://localhost:3000"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"],
     expose_headers=["Set-Cookie"]
)

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
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(history_bp, url_prefix='/history')
 
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)