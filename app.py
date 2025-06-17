from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import cloudconvert
import os
import requests

app = Flask(__name__)
cloudconvert.configure(api_key='eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiOThiYzBhYjg4ODkwZWI5ODczZDNjYzcwNjU3NjgwYjlkZjc4MjlhY2Y2NWYzMGNiZjI5OGY2NzQyYTUyYzA0Nzg1ZjE2MDI1MDVlNTRiNmEiLCJpYXQiOjE3NTAxMTI5NzAuOTE5OTM0LCJuYmYiOjE3NTAxMTI5NzAuOTE5OTM1LCJleHAiOjQ5MDU3ODY1NzAuOTE0NjA4LCJzdWIiOiI3MjIyMjEwNiIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ1c2VyLndyaXRlIiwidGFzay5yZWFkIiwidGFzay53cml0ZSIsIndlYmhvb2sucmVhZCIsIndlYmhvb2sud3JpdGUiLCJwcmVzZXQucmVhZCIsInByZXNldC53cml0ZSJdfQ.Bl91cayJ9svh1O7RPdgV7BeyUrDwBEE0JmwJeebZT-ecR1QPqHSlW6NiD5OOyJY4S7lthUZNLnKtxPRjsFyHuxV5Zi-pNQZakOEjK4Tm_tbGzr35Tk-crcNWOt48avn0hgCtI13s8U8oBbjLMzu4vW0vMMzZTKCEVa0vJl6DTsB5Vp14SnxxoX2HF5-XBLzT1uu76THXu3QrVxxNjAlSlXH2aH0_BSI0zgEFqzWy3iySLBYVqs9cY5d3tpoYbAGKX0CfGszSK-6YiAJPeTCA1Qm6kjM0I-nwB7XDH4tIbiHNgn4zGk4_yBowm53A3IwCAT-GX03Z25vl0hkBtvuXLPOSROsBXd1q-ds4Wm_-BMX1I411ABDkNxNKJGe9in6sw62R4maXPaGT-NNl7PXDDqfXfAtAuQkXWPQJiuj6onLaNXlks1o6dTQE-dbYfOufQy-4doiBSQL4vfaKfBpRdPCHslclgoogJ5n4e1XAsWgkqAiRHg9xYefqAfrgxTiqWWSV5XsjZQs7ylMK4zku9gQIj1esRdYiVzoXlynSR64due3k9mADVTD3zMYKzfvOgMBtJuOXzvz5mI4QaGVVLWKYpf0ecZ1DGE768WzOxgnki2XXYOLqHliMNJDa7PpW7SXIeYuOEDTAOO7UHHhT5hkCl2NkwJTgLX7KhqHjz04')  # Reemplaza con tu clave real

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
