from flask_login import UserMixin
from flask import current_app
from app.extensions import bcrypt
from bson.objectid import ObjectId
from datetime import datetime

# -------------------- MODELO USUARIO --------------------
class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.email = data["email"]
        self.password = data["password"]

    @staticmethod
    def get_by_id(user_id):
        mongo = current_app.extensions["pymongo"]
        data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None

    @staticmethod
    def get_by_email(email):
        mongo = current_app.extensions["pymongo"]
        data = mongo.db.users.find_one({"email": email})
        return User(data) if data else None

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# -------------------- MODELO MONITOREO --------------------
class Monitoreo:

    @staticmethod
    def guardar(data):
        mongo = current_app.extensions["pymongo"]
        return mongo.db.monitoreos.insert_one(data)

    @staticmethod
    def obtener_todos(filtro=None, orden=None):
        mongo = current_app.extensions["pymongo"]
        query = filtro or {}
        sort = orden or [("fecha", -1)]
        return list(mongo.db.monitoreos.find(query).sort(sort))

    @staticmethod
    def obtener_paginado(filtro=None, pagina=1, por_pagina=5):
        mongo = current_app.extensions["pymongo"]
        filtro = filtro or {}
        saltar = (pagina - 1) * por_pagina
        resultados = mongo.db.monitoreos.find(filtro).sort("fecha", -1).skip(saltar).limit(por_pagina)

        resultados_list = list(resultados)
        for m in resultados_list:
            m["_id"] = str(m["_id"])  # Para evitar errores de Jinja2 al renderizar

        return resultados_list

    @staticmethod
    def eliminar_por_id(monitoreo_id):
        mongo = current_app.extensions["pymongo"]
        return mongo.db.monitoreos.delete_one({"_id": ObjectId(monitoreo_id)})

    @staticmethod
    def obtener_por_id(monitoreo_id):
        mongo = current_app.extensions["pymongo"]
        return mongo.db.monitoreos.find_one({"_id": ObjectId(monitoreo_id)})
