from flask import Flask
from .extensions import mongo, login_manager, bcrypt
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)

    # --- Cargar variables de entorno desde .env si estás localmente ---
    load_dotenv()

    # --- Configuración de MongoDB ---
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # ← ESTA ES LA CORRECTA
    app.config['SECRET_KEY'] = 'mysecret'

    # Inicializar extensiones
    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Registrar Blueprints
    from .routes import routes as routes_blueprint
    from .auth import auth as auth_blueprint
    app.register_blueprint(routes_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Cargar usuario
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.get_by_id(user_id)

    return app
