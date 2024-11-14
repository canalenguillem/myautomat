from flask import Flask, render_template, request, jsonify,url_for
from classes.YouTube import YouTube
from classes.Audio import Audio
import markdown
import os
import shutil


app = Flask(__name__)

# Asegurarse de que la carpeta de miniaturas exista
THUMBNAIL_FOLDER = os.path.join(app.root_path, 'static', 'thumbnails')
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/youtube', methods=['GET', 'POST'])
def youtube():
    if request.method == 'POST':
        url = request.form.get('url')
        generate_transcription = 'transcription' in request.form
        content_type = request.form.get('type')  # Recoge la opción seleccionada en el formulario (summary, tutorial, description)
        idioma = request.form.get('language', 'Castellano')  # Obtiene el idioma seleccionado o usa "Castellano" por defecto

        if not url:
            return jsonify({"success": False, "error": "URL no proporcionada"}), 400

        try:
            yt = YouTube(url=url)
            yt.descargar_mp3()
            yt.descargar_video()

            result = {"success": True, "thumbnail": None, "content": None}

            # Generar transcripción si está seleccionado
            if generate_transcription:
                yt.transcribir_audio()

            # Generar el contenido adecuado según el tipo seleccionado
            if content_type == 'summary':
                resumen_path = yt.generara_resumen_video(idioma=idioma)
                if resumen_path:
                    with open(resumen_path, 'r', encoding='utf-8') as f:
                        summary_markdown = f.read()
                        summary_html = markdown.markdown(summary_markdown)
                        result["content"] = summary_html
            elif content_type == 'tutorial':
                tutorial_path = yt.generar_tutorial_web(idioma=idioma)
                if tutorial_path:
                    with open(tutorial_path, 'r', encoding='utf-8') as f:
                        tutorial_markdown = f.read()
                        tutorial_html = markdown.markdown(tutorial_markdown)
                        result["content"] = tutorial_html
            elif content_type == 'description':
                description_path, title = yt.generar_descripcion_seo(idioma=idioma)
                if description_path:
                    with open(description_path, 'r', encoding='utf-8') as f:
                        description_content = f.read()
                        # Formato con párrafos independientes para el título y la descripción
                        result["content"] = f"<p><strong>Título:</strong> {title}</p><p><strong>Descripción:</strong> {description_content}</p>"

            # Descargar miniatura del video
            yt.descargar_thumbnail()
            if yt.path_thumbnail:
                thumbnail_name = os.path.basename(yt.path_thumbnail)
                thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_name)
                shutil.move(yt.path_thumbnail, thumbnail_path)
                result["thumbnail"] = url_for('static', filename=f'thumbnails/{thumbnail_name}')

            return jsonify(result)
        
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        return render_template('youtube_form.html')

@app.route('/audio', methods=['GET', 'POST'])
def audio():
    if request.method == 'POST':
        file = request.files['audio_file']
        generate_transcription = 'transcription' in request.form
        generate_summary = 'summary' in request.form

        if file:
            path_mp3 = os.path.join('data', file.filename)
            file.save(path_mp3)

            audio = Audio(path_mp3=path_mp3)
            
            if generate_transcription:
                audio.transcribe()
            if generate_summary:
                audio.get_summary()

            return redirect(url_for('index'))

    return render_template('audio_form.html')

if __name__ == '__main__':
    app.run(debug=True)
