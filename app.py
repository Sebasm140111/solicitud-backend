from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import cloudconvert
import os
import requests

app = Flask(__name__)
cloudconvert.configure(api_key='TU_API_KEY')  # Reemplaza con tu API Key real

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

def convertir_a_pdf(nombre_docx, nombre_pdf):
    job = cloudconvert.Job.create(payload={
        "tasks": {
            "import-my-file": {"operation": "import/upload"},
            "convert-my-file": {
                "operation": "convert",
                "input": "import-my-file",
                "input_format": "docx",
                "output_format": "pdf",
                "engine": "libreoffice"
            },
            "export-my-file": {
                "operation": "export/url",
                "input": "convert-my-file"
            }
        }
    })

    job = job.get('data') if isinstance(job, dict) else job
    if 'tasks' not in job:
        raise Exception("Respuesta inesperada de CloudConvert")

    upload_task = next((task for task in job['tasks'] if task['name'] == 'import-my-file'), None)
    if not upload_task or 'result' not in upload_task:
        raise Exception("No se pudo obtener el formulario de subida")

    upload_url = upload_task['result']['form']['url']
    upload_params = upload_task['result']['form']['parameters']

    with open(nombre_docx, 'rb') as f:
        requests.post(upload_url, data=upload_params, files={'file': f})

    job = cloudconvert.Job.wait(id=job['id'])

    export_task = next((task for task in job['tasks'] if task['name'] == 'export-my-file'), None)
    if not export_task or 'result' not in export_task:
        raise Exception("No se pudo obtener el archivo exportado")

    file_url = export_task['result']['files'][0]['url']
    response = requests.get(file_url)
    with open(nombre_pdf, "wb") as f:
        f.write(response.content)

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        if not request.is_json:
            raise Exception("❌ La solicitud no contiene JSON válido")

        data = request.get_json(force=True)
        if not isinstance(data, dict):
            raise Exception("❌ El cuerpo JSON no es un diccionario válido")

        print("✅ JSON recibido en /generar-pdf:", data)

        required_fields = ["fecha", "titulo", "nombres_estudiantes", "nombre_director"]
        for campo in required_fields:
            if campo not in data or not isinstance(data[campo], str):
                raise Exception(f"❌ Falta o es inválido el campo: {campo}")

        contexto = {k: data[k] for k in required_fields}
        print("📦 Contexto:", contexto)

        doc = DocxTemplate("templates/test_formato_simple.docx")
        doc.render(contexto)
        doc.save("documento.docx")

        convertir_a_pdf("documento.docx", "documento.pdf")
        return send_file("documento.pdf", as_attachment=True)

    except Exception as e:
        print("❌ ERROR:", str(e))
        return f"Error: {e}", 500


@app.route('/generar-perfil', methods=['POST'])
def generar_perfil():
    try:
        data = request.get_json()
        print("📥 Datos recibidos:", data)

        contexto = {
            "facultad": data.get("facultad", ""),
            "carrera": data.get("carrera", ""),
            "periodo_academico": data.get("periodo_academico", ""),
            "apellidos": data.get("apellidos", ""),
            "nombres": data.get("nombres", ""),
            "codigo_estudiante": data.get("codigo_estudiante", ""),
            "cedula": data.get("cedula", ""),
            "correo_electronico_institu": data.get("correo_electronico_institu", ""),
            "apellidos_director": data.get("apellidos_director", ""),
            "nombres_director": data.get("nombres_director", ""),
            "cedula_director": data.get("cedula_director", ""),
            "correo_director_institu": data.get("correo_director_institu", ""),
            "opción_del_trabajo_de_titulacion": data.get("opcion", ""),
            "modalidad": data.get("modalidad", ""),
            "tema": data.get("tema", ""),
            "objetivo_general": data.get("objetivo_general", ""),
            "linea_de_investigacion": data.get("linea_de_investigacion", ""),
            "programa": data.get("programa", ""),
            "ods": data.get("ods", []),  # lista de enteros
            "problema": data.get("problema", ""),
            "metodo_de_metodologia": data.get("metodo_de_metodologia", ""),
            "tecnica": data.get("tecnica", ""),
            "instrumentos": data.get("instrumentos", ""),
            "bibliografia": data.get("bibliografia", []),  # lista de strings
            "firma_estudiante": data.get("firma_estudiante", ""),
            "firma_director": data.get("firma_director", "")
        }

        print("📦 Contexto generado:", contexto)

        doc = DocxTemplate("templates/Perfil_Trabajo_Titulacion.docx")
        doc.render(contexto)
        doc_path = "perfil_trabajo.docx"
        pdf_path = "perfil_trabajo.pdf"
        doc.save(doc_path)

        convertir_a_pdf(doc_path, pdf_path)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print("❌ ERROR AL GENERAR PERFIL:", str(e))
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)