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
        output_type = request.form.get('output_type', 'resumen')
        idioma = request.form.get('language', 'Castellano')

        if not url:
            return jsonify({"success": False, "error": "URL no proporcionada"}), 400

        try:
            yt = YouTube(url=url)
            yt.descargar_mp3()
            yt.descargar_video()

            result = {"success": True, "thumbnail": None, "output": None}

            if generate_transcription:
                yt.transcribir_audio()
            
            if output_type == 'resumen':
                resumen_path = yt.generara_resumen_video(idioma=idioma)
                if resumen_path:
                    with open(resumen_path, 'r', encoding='utf-8') as f:
                        summary_markdown = f.read()
                        summary_html = markdown.markdown(summary_markdown)
                        result["output"] = summary_html
            elif output_type == 'tutorial':
                tutorial_path = yt.generar_tutorial_web(idioma=idioma)
                if tutorial_path:
                    with open(tutorial_path, 'r', encoding='utf-8') as f:
                        tutorial_content = f.read()
                        if tutorial_path.endswith('.md'):
                            tutorial_html = markdown.markdown(tutorial_content)
                        else:
                            tutorial_html = tutorial_content
                        result["output"] = tutorial_html

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
