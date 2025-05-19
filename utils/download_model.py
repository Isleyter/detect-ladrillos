import os
import gdown # type: ignore

def download_model(file_id, destination):
    print("Descargando modelo desde Google Drive...")

    # Crea la carpeta si no existe
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    # Construye la URL de descarga directa
    url = f"https://drive.google.com/uc?id={file_id}"

    try:
        gdown.download(url, destination, quiet=False)

        # Verifica si el archivo es válido
        if os.path.getsize(destination) < 10_000:
            print("⚠️ Descarga fallida o archivo incorrecto (archivo demasiado pequeño).")
            os.remove(destination)
            raise Exception("El modelo no se descargó correctamente.")
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")
        raise

    print("✅ Descarga completada.")
