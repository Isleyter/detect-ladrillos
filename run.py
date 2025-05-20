import sys
import os

# Agrega el path al directorio actual y a la carpeta yolov5 antes de cualquier import relacionado
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolov5'))

from download_model import download_model  # type: ignore # IMPORTACIÓN CORRECTA
from yolov5.models.common import DetectMultiBackend      # IMPORTACIÓN CORRECTA

from flask import Flask  # type: ignore
from pymongo import MongoClient  # type: ignore
import torch
from pathlib import Path



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
os.makedirs("models", exist_ok=True)
if not os.path.exists(model_path):
    print("📥 Descargando modelo desde Google Drive...")
    download_model(DRIVE_MODEL_ID, model_path)

# --- Cargar modelo YOLOv5 localmente ---
device = 'cpu'  # Cambiar a 'cuda' si Render tiene GPU
model = DetectMultiBackend(model_path, device=device, dnn=False)
model.eval()

# --- Ruta simple de prueba ---
@app.route("/")
def home():
    return "✅ App Flask corriendo con MongoDB y modelo YOLOv5 cargado localmente."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
