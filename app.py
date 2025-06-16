from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import os

# Primero debes definir app
app = Flask(__name__)

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

@app.route('/generar-doc', methods=['POST'])
def generar_doc():
    try:
        data = request.json
        print("Recibido:", data)

        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")
        contexto = {
            "fecha": data.get("fecha", ""),
            "titulo": data.get("titulo", ""),
            "nombres_estudiantes": data.get("nombres_estudiantes", ""),
            "nombre_director": data.get("nombre_director", "")
        }


        print("Contexto:", contexto)

        doc.render(contexto)
        output_path = "solicitud_generada.docx"
        doc.save(output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("ERROR AL GENERAR:", str(e))
        return f"Error interno del servidor: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
