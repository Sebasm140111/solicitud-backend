from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'API lista para generar .docx'

@app.route('/generar-docx', methods=['POST'])
def generar_docx():
    try:
        data = request.get_json()
        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")

        contexto = {
            "fecha": data.get("fecha", ""),
            "titulo": data.get("titulo", ""),
            "nombres_estudiantes": data.get("nombres_estudiantes", ""),
            "nombre_director": data.get("nombre_director", "")
        }

        output_path = "documento_generado.docx"
        doc.render(contexto)
        doc.save(output_path)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
