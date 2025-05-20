from flask import Flask, flash, jsonify, Blueprint, render_template, redirect, session, url_for, Response, send_file, request
from flask_login import current_user, login_required
from datetime import date, datetime

from sqlalchemy import func
from .extensions import mongo, bcrypt

from app.camera import VideoCamera, generate_frames
from .models import Monitoreo
from app.utils import generar_pdf, get_monitoring_results
from app.camera import listar_camaras_disponibles
import os

from flask import render_template, request

from app.models import Monitoreo  # Si lo tienes, o lo puedes reemplazar por el modelo Mongo directamente.
from flask_login import login_required
from bson.objectid import ObjectId # type: ignore



routes = Blueprint('routes', __name__)

# Variable global para almacenar la hora de inicio
video_camera = None  # Global inicial
start_time = None

# -- INDEX --
@routes.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.panel'))  # o la página principal para usuarios logueados
    else:
        return render_template('login.html')

# -- PANEL --
from bson.son import SON

@routes.route('/panel')
@login_required
def panel():
    # Agregación de valores desde MongoDB
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


from flask import render_template
from app.utils import listar_camaras_disponibles  # si está en otro archivo

@routes.route('/monitoreo')
def monitoreo():
    global video_camera
    #
    try:
    #    # Obtener lista de cámaras disponibles
        disponibles = listar_camaras_disponibles()
    #    
    #    print(f"[DEBUG] Cámaras disponibles: {disponibles}")
    #    if not disponibles:
    #        flash("No hay cámaras disponibles.", "danger")
    #        return redirect(url_for('routes.panel'))
#
    #    # Convertir a tuplas (índice, nombre) para mostrar en el frontend
        camaras = [(i, f"Cámara {i}") for i in disponibles]
#
        monitoring_active = video_camera is not None and video_camera.running
#
        return render_template('monitoreo.html', camaras=camaras, monitoring_active=monitoring_active)
#
    #except Exception as e:
    #    print(f"[ERROR] Fallo al iniciar monitoreo: {e}")
    #    flash(f"Error al iniciar monitoreo: {e}", "danger")
    #    return redirect(url_for('routes.panel')) 
    #global video_camera
    #try:
    #    monitoring_active = video_camera is not None and video_camera.running
    #    return render_template('monitoreo.html', camaras=[], monitoring_active=monitoring_active)
    except Exception as e:
        print(f"[ERROR] Fallo al iniciar monitoreo: {e}")
        return redirect(url_for('routes.panel'))
    

#-- IICIAR Y FINALIZAR MONITOREO
@routes.route('/iniciar_monitoreo', methods=['POST'])
def iniciar_monitoreo():
    global video_camera
    try:
        selected_camera = int(request.form.get('selected_camera', 0))
    except ValueError:
        return "Error: Índice de cámara inválido", 400
    disponibles = listar_camaras_disponibles()
    print(f"[DEBUG] Cámaras disponibles: {disponibles}")
    print(f"[DEBUG] Cámara seleccionada por el usuario: {selected_camera}")

    if selected_camera not in disponibles:
        return f"Error: La cámara seleccionada ({selected_camera}) no está disponible", 400

    # Reiniciar cámara si es necesario
    if video_camera is None or not video_camera.running or video_camera.camera_index != selected_camera:
        print("[DEBUG] Inicializando cámara seleccionada")
        video_camera = VideoCamera(selected_camera)
        video_camera.start()
    else:
        print("[DEBUG] La cámara ya está corriendo con el índice seleccionado")

    session['hora_inicio'] = datetime.now().time().strftime('%H:%M:%S')
    session['monitoring_active'] = True

    return redirect(url_for('routes.monitoreo'))


#--funct finish monitoring--
from app.models import Monitoreo
from datetime import datetime

@routes.route('/finalizar_monitoreo', methods=['POST'])
@login_required
def finalizar_monitoreo():
    global video_camera

    if not video_camera:
        return 'Error: Cámara no iniciada', 400

    hora_inicio_str = session.get("hora_inicio")
    if not hora_inicio_str:
        return 'Error: Monitoreo no iniciado', 400

    hora_fin = datetime.now()
    hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M:%S').time()
    hora_fin_time = hora_fin.time()

    resultados = video_camera.get_counts()
    precision = float(resultados["precision"])
    tiempo_promedio_fisura = video_camera.obtener_tiempo_promedio_fisura()

    data = {
        "fecha": datetime.now(),
        "hora_inicio": hora_inicio.strftime('%H:%M:%S'),
        "hora_fin": hora_fin_time.strftime('%H:%M:%S'),
        "total_ladrillos": resultados["total"],
        "ladrillos_buenos": resultados["buenos"],
        "ladrillos_malos": resultados["malos"],
        "precision": precision,
        "tiempo_promedio_fisura": tiempo_promedio_fisura,
    }

    Monitoreo.guardar(data)

    # Limpiar sesión y cámara
    video_camera.stop()
    video_camera.release()
    video_camera.reset_counts()
    video_camera = None
    session.pop("hora_inicio", None)

    return redirect(url_for('routes.monitoreo'))


# -- RESULTADOS --
from app.models import Monitoreo

@routes.route('/resultados')
@login_required
def resultados():
    # Obtener los parámetros de la página actual y fecha (si existe)
    page = request.args.get('page', 1, type=int)
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    # Generar el filtro para las fechas (si existen)
    filtro = {}
    if fecha_inicio and fecha_fin:
        filtro["fecha"] = {
            "$gte": fecha_inicio,
            "$lte": fecha_fin
        }
    elif fecha_inicio:
        filtro["fecha"] = {"$gte": fecha_inicio}
    elif fecha_fin:
        filtro["fecha"] = {"$lte": fecha_fin}

    # Paginación
    por_pagina = 5
    saltar = (page - 1) * por_pagina

    # Obtener los resultados paginados desde MongoDB
    monitoreos = list(mongo.db.monitoreos.find(filtro).skip(saltar).limit(por_pagina))

    # Convertir ObjectId a string para evitar error de Jinja
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

# -- PDF DE RESULTADOS --
#from bson.objectid import ObjectId

@routes.route('/descargar_reporte/<monitoreo_id>')
@login_required
def descargar_reporte(monitoreo_id):
    try:
        # Obtener el monitoreo por su ID desde MongoDB
        monitoreo_data = mongo.db.monitoreos.find_one({"_id": ObjectId(monitoreo_id)})
        
        if not monitoreo_data:
            return jsonify({"error": "Monitoreo no encontrado"}), 404
        
        # Generar el PDF usando los datos del monitoreo
        pdf_path = generar_pdf(monitoreo_data)  # Aquí usamos la función que ya tienes para generar el PDF
        if not pdf_path:
            return jsonify({"error": "No se pudo generar el PDF"}), 500
        
        # Verificar si el archivo PDF existe
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        else:
            return jsonify({"error": "Archivo PDF no encontrado"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -- VIDEO FEED --
@routes.route('/video_feed')
@login_required
def video_feed():
    #global video_camera
    #if not video_camera:
    #    return "Cámara no iniciada", 500
    #if not video_camera or not video_camera.running:
    #    return "Cámara no iniciada o no activa", 500
#
    #def gen(camera):
    #    while camera is not None and camera.running:
    #        frame = camera.get_frame()
    #        if frame:
    #            yield (b'--frame\r\n'
    #                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    global video_camera
    if not video_camera:
        return "Cámara no iniciada", 500

    return Response(generate_frames(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

#--------------conteo total monitoreo-----------
from flask import jsonify

@routes.route('/conteo')
def conteo():
    global video_camera
    if video_camera:
        data = video_camera.get_counts()
        return jsonify(data)
    return jsonify({'total': 0, 'buenos': 0, 'malos': 0, 'precision': 0.0})


#-----eliminar registro de monitoreo-------------
@routes.route('/eliminar_monitoreo/<monitoreo_id>', methods=['POST'])
@login_required
def eliminar_monitoreo(monitoreo_id):
    monitoreo = mongo.db.monitoreos.find_one({"_id": ObjectId(monitoreo_id)})

    if not monitoreo:
        return "Monitoreo no encontrado", 404

    # Eliminar PDF si existe
    if monitoreo.get("pdf_path"):
        pdf_path = os.path.join(os.getcwd(), 'app', 'static', monitoreo["pdf_path"])
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    mongo.db.monitoreos.delete_one({"_id": ObjectId(monitoreo_id)})

    return redirect(url_for('routes.resultados'))


#--LISTAR CAMARAS--
@routes.route('/listar_camaras')
def listar_camaras():
    try:
        disponibles = listar_camaras_disponibles()
        camaras = [(i, f"Cámara {i}") for i in disponibles]
        return jsonify(camaras)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def configure_routes(app, model=None, db=None):
    app.register_blueprint(routes)
