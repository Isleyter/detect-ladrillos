from flask import Flask  # type: ignore
from pymongo import MongoClient  # type: ignore
import torch
import os
from pathlib import Path
import sys

from utils.download_model import download_model # type: ignore

app = Flask(__name__)

# --- Variables de entorno ---
MONGO_URI = os.environ.get("MONGO_URI")
DRIVE_MODEL_ID = os.environ.get("DRIVE_MODEL_ID")

# --- Validar que MONGO_URI y DRIVE_MODEL_ID existan ---
if not MONGO_URI:
    raise EnvironmentError("❌ La variable de entorno MONGO_URI no está definida.")
if not DRIVE_MODEL_ID:
    raise EnvironmentError("❌ La variable de entorno DRIVE_MODEL_ID no está definida.")

# --- Conexión MongoDB ---
client = MongoClient(MONGO_URI)
db = client["mi_basedatos"]

# --- Descargar modelo si no existe ---
model_path = "models/best50e1.pt"
if not os.path.exists(model_path):
    print("Descargando modelo desde Google Drive...")
    download_model(DRIVE_MODEL_ID, model_path)

# --- Cargar modelo YOLOv5 desde carpeta local ---
sys.path.append('./yolov5')  # Asegúrate de que esta ruta sea correcta

from models.common import DetectMultiBackend

device = 'cpu'  # Cambia a 'cuda' si Render tiene soporte GPU y lo deseas
model = DetectMultiBackend(model_path, device=device)
model.eval()

# --- Ruta de prueba ---
@app.route("/")
def home():
    return "✅ App Flask corriendo con MongoDB y modelo YOLOv5 cargado localmente."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
