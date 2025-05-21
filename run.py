import sys
import os

# Agrega el path del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolov5'))

from utils.download_model import download_model  # type: ignore
from yolov5.models.common import DetectMultiBackend  # type: ignore
from pathlib import Path

from app import create_app
from app.extensions import mongo

# --- Variables de entorno ---
MONGO_URI = os.environ.get("MONGO_URI")
DRIVE_MODEL_ID = os.environ.get("DRIVE_MODEL_ID")

if not MONGO_URI:
    raise EnvironmentError("❌ La variable de entorno MONGO_URI no está definida.")
if not DRIVE_MODEL_ID:
    raise EnvironmentError("❌ La variable de entorno DRIVE_MODEL_ID no está definida.")

# --- Crear app desde factory ---
app = create_app()

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

# --- Registrar rutas dinámicas ---
from app.routes import configure_routes
configure_routes(app, model, mongo.db)

# --- Ruta simple de prueba ---
@app.route("/ping")
def home():
    return "✅ App Flask corriendo con MongoDB y modelo YOLOv5 cargado localmente."

# --- Ejecutar app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
