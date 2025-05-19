import os

# Crear carpeta "reportes" si no existe
REPORT_DIR = os.path.join(os.getcwd(), 'reportes')
os.makedirs(REPORT_DIR, exist_ok=True)



def get_monitoring_results():
    # Lógica para calcular métricas
    return {
        "total": 100,
        "buenos": 85,
        "malos": 15,
        "precision": 85.0,
        "promedio_tiempo": "0.2s"
    }


#--2-------monitoreo--------------

from fpdf import FPDF # type: ignore
import os

def generar_pdf(monitoreo_data):
    # Generar el nombre del archivo PDF basado en la fecha y el ID
    file_name = f"monitoreo_{str(monitoreo_data['_id'])}.pdf"
    pdf_path = os.path.join(os.getcwd(), 'app', 'static', 'reportes', file_name)

    # Verificar que el directorio exista, si no, crearlo
    if not os.path.exists(os.path.dirname(pdf_path)):
        os.makedirs(os.path.dirname(pdf_path))

    # Crear el documento PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Establecer la fuente
    pdf.set_font('Arial', 'B', 16)

    # Título del documento
    pdf.cell(200, 10, txt=f"Reporte de Monitoreo", ln=True, align="C")

    # Agregar la fecha de creación del monitoreo
    pdf.ln(10)
    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, txt=f"Fecha: {monitoreo_data['fecha']}", ln=True)
    pdf.cell(200, 10, txt=f"Hora Inicio: {monitoreo_data['hora_inicio']}", ln=True)
    pdf.cell(200, 10, txt=f"Hora Fin: {monitoreo_data['hora_fin']}", ln=True)
    pdf.cell(200, 10, txt=f"Total de Ladrillos: {monitoreo_data['total_ladrillos']}", ln=True)
    pdf.cell(200, 10, txt=f"Ladrillos Buenos: {monitoreo_data['ladrillos_buenos']}", ln=True)
    pdf.cell(200, 10, txt=f"Ladrillos Malos: {monitoreo_data['ladrillos_malos']}", ln=True)
    pdf.cell(200, 10, txt=f"Precisión: {monitoreo_data['precision']}%", ln=True)
    pdf.cell(200, 10, txt=f"Tiempo Promedio Fisura: {monitoreo_data['tiempo_promedio_fisura']} segundos", ln=True)

    # Guardar el archivo PDF
    pdf.output(pdf_path)

    return pdf_path


import cv2

def listar_camaras_disponibles(max_dispositivos=5):
    camaras_disponibles = []
    for i in range(max_dispositivos):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            camaras_disponibles.append(i)
        cap.release()
    return camaras_disponibles


