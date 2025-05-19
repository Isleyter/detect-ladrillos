import cv2  # type: ignore
import torch  # type: ignore
from pathlib import Path
import sys
from datetime import datetime
from fpdf import FPDF  # type: ignore
import os
import threading
import time



class VideoCamera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.video = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.video.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara con índice {camera_index}")
       
        self.running = False
        self.frame = None
        self.lock = threading.Lock()

        self.total_counts = {'fisura': 0, 'rotura': 0, 'bueno': 0}
        self.tiempos_fisura = []
        self.start_time = datetime.now()
        self.end_time = None

        # ----- sys.modules['pathlib'].PosixPath = Path -------
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path='./models/best50e1.pt')
        self.model.conf = 0.5
        self.model.iou = 0.45
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)

    def start(self):
        if self.video is None or not self.video.isOpened():
            print(f"[DEBUG] Reintentando abrir cámara en índice {self.camera_index}")
            self.video = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.video.isOpened():
                raise RuntimeError(f"No se pudo abrir la cámara con índice {self.camera_index}")
        self.running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        print(f"[DEBUG] Monitoreo iniciado con cámara {self.camera_index}")

    def _capture_loop(self):
        while self.running:
            success, frame = self.video.read()
            if not success or frame is None:
                continue

            self.counts = {'fisura': 0, 'rotura': 0, 'bueno': 0}
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.model(img, size=416)
            detections = results.xyxy[0]

            ret, jpeg = cv2.imencode('.jpg', frame)

            for *box, conf, cls in detections:
                label = self.model.names[int(cls)]
                if label in self.counts:
                    self.counts[label] += 1
                    self.total_counts[label] += 1
                    if label == 'fisura':
                        duracion = (datetime.now() - self.start_time).total_seconds()
                        self.tiempos_fisura.append(duracion)

                x1, y1, x2, y2 = map(int, box)
                color = (0, 255, 0) if label == 'bueno' else (0, 0, 255)
                text = f"{label} {float(conf):.1f}%"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            conteo_texto = f"Fisuras: {self.counts['fisura']}  Roturas: {self.counts['rotura']}  Buenos: {self.counts['bueno']}"
            cv2.putText(frame, conteo_texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.lock:
                    self.frame = jpeg.tobytes()

            time.sleep(0.03)  # para evitar sobrecarga: ~30 FPS

    def stop(self):
        self.running = False
        if self.video is not None:
            self.video.release()

    def get_frame(self):
        with self.lock:
            return self.frame

    def get_counts(self):
        total = sum(self.total_counts.values())
        buenos = self.total_counts['bueno']
        malos = self.total_counts['fisura'] + self.total_counts['rotura']
        precision = self.get_precision()
        return {
            "total": total,
            "buenos": buenos,
            "malos": malos,
            "precision": precision
        }

    def get_precision(self):
        total_detectados = sum(self.total_counts.values())
        if total_detectados == 0:
            return 0.0
        defectuosos = self.total_counts['fisura'] + self.total_counts['rotura']
        return round((defectuosos / total_detectados) * 100, 2)

    def reset_counts(self):
        self.total_counts = {'fisura': 0, 'rotura': 0, 'bueno': 0}
        self.tiempos_fisura = []
        self.start_time = datetime.now()
        self.end_time = None

    def release(self):
        if self.video.isOpened():
            self.video.release()
        self.end_time = datetime.now()
        try:
            self.save_results()
        except Exception as e:
            print(f"[Error al guardar resultados]: {e}")

    def obtener_tiempo_promedio_fisura(self):
        if not self.tiempos_fisura:
            return 0.0
        return round(sum(self.tiempos_fisura) / len(self.tiempos_fisura), 2)

    def save_results(self):
        total = sum(self.total_counts.values())
        malos = self.total_counts['fisura'] + self.total_counts['rotura']
        buenos = self.total_counts['bueno']
        precision = (self.total_counts['fisura'] / (malos + buenos)) * 100 if malos + buenos > 0 else 0

        tiempo_promedio_fisura = self.obtener_tiempo_promedio_fisura()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Reporte de Monitoreo", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Inicio: {self.start_time}", ln=True)
        pdf.cell(200, 10, txt=f"Fin: {self.end_time}", ln=True)
        pdf.cell(200, 10, txt=f"Total ladrillos: {total}", ln=True)
        pdf.cell(200, 10, txt=f"Buenos: {buenos}", ln=True)
        pdf.cell(200, 10, txt=f"Malos: {malos}", ln=True)
        pdf.cell(200, 10, txt=f"Precisión de fisura: {precision:.2f}%", ln=True)
        pdf.cell(200, 10, txt=f"Tiempo promedio de detección de fisura: {tiempo_promedio_fisura:.2f} seg", ln=True)

        os.makedirs("reportes", exist_ok=True)
        filename = f"reporte_{self.start_time.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(f"reportes/{filename}")


# ------------Funciones auxiliares------------
def generate_frames(video_camera):
    while True:
        if not video_camera.running:
            break

        frame = video_camera.get_frame()
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        #time.sleep(0.1)  # Limita la frecuencia a ~10 fps (ajustable)

def listar_camaras_disponibles(max_camaras=5):
    disponibles = []
    for index in range(max_camaras):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap is not None and cap.isOpened():
            print(f"[DEBUG] Cámara encontrada en índice {index}")
            disponibles.append(index)
            cap.release()
        else:
            print(f"[DEBUG] No se encontró cámara en índice {index}")
    return disponibles
