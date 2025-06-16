@app.route('/generar-doc', methods=['POST'])
def generar_doc():
    try:
        data = request.json
        print("Recibido:", data)  # 👈 LOG DE DATOS

        doc = DocxTemplate("templates/2_Solicitud_fecha_de_defensa_final.docx")
        contexto = {
            "fecha": data.get("fecha", ""),
            "TITULO DEL TRABAJO DE TITULACION": data.get("titulo", ""),
            "NOMBRE/S DE ESTUDIANTE/S": data.get("nombres_estudiantes", ""),
            "nombres completos director": data.get("nombre_director", "")
        }

        print("Contexto:", contexto)  # 👈 LOG DE CONTEXTO

        doc.render(contexto)
        output_path = "solicitud_generada.docx"
        doc.save(output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("ERROR AL GENERAR:", str(e))  # 👈 LOG DEL ERROR
        return f"Error interno del servidor: {e}", 500
