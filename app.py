from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import cloudconvert
import os
import requests
import base64

app = Flask(__name__)
cloudconvert.configure(api_key=os.environ.get('CLOUDCONVERT_API_KEY'))

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "Sebasm140111/solicitud-backend"


@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'


def generar_pdf_cloudconvert(nombre_docx, nombre_pdf, contexto):
    try:
        doc = DocxTemplate(nombre_docx)
        doc.render(contexto)
        doc_path = "temp.docx"
        doc.save(doc_path)
        print("📤 Iniciando trabajo en CloudConvert...")

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
                "export-my-file": {"operation": "export/url", "input": "convert-my-file"}
            }
        })

        if 'tasks' not in job or job['tasks'] is None:
            return None, "Error: No se recibieron las tareas de CloudConvert"

        upload_task = next((t for t in job['tasks'] if t['name'] == 'import-my-file'), None)
        if upload_task is None:
            return None, "Error: No se encontró la tarea 'import-my-file' en el job de CloudConvert"

        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        with open(doc_path, 'rb') as f:
            requests.post(upload_url, data=upload_params, files={'file': f})

        job = cloudconvert.Job.wait(id=job['id'])
        job = cloudconvert.Job.find(id=job['id'])  # Asegurarse de tener la versión actualizada del job

        if job['status'] != 'finished':
            return None, f"Error: El trabajo de conversión no finalizó correctamente. Estado: {job['status']}"

        export_task = next((t for t in job['tasks'] if t['name'] == 'export-my-file'), None)
        if not export_task or 'files' not in export_task['result'] or not export_task['result']['files']:
            return None, "Error: No se pudo obtener el archivo exportado"

        file_url = export_task['result']['files'][0]['url']
        response = requests.get(file_url)

        with open(nombre_pdf, "wb") as f:
            f.write(response.content)

        return nombre_pdf, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al generar PDF: {str(e)}"


@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    data = request.json
    contexto = {
        "fecha": data.get("fecha", ""),
        "titulo": data.get("titulo", ""),
        "nombres_estudiantes": data.get("nombres_estudiantes", ""),
        "nombre_director": data.get("nombre_director", "")
    }
    pdf_path, error = generar_pdf_cloudconvert("templates/2_Solicitud_fecha_de_defensa_final.docx", "documento.pdf", contexto)
    if error:
        return error, 500
    return send_file(pdf_path, as_attachment=True)


@app.route('/generar-emprendimiento', methods=['POST'])
def generar_emprendimiento():
    data = request.json
    pdf_path, error = generar_pdf_cloudconvert("templates/Solicitud_TTitulacion_Emprendimiento_IT112b.docx", "emprendimiento.pdf", data)
    if error:
        return error, 500
    return send_file(pdf_path, as_attachment=True)


@app.route('/generar-examen-complexivo', methods=['POST'])
def generar_examen_complexivo():
    data = request.json
    contexto = {
        "fecha": data.get("fecha", ""),
        "nombre_completo_ingeniero": data.get("nombre_completo_ingeniero", ""),
        "carrera": data.get("carrera", ""),
        "codigo": data.get("codigo", ""),
        "nombre_completo_estudiante": data.get("nombre_completo_estudiante", ""),
        "cedula": data.get("cedula", ""),
        "correo_institucional": data.get("correo_institucional", ""),
        "version": data.get("version", "1"),
        "actualizado_si_existe": data.get("actualizado_si_existe", ""),
        "fecha_actualizacion": data.get("fecha_actualizacion", ""),
    }
    pdf_path, error = generar_pdf_cloudconvert("templates/Solicitud_ExamenComplexivoIT112a.docx", "complexivo.pdf", contexto)
    if error:
        return error, 500
    return send_file(pdf_path, as_attachment=True)


@app.route('/subir-docx-github', methods=['POST'])
def subir_docx_github():
    try:
        archivo = request.files['archivo']
        nombre_archivo = request.form.get("nombre_archivo")

        if not nombre_archivo:
            return {"error": "Debes enviar el nombre del archivo"}, 400

        contenido_binario = archivo.read()
        contenido_base64 = base64.b64encode(contenido_binario).decode('utf-8')
        ruta_completa = f"templates/{nombre_archivo}"

        # Obtener SHA actual del archivo
        sha_res = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ruta_completa}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )

        sha = sha_res.json().get("sha") if sha_res.status_code == 200 else None

        # Subir el nuevo archivo
        response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ruta_completa}",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            },
            json={
                "message": f"Actualización de plantilla {nombre_archivo}",
                "content": contenido_base64,
                "sha": sha
            }
        )

        if response.status_code in [200, 201]:
            return {"mensaje": f"✅ Archivo {nombre_archivo} actualizado correctamente en GitHub"}
        else:
            return {
                "error": "❌ Error al subir",
                "status_code": response.status_code,
                "respuesta": response.json()
            }, 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
