from flask_login import UserMixin
from flask import current_app
from app.extensions import bcrypt
from bson.objectid import ObjectId
from datetime import datetime

# -------------------- GET DB DINÁMICO --------------------
def get_db():
    mongo_ext = current_app.extensions.get("pymongo")
    if not mongo_ext:
        raise RuntimeError("❌ Mongo no está inicializado correctamente en Flask.")
    return mongo_ext.db

# -------------------- MODELO USUARIO --------------------
class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.email = data["email"]
        self.password = data["password"]

    @staticmethod
    def get_by_id(user_id):
        data = get_db().users.find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None

    @staticmethod
    def get_by_email(email):
        data = get_db().users.find_one({"email": email})
        return User(data) if data else None

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# -------------------- MODELO MONITOREO --------------------
class Monitoreo:

    @staticmethod
    def guardar(data):
        return get_db().monitoreos.insert_one(data)

    @staticmethod
    def obtener_todos(filtro=None, orden=None):
        query = filtro or {}
        sort = orden or [("fecha", -1)]
        return list(get_db().monitoreos.find(query).sort(sort))

    @staticmethod
    def obtener_paginado(filtro=None, pagina=1, por_pagina=5):
        filtro = filtro or {}
        saltar = (pagina - 1) * por_pagina
        resultados = get_db().monitoreos.find(filtro).sort("fecha", -1).skip(saltar).limit(por_pagina)
        resultados_list = list(resultados)
        for m in resultados_list:
            m["_id"] = str(m["_id"])
        return resultados_list

    @staticmethod
    def eliminar_por_id(monitoreo_id):
        return get_db().monitoreos.delete_one({"_id": ObjectId(monitoreo_id)})

    @staticmethod
    def obtener_por_id(monitoreo_id):
        return get_db().monitoreos.find_one({"_id": ObjectId(monitoreo_id)})
