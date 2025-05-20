import os
import gdown  # type: ignore

def download_model(file_id, destination):
    print("📥 Descargando modelo desde Google Drive...")

    # Validar ID
    if not file_id or not isinstance(file_id, str) or len(file_id) < 10:
        raise ValueError("❌ El ID del archivo de Google Drive no es válido.")

    # Crear carpeta de destino
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    # Construir URL de descarga directa
    url = f"https://drive.google.com/uc?id={file_id}"

    try:
        gdown.download(url, destination, quiet=False)

        # Validar tamaño mínimo del archivo descargado
        if os.path.getsize(destination) < 10_000:
            print("⚠️ Descarga fallida o archivo demasiado pequeño.")
            os.remove(destination)
            raise RuntimeError("❌ El modelo no se descargó correctamente o está corrupto.")
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")
        raise

    print("✅ Descarga completada correctamente.")
