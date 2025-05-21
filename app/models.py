from flask_login import UserMixin
from app.extensions import mongo, bcrypt
from bson.objectid import ObjectId

# Definir las colecciones globales para evitar repetir mongo.db
users_collection = mongo.db.users
monitoreos_collection = mongo.db.monitoreos

# -------------------- MODELO USUARIO --------------------
class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.email = data["email"]
        self.password = data["password"]

    @staticmethod
    def get_by_id(user_id):
        data = users_collection.find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None

    @staticmethod
    def get_by_email(email):
        data = users_collection.find_one({"email": email})
        return User(data) if data else None

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


# -------------------- MODELO MONITOREO --------------------
class Monitoreo:
    @staticmethod
    def guardar(data):
        return monitoreos_collection.insert_one(data)

    @staticmethod
    def obtener_todos(filtro=None, orden=None):
        query = filtro or {}
        sort = orden or [("fecha", -1)]
        return list(monitoreos_collection.find(query).sort(sort))

    @staticmethod
    def obtener_paginado(filtro=None, pagina=1, por_pagina=5):
        filtro = filtro or {}
        saltar = (pagina - 1) * por_pagina
        resultados = monitoreos_collection.find(filtro).sort("fecha", -1).skip(saltar).limit(por_pagina)

        resultados_list = list(resultados)
        for m in resultados_list:
            m["_id"] = str(m["_id"])  # Para evitar errores de Jinja2 al renderizar

        return resultados_list

    @staticmethod
    def eliminar_por_id(monitoreo_id):
        return monitoreos_collection.delete_one({"_id": ObjectId(monitoreo_id)})

    @staticmethod
    def obtener_por_id(monitoreo_id):
        return monitoreos_collection.find_one({"_id": ObjectId(monitoreo_id)})
