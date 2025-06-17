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
        data = request.json
        print("==========================")
        print(">> Datos recibidos en /generar-pdf:", data)

        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")
        contexto = {
            "fecha": data.get("fecha", ""),
            "titulo": data.get("titulo", ""),
            "nombres_estudiantes": data.get("nombres_estudiantes", ""),
            "nombre_director": data.get("nombre_director", "")
        }
        print(">> Contexto generado:", contexto)

        doc.render(contexto)
        doc_path = "documento.docx"
        pdf_path = "documento.pdf"
        doc.save(doc_path)

        convertir_a_pdf(doc_path, pdf_path)
        print("✅ PDF generado correctamente")
        print("==========================")
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print("❌ ERROR AL GENERAR PDF:", str(e))
        return f"Error: {e}", 500

@app.route('/generar-perfil', methods=['POST'])
def generar_perfil():
    try:
        data = request.json
        print("==========================")
        print(">> Datos recibidos en /generar-perfil:", data)

        doc = DocxTemplate("templates/Perfil_Trabajo_Titulacion.docx")
        contexto = data.copy()
        contexto['ods'] = data.get('ods') or []
        contexto['bibliografia'] = data.get('bibliografia') or []
        print(">> Contexto generado:", contexto)

        doc.render(contexto)
        doc_path = "perfil_trabajo.docx"
        pdf_path = "perfil_trabajo.pdf"
        doc.save(doc_path)

        convertir_a_pdf(doc_path, pdf_path)
        print("✅ PDF generado correctamente")
        print("==========================")
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print("❌ ERROR AL GENERAR PERFIL:", str(e))
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
