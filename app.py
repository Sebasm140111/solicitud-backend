from flask import Flask, request, send_file
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import cloudconvert
import os
import requests
import json

app = Flask(__name__)
cloudconvert.configure(api_key='TU_API_KEY_AQUI')

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        data = request.json
        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")
        contexto = {
            "fecha": data.get("fecha", ""),
            "titulo": data.get("titulo", ""),
            "nombres_estudiantes": data.get("nombres_estudiantes", ""),
            "nombre_director": data.get("nombre_director", "")
        }
        doc.render(contexto)
        doc_path = "documento.docx"
        doc.save(doc_path)

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

        upload_task = next((task for task in job['tasks'] if task['name'] == 'import-my-file'), None)
        if not upload_task or 'result' not in upload_task:
            raise Exception("No se pudo obtener el formulario de subida")

        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        with open(doc_path, 'rb') as f:
            upload_data = upload_params.copy()
            requests.post(upload_url, data=upload_params, files={'file': f})

        job = cloudconvert.Job.wait(id=job['id'])
        export_task = next((task for task in job['tasks'] if task['name'] == 'export-my-file'), None)
        if not export_task or 'result' not in export_task:
            raise Exception("No se pudo obtener el archivo exportado")

        file_url = export_task['result']['files'][0]['url']
        response = requests.get(file_url)
        with open("documento.pdf", "wb") as f:
            f.write(response.content)

        return send_file("documento.pdf", as_attachment=True)

    except Exception as e:
        print("ERROR AL GENERAR PDF:", str(e))
        return f"Error: {e}", 500

@app.route('/generar-perfil', methods=['POST'])
def generar_perfil():
    try:
        data = request.json
        doc = DocxTemplate("templates/Perfil_Trabajo_Titulacion.docx")

        contexto = data.copy()
        contexto['ods'] = data.get('ods', [])
        contexto['bibliografia'] = data.get('bibliografia', [])

        doc.render(contexto)
        doc_path = "perfil_trabajo.docx"
        doc.save(doc_path)

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

        upload_task = next((task for task in job['tasks'] if task['name'] == 'import-my-file'), None)
        if not upload_task or 'result' not in upload_task:
            raise Exception("No se pudo obtener el formulario de subida")

        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        with open(doc_path, 'rb') as f:
            requests.post(upload_url, data=upload_params, files={'file': f})

        job = cloudconvert.Job.wait(id=job['id'])
        export_task = next((task for task in job['tasks'] if task['name'] == 'export-my-file'), None)
        if not export_task or 'result' not in export_task:
            raise Exception("No se pudo obtener el archivo exportado")

        file_url = export_task['result']['files'][0]['url']
        response = requests.get(file_url)
        with open("perfil_trabajo.pdf", "wb") as f:
            f.write(response.content)

        return send_file("perfil_trabajo.pdf", as_attachment=True)

    except Exception as e:
        print("ERROR AL GENERAR PERFIL:", str(e))
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
