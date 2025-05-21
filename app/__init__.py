from flask import Flask
from .extensions import mongo, login_manager, bcrypt
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)

    # --- Cargar variables de entorno ---
    load_dotenv()
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config['SECRET_KEY'] = 'mysecret'

    # Inicializar extensiones
    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # NO registrar aquí los blueprints si lo haces en configure_routes()

    # Configurar usuario loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.get_by_id(user_id)

    return app
