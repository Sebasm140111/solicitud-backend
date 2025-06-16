from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import cloudconvert
import requests
import os
import requests

app = Flask(__name__)
cloudconvert.configure(api_key='eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiOThiYzBhYjg4ODkwZWI5ODczZDNjYzcwNjU3NjgwYjlkZjc4MjlhY2Y2NWYzMGNiZjI5OGY2NzQyYTUyYzA0Nzg1ZjE2MDI1MDVlNTRiNmEiLCJpYXQiOjE3NTAxMTI5NzAuOTE5OTM0LCJuYmYiOjE3NTAxMTI5NzAuOTE5OTM1LCJleHAiOjQ5MDU3ODY1NzAuOTE0NjA4LCJzdWIiOiI3MjIyMjEwNiIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ1c2VyLndyaXRlIiwidGFzay5yZWFkIiwidGFzay53cml0ZSIsIndlYmhvb2sucmVhZCIsIndlYmhvb2sud3JpdGUiLCJwcmVzZXQucmVhZCIsInByZXNldC53cml0ZSJdfQ.Bl91cayJ9svh1O7RPdgV7BeyUrDwBEE0JmwJeebZT-ecR1QPqHSlW6NiD5OOyJY4S7lthUZNLnKtxPRjsFyHuxV5Zi-pNQZakOEjK4Tm_tbGzr35Tk-crcNWOt48avn0hgCtI13s8U8oBbjLMzu4vW0vMMzZTKCEVa0vJl6DTsB5Vp14SnxxoX2HF5-XBLzT1uu76THXu3QrVxxNjAlSlXH2aH0_BSI0zgEFqzWy3iySLBYVqs9cY5d3tpoYbAGKX0CfGszSK-6YiAJPeTCA1Qm6kjM0I-nwB7XDH4tIbiHNgn4zGk4_yBowm53A3IwCAT-GX03Z25vl0hkBtvuXLPOSROsBXd1q-ds4Wm_-BMX1I411ABDkNxNKJGe9in6sw62R4maXPaGT-NNl7PXDDqfXfAtAuQkXWPQJiuj6onLaNXlks1o6dTQE-dbYfOufQy-4doiBSQL4vfaKfBpRdPCHslclgoogJ5n4e1XAsWgkqAiRHg9xYefqAfrgxTiqWWSV5XsjZQs7ylMK4zku9gQIj1esRdYiVzoXlynSR64due3k9mADVTD3zMYKzfvOgMBtJuOXzvz5mI4QaGVVLWKYpf0ecZ1DGE768WzOxgnki2XXYOLqHliMNJDa7PpW7SXIeYuOEDTAOO7UHHhT5hkCl2NkwJTgLX7KhqHjz04')  # Reemplaza con tu API Key de CloudConvert

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        data = request.json
        print("Datos recibidos:", data)

        # Rellenar el documento .docx con los datos recibidos
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

        # Crear el trabajo en CloudConvert
        job = cloudconvert.Job.create(payload={
            "tasks": {
                'import-1': {
                    "operation": "import/upload"
                },
                'task-1': {
                    "operation": "convert",
                    "input": "import-1",
                    "input_format": "docx",
                    "output_format": "pdf",
                    "engine": "libreoffice"
                },
                'export-1': {
                    "operation": "export/url",
                    "input": "task-1"
                }
            }
        })

        upload_task = job['tasks'][0]
        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        with open(doc_path, 'rb') as f:
            upload_data = upload_params.copy()
            upload_data['file'] = f
            response = requests.post(upload_url, data=upload_data, files={'file': f})
            

        # Esperar a que finalice el trabajo y obtener la URL del PDF
        job = cloudconvert.Job.wait(id=job['id'])
        file_url = job['tasks'][-1]['result']['files'][0]['url']

        # Descargar el archivo PDF generado
        response = requests.get(file_url)
        with open("documento.pdf", "wb") as f:
            f.write(response.content)

        return send_file("documento.pdf", as_attachment=True)

    except Exception as e:
        print("ERROR AL GENERAR PDF:", str(e))
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)