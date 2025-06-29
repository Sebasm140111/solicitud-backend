from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import os
import requests
import base64

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "Sebasm140111/solicitud-backend"
PDFCO_API_KEY = os.environ.get("PDFCO_API_KEY")

@app.route('/')
def home():
    return 'API de generación de solicitud funcionando'

def generar_pdf_pdfco(nombre_docx, nombre_pdf, contexto):
    try:
        doc = DocxTemplate(nombre_docx)
        doc.render(contexto)
        doc_path = "temp.docx"
        doc.save(doc_path)

        with open(doc_path, "rb") as file:
            encoded_file = base64.b64encode(file.read()).decode()

        response = requests.post(
            "https://api.pdf.co/v1/pdf/convert/from/url",
            headers={"x-api-key": PDFCO_API_KEY},
            json={"url": f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{doc_path}", "name": nombre_pdf}
        )

        if response.status_code != 200:
            return None, f"Error al generar PDF: {response.text}"

        result_url = response.json().get("url")
        pdf_response = requests.get(result_url)

        with open(nombre_pdf, "wb") as f:
            f.write(pdf_response.content)

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
    pdf_path, error = generar_pdf_pdfco("templates/2_Solicitud_fecha_de_defensa_final.docx", "documento.pdf", contexto)
    if error:
        return error, 500
    return send_file(pdf_path, as_attachment=True)

@app.route('/generar-emprendimiento', methods=['POST'])
def generar_emprendimiento():
    data = request.json
    pdf_path, error = generar_pdf_pdfco("templates/Solicitud_TTitulacion_Emprendimiento_IT112b.docx", "emprendimiento.pdf", data)
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
    pdf_path, error = generar_pdf_pdfco("templates/Solicitud_ExamenComplexivoIT112a.docx", "complexivo.pdf", contexto)
    if error:
        return error, 500
    return send_file(pdf_path, as_attachment=True)

@app.route('/generar-perfil-titulacion', methods=['POST'])
def generar_perfil_titulacion():
    data = request.json
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
        "ods": data.get("ods", []),
        "problema": data.get("problema", ""),
        "metodo_de_metodologia": data.get("metodo", ""),
        "tecnica": data.get("tecnica", ""),
        "instrumentos": data.get("instrumentos", ""),
        "bibliografia": data.get("bibliografia", []),
        "firma_estudiante": data.get("firma_estudiante", ""),
        "firma_director": data.get("firma_director", "")
    }
    pdf_path, error = generar_pdf_pdfco("templates/Perfil_Trabajo_Titulacion.docx", "perfil_titulacion.pdf", contexto)
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

        sha_res = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ruta_completa}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )

        sha = sha_res.json().get("sha") if sha_res.status_code == 200 else None

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
