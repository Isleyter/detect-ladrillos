from flask_login import LoginManager
from flask_bcrypt import Bcrypt  # type: ignore
from flask_migrate import Migrate  # type: ignore
from flask_pymongo import PyMongo  # type: ignore

login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
mongo = PyMongo()  # MongoDB
