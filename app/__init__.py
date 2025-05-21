from flask import Flask
from .extensions import mongo, login_manager, bcrypt
import os
from dotenv import load_dotenv

def create_app():
    # --- Cargar variables de entorno ---
    load_dotenv()

    app = Flask(__name__)

    # --- Configuración ---
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    if not app.config["MONGO_URI"]:
        raise RuntimeError("MONGO_URI no está definida. Verifica tu archivo .env o variables de entorno en Render.")

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "mysecret")  # Valor por defecto

    # --- Inicializar extensiones ---
    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # --- Registrar Blueprints ---
    
    from .auth import auth as auth_blueprint
    
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # --- Cargar usuario ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.get_by_id(user_id)

    return app
