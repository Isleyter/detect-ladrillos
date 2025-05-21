from flask import (
    Blueprint, render_template, redirect, session,
    url_for, Response, send_file, request, jsonify, current_app
)
from flask_login import current_user, login_required
from datetime import datetime
from bson.objectid import ObjectId
from .extensions import mongo
from app.camera import VideoCamera, generate_frames, listar_camaras_disponibles
from app.utils import generar_pdf
from app.models import Monitoreo
import os

routes = Blueprint('routes', __name__)
video_camera = None  # Cámara global


# ===================== INDEX =====================
@routes.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.panel'))
    return render_template('login.html')


# ===================== PANEL =====================
@routes.route('/panel')
@login_required
def panel():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_ladrillos": {"$sum": "$total_ladrillos"},
                "ladrillos_buenos": {"$sum": "$ladrillos_buenos"},
                "ladrillos_malos": {"$sum": "$ladrillos_malos"},
                "precision_promedio": {"$avg": "$precision"},
                "tiempo_promedio_fisura": {"$avg": "$tiempo_promedio_fisura"}
            }
        }
    ]
    resultados = list(mongo.db.monitoreos.aggregate(pipeline))
    resumen = resultados[0] if resultados else {}

    return render_template('panel.html',
        total_ladrillos=resumen.get("total_ladrillos", 0),
        total_buenos=resumen.get("ladrillos_buenos", 0),
        total_malos=resumen.get("ladrillos_malos", 0),
        precision_promedio=round(resumen.get("precision_promedio", 0.0), 2),
        tiempo_promedio_fisura=round(resumen.get("tiempo_promedio_fisura", 0.0), 2)
    )


# ===================== MONITOREO =====================
@routes.route('/monitoreo')
def monitoreo():
    global video_camera
    try:
        disponibles = listar_camaras_disponibles()
        camaras = [(i, f"Cámara {i}") for i in disponibles]
        monitoring_active = video_camera is not None and video_camera.running
        return render_template('monitoreo.html', camaras=camaras, monitoring_active=monitoring_active)
    except Exception as e:
        print(f"[ERROR] Fallo al iniciar monitoreo: {e}")
        return redirect(url_for('routes.panel'))


# ===================== INICIAR MONITOREO =====================
@routes.route('/iniciar_monitoreo', methods=['POST'])
def iniciar_monitoreo():
    global video_camera
    try:
        selected_camera = int(request.form.get('selected_camera', 0))
    except ValueError:
        return "Error: Índice de cámara inválido", 400

    disponibles = listar_camaras_disponibles()
    if selected_camera not in disponibles:
        return f"Error: La cámara seleccionada ({selected_camera}) no está disponible", 400

    if video_camera is None or not video_camera.running or video_camera.camera_index != selected_camera:
        video_camera = VideoCamera(selected_camera)
        video_camera.start()

    session['hora_inicio'] = datetime.now().time().strftime('%H:%M:%S')
    session['monitoring_active'] = True
    return redirect(url_for('routes.monitoreo'))


# ===================== FINALIZAR MONITOREO =====================
@routes.route('/finalizar_monitoreo', methods=['POST'])
@login_required
def finalizar_monitoreo():
    global video_camera
    if not video_camera:
        return 'Error: Cámara no iniciada', 400

    hora_inicio_str = session.get("hora_inicio")
    if not hora_inicio_str:
        return 'Error: Monitoreo no iniciado', 400

    hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M:%S').time()
    hora_fin = datetime.now().time()

    resultados = video_camera.get_counts()
    precision = float(resultados["precision"])
    tiempo_promedio_fisura = video_camera.obtener_tiempo_promedio_fisura()

    data = {
        "fecha": datetime.now(),
        "hora_inicio": hora_inicio.strftime('%H:%M:%S'),
        "hora_fin": hora_fin.strftime('%H:%M:%S'),
        "total_ladrillos": resultados["total"],
        "ladrillos_buenos": resultados["buenos"],
        "ladrillos_malos": resultados["malos"],
        "precision": precision,
        "tiempo_promedio_fisura": tiempo_promedio_fisura,
    }

    Monitoreo.guardar(data)

    video_camera.stop()
    video_camera.release()
    video_camera.reset_counts()
    video_camera = None
    session.pop("hora_inicio", None)

    return redirect(url_for('routes.monitoreo'))


# ===================== RESULTADOS =====================
@routes.route('/resultados')
@login_required
def resultados():
    page = request.args.get('page', 1, type=int)
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    filtro = {}
    if fecha_inicio and fecha_fin:
        filtro["fecha"] = {"$gte": fecha_inicio, "$lte": fecha_fin}
    elif fecha_inicio:
        filtro["fecha"] = {"$gte": fecha_inicio}
    elif fecha_fin:
        filtro["fecha"] = {"$lte": fecha_fin}

    por_pagina = 5
    saltar = (page - 1) * por_pagina

    monitoreos = list(mongo.db.monitoreos.find(filtro).skip(saltar).limit(por_pagina))
    for m in monitoreos:
        m["_id"] = str(m["_id"])

    total_monitoreos = mongo.db.monitoreos.count_documents(filtro)
    total_paginas = (total_monitoreos // por_pagina) + (1 if total_monitoreos % por_pagina > 0 else 0)

    return render_template("resultados.html",
                           monitoreos=monitoreos,
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           page=page,
                           total_paginas=total_paginas)


# ===================== DESCARGAR PDF =====================
@routes.route('/descargar_reporte/<monitoreo_id>')
@login_required
def descargar_reporte(monitoreo_id):
    try:
        monitoreo_data = mongo.db.monitoreos.find_one({"_id": ObjectId(monitoreo_id)})
        if not monitoreo_data:
            return jsonify({"error": "Monitoreo no encontrado"}), 404

        pdf_path = generar_pdf(monitoreo_data)
        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify({"error": "PDF no disponible"}), 500

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================== VIDEO STREAM =====================
@routes.route('/video_feed')
@login_required
def video_feed():
    global video_camera
    if not video_camera:
        return "Cámara no iniciada", 500
    return Response(generate_frames(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')


# ===================== CONTEO EN VIVO =====================
@routes.route('/conteo')
def conteo():
    global video_camera
    if video_camera:
        data = video_camera.get_counts()
        return jsonify(data)
    return jsonify({'total': 0, 'buenos': 0, 'malos': 0, 'precision': 0.0})


# ===================== ELIMINAR MONITOREO =====================
@routes.route('/eliminar_monitoreo/<monitoreo_id>', methods=['POST'])
@login_required
def eliminar_monitoreo(monitoreo_id):
    monitoreo = mongo.db.monitoreos.find_one({"_id": ObjectId(monitoreo_id)})
    if not monitoreo:
        return "Monitoreo no encontrado", 404

    if monitoreo.get("pdf_path"):
        pdf_path = os.path.join(os.getcwd(), 'app', 'static', monitoreo["pdf_path"])
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    mongo.db.monitoreos.delete_one({"_id": ObjectId(monitoreo_id)})
    return redirect(url_for('routes.resultados'))


# ===================== LISTAR CÁMARAS =====================
@routes.route('/listar_camaras')
def listar_camaras():
    try:
        disponibles = listar_camaras_disponibles()
        camaras = [(i, f"Cámara {i}") for i in disponibles]
        return jsonify(camaras)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
