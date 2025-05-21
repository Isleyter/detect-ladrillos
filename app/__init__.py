from flask import Flask
from .extensions import mongo, login_manager, bcrypt
import os
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    if not app.config["MONGO_URI"]:
        raise RuntimeError("MONGO_URI no está definida.")

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "mysecret")

    # --- Inicializar extensiones ---
    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # 👇 IMPORTAR DESPUÉS DE INICIALIZAR EXTENSIONES
    from .auth import auth as auth_blueprint
    from .routes import routes as routes_blueprint  # si lo tienes
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(routes_blueprint)  # si tienes routes.py

    # --- Cargar usuario (debe ir después de mongo.init_app) ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.get_by_id(user_id)

    return app
