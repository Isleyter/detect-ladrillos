from flask import Flask # type: ignore
from pymongo import MongoClient # type: ignore
import torch
import os
import torch
from pathlib import Path

from utils.download_model import download_model

app = Flask(__name__)

# --- Variables de entorno ---
MONGO_URI = os.environ.get("MONGO_URI")
DRIVE_MODEL_ID = os.environ.get("174Td9kRd10iImunxIwrXZsKn9PduBDTX")

# --- Conexión MongoDB ---
client = MongoClient(MONGO_URI)
db = client["mi_basedatos"]

# --- Descargar modelo si no existe ---
model_path = "models/best50e1.pt"
if not os.path.exists(model_path):
    print("Descargando modelo desde Google Drive...")
    download_model(DRIVE_MODEL_ID, model_path)

# --- Cargar modelo YOLOv5 ---
model = torch.load(model_path, map_location=torch.device("cpu"))
model.eval()

# --- Ruta de prueba ---
@app.route("/")
def home():
    return "App Flask corriendo con MongoDB y modelo YOLOv5."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
