from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import cloudconvert
import os
import requests

app = Flask(__name__)
cloudconvert.configure(api_key='TU_API_KEY')  # Reemplaza con tu clave real

@app.route('/')
def home():
    return '✅ API de generación de documentos funcionando correctamente'

def convertir_a_pdf(nombre_docx, nombre_pdf):
    print(f"⏳ Convertir: {nombre_docx} -> {nombre_pdf}")
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
    upload_task = next((t for t in job['tasks'] if t['name'] == 'import-my-file'), None)
    upload_url = upload_task['result']['form']['url']
    upload_params = upload_task['result']['form']['parameters']

    with open(nombre_docx, 'rb') as f:
        requests.post(upload_url, data=upload_params, files={'file': f})

    job = cloudconvert.Job.wait(id=job['id'])
    export_task = next((t for t in job['tasks'] if t['name'] == 'export-my-file'), None)
    file_url = export_task['result']['files'][0]['url']
    response = requests.get(file_url)

    with open(nombre_pdf, "wb") as f:
        f.write(response.content)
    print("✅ Conversión exitosa")

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        if not request.is_json:
            raise Exception("❌ El cuerpo no contiene JSON válido")

        data = request.get_json(force=True)
        print("📥 Datos recibidos:", data)

        required = ["fecha", "titulo", "nombres_estudiantes", "nombre_director"]
        for campo in required:
            if campo not in data or not data[campo]:
                raise Exception(f"❌ Campo faltante o vacío: {campo}")

        contexto = {campo: data[campo] for campo in required}
        print("📦 Contexto para el DOCX:", contexto)

        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")
        doc.render(contexto)
        doc.save("documento.docx")
        print("📝 Documento .docx generado")

        convertir_a_pdf("documento.docx", "documento.pdf")
        return send_file("documento.pdf", as_attachment=True)

    except Exception as e:
        print("❌ ERROR en /generar-pdf:", str(e))
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
