from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

@app.route('/generar-doc', methods=['POST'])
def generar_doc():
    data = request.json
    doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")

    contexto = {
        "fecha": data.get("fecha", ""),
        "TITULO DEL TRABAJO DE TITULACION": data.get("titulo", ""),
        "NOMBRE/S DE ESTUDIANTE/S": data.get("nombres_estudiantes", ""),
        "nombres completos director": data.get("nombre_director", "")
    }

    doc.render(contexto)
    output_path = "solicitud_generada.docx"
    doc.save(output_path)

    return send_file(output_path, as_attachment=True)
