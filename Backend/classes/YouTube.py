import yt_dlp
import re
import os
import json
from pydub import AudioSegment
from Gpt import transcribe_audio,get_response_from_openai
import requests




# Definir la ruta del archivo JSON de registro
REGISTRO_PATH = "registro_videos.json"


class YouTube:
    def __init__(self, ai_model: str = "gpt-4-turbo", url: str = ""):
        self.ai_model = ai_model
        self.url = url
        self.path_mp3 = None
        self.path_video = None
        self.transcription_path = None
        self.video_id = None  # ID único del video

        # Cargar o inicializar el registro de videos
        self.registro_videos = self.cargar_registro()

        # Si el video ya fue descargado, cargar sus paths desde el registro
        self.verificar_registro()

    def cargar_registro(self):
        """
        Carga el registro de videos desde el archivo JSON.
        """
        if os.path.exists(REGISTRO_PATH):
            with open(REGISTRO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {}

    def guardar_registro(self):
        """
        Guarda el registro de videos en el archivo JSON.
        """
        with open(REGISTRO_PATH, "w", encoding="utf-8") as f:
            json.dump(self.registro_videos, f, ensure_ascii=False, indent=4)

    def verificar_registro(self):
        """
        Verifica si el video ya ha sido procesado anteriormente
        y carga los paths si es así.
        """
        # Obtener el ID del video desde la URL
        self.video_id = self.extraer_video_id()
        if self.video_id in self.registro_videos:
            info = self.registro_videos[self.video_id]
            self.path_mp3 = info.get("path_mp3")
            self.path_video = info.get("path_video")
            self.transcription_path = info.get("transcription_path")
            self.path_thumbnail = info.get("path_thumbnail")
            print(f"Video ya procesado. Cargando paths desde el registro: {info}")

    def extraer_video_id(self):
        """
        Extrae el ID del video desde la URL de YouTube.
        Maneja varios formatos comunes de URL.
        """
        # Expresiones regulares para diferentes formatos de URL
        patrones = [
            r"v=([a-zA-Z0-9_-]{11})",            # URL con parámetro v=ID
            r"youtu\.be/([a-zA-Z0-9_-]{11})",    # URL corta de youtu.be
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",  # URL embed
        ]
        
        for patron in patrones:
            match = re.search(patron, self.url)
            if match:
                return match.group(1)
        
        print("No se pudo extraer el ID del video.")
        return None  # En caso de que no se encuentre un ID válido
    def eliminar_emojis(self, text):
        """
        Elimina emojis y otros caracteres especiales del texto,
        reemplaza espacios en blanco por guiones bajos y hace un trim de espacios al inicio y al final.
        """
        # Elimina emojis y caracteres no válidos
        sanitized_text = re.sub(r'[^\w\s-]', '', text)
        # Hacer trim de espacios en blanco al inicio y al final
        sanitized_text = sanitized_text.strip()
        # Reemplaza los espacios en blanco internos por guiones bajos
        sanitized_text = re.sub(r'\s+', '_', sanitized_text)
        return sanitized_text

    def descargar_mp3(self):
        """
        Descarga el audio en formato MP3 y guarda la ruta en el registro.
        """
        if self.path_mp3:
            print("El archivo MP3 ya existe. Saltando la descarga.")
            return

        base_dir = 'data'
        os.makedirs(base_dir, exist_ok=True)

        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            titulo = info_dict.get('title', 'audio')
            titulo_sanitizado = self.eliminar_emojis(titulo)
            titulo_sanitizado = re.sub(r'[\/:*?"<>|]', '', titulo_sanitizado)

        video_dir = os.path.join(base_dir, titulo_sanitizado)
        os.makedirs(video_dir, exist_ok=True)
        output_path = os.path.join(video_dir, titulo_sanitizado)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        
        self.path_mp3 = f"{output_path}.mp3"
        print(f"Descarga completada: {self.path_mp3}")

        # Actualizar el registro y guardar
        self.registro_videos[self.video_id] = {"path_mp3": self.path_mp3}
        self.guardar_registro()

    def descargar_video(self):
        """
        Descarga el video completo y guarda la ruta en el registro.
        """
        if self.path_video:
            print("El archivo de video ya existe. Saltando la descarga.")
            return

        base_dir = 'data'
        os.makedirs(base_dir, exist_ok=True)

        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            titulo = info_dict.get('title', 'video')
            titulo_sanitizado = self.eliminar_emojis(titulo)
            titulo_sanitizado = re.sub(r'[\/:*?"<>|]', '', titulo_sanitizado)

        video_dir = os.path.join(base_dir, titulo_sanitizado)
        os.makedirs(video_dir, exist_ok=True)
        output_path = os.path.join(video_dir, titulo_sanitizado)

        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': output_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        
        self.path_video = f"{output_path}.mp4"
        print(f"Descarga completada: {self.path_video}")

        # Actualizar el registro y guardar
        self.registro_videos[self.video_id]["path_video"] = self.path_video
        self.guardar_registro()

    def transcribir_audio(self):
        """
        Transcribe el audio del archivo MP3 y guarda la transcripción en un archivo .txt.
        """
        if self.transcription_path:
            print("La transcripción ya existe. Saltando la transcripción.")
            return
        
        # Intentar descargar la transcripción automática de YouTube
        ydl_opts = {
            'skip_download': True,  # No descargues el video, solo extrae información
            'writesubtitles': True,  # Intenta obtener subtítulos automáticos
            'subtitle': 'best',  # Selecciona el mejor idioma disponible
            'subtitleslangs': ['en'],  # Puedes ajustar el idioma según necesites
            'outtmpl': os.path.join(os.path.dirname(self.path_mp3), 'temp_subtitles')
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # Aquí usamos yt_dlp.YoutubeDL en lugar de YoutubeDL directamente
            try:
                info_dict = ydl.extract_info(self.url, download=False)
                # Revisar si se descargó algún subtítulo
                subtitle_files = [f for f in os.listdir(os.path.dirname(self.path_mp3)) if f.startswith("temp_subtitles")]
                if subtitle_files:
                    # Renombrar el archivo de subtítulos como la transcripción final
                    self.transcription_path = os.path.join(os.path.dirname(self.path_mp3), f"transcription_{os.path.basename(self.path_mp3)}.txt")
                    os.rename(os.path.join(os.path.dirname(self.path_mp3), subtitle_files[0]), self.transcription_path)
                    print(f"Transcripción automática de YouTube descargada: {self.transcription_path}")
                    
                    # Actualizar el registro JSON y salir de la función
                    if self.video_id not in self.registro_videos:
                        self.registro_videos[self.video_id] = {}
                    self.registro_videos[self.video_id]["transcription_path"] = self.transcription_path
                    self.guardar_registro()
                    print("--------------------------------")
                    print("---------TRANSCRIPCION VIDEO----")
                    print("--------------------------------")
                    return
                else:
                    print("No se encontró transcripción automática en YouTube. Procediendo con OpenAI.")
            except Exception as e:
                print(f"No se pudo descargar la transcripción automática de YouTube: {e}")

        # Si no se encontró transcripción automática, proceder con OpenAI

        audio = AudioSegment.from_mp3(self.path_mp3)
        duration_ms = len(audio)
        segment_duration_ms = 5 * 60 * 1000  # 5 minutos en milisegundos

        titulo_sanitizado = os.path.splitext(os.path.basename(self.path_mp3))[0]
        self.transcription_path = os.path.join(os.path.dirname(self.path_mp3), f"transcription_{titulo_sanitizado}.txt")

        full_transcription = ""
        for i in range(0, duration_ms, segment_duration_ms):
            segment = audio[i:i + segment_duration_ms]
            segment_path = os.path.join(os.path.dirname(self.path_mp3), f"temp_segment_{i // segment_duration_ms}.mp3")
            segment.export(segment_path, format="mp3")
            
            transcription_text = transcribe_audio(segment_path)
            full_transcription += transcription_text + "\n"
            os.remove(segment_path)

        with open(self.transcription_path, "w", encoding="utf-8") as f:
            f.write(full_transcription)

        print(f"Transcripción completada: {self.transcription_path}")

        # Actualizar el registro y guardar
        self.registro_videos[self.video_id]["transcription_path"] = self.transcription_path
        self.guardar_registro()

    def descargar_thumbnail(self):
        """
        Descarga la miniatura del video y la guarda en la carpeta correspondiente
        con el nombre `thumbnail_nombre_del_video.jpg`.
        """
        if not self.video_id:
            print("No se pudo descargar la miniatura: ID de video no encontrado.")
            return

        # Asegúrate de que ya tienes un nombre sanitizado del video
        if not self.path_video and not self.path_mp3:
            print("Error: Debes descargar el video o el audio primero para obtener el título.")
            return

        titulo_sanitizado = os.path.splitext(os.path.basename(self.path_video or self.path_mp3))[0]

        base_dir = 'data'
        video_dir = os.path.join(base_dir, titulo_sanitizado)
        os.makedirs(video_dir, exist_ok=True)

        # URL de la miniatura
        thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/maxresdefault.jpg"
        thumbnail_path = os.path.join(video_dir, f"thumbnail_{titulo_sanitizado}.jpg")

        # Descargar la miniatura
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            with open(thumbnail_path, "wb") as f:
                f.write(response.content)
            self.path_thumbnail = thumbnail_path
            print(f"Miniatura descargada: {thumbnail_path}")
        else:
            print("No se pudo descargar la miniatura: enlace no válido.")

        # Actualizar el registro y guardar
        if self.video_id not in self.registro_videos:
            self.registro_videos[self.video_id] = {}
        self.registro_videos[self.video_id]["path_thumbnail"] = self.path_thumbnail
        self.guardar_registro()



    def generara_resumen_video(self, formato="Markdown", idioma="Castellano", MODEL='gpt-4-turbo'):
        """
        Genera un resumen del video en formato Markdown.
        """
        path=self.transcription_path
        # Lee el contenido del archivo de texto
        with open(self.transcription_path, 'r', encoding='utf-8') as file:
            prompt = file.read()

        # Extraemos el nombre del video (sin extensión)
        nombre_video = os.path.basename(self.transcription_path).replace('.txt', '')
        directorio_base = os.path.dirname(path)

        
        # Creamos el sistema de prompt para generar un resumen de video
        system_prompt=f"""
            Generate a summary from the transcription of a video, including a detailed introduction, explanation of key points, and a final conclusion. 

            Use the following guidelines for the summary:

            - Write in the specified language `{idioma}`.
            - Maintain a formal tone throughout the text.
            - Begin with a compelling introduction that presents the topic of the video and encourages the reader to continue reading.
            - Clearly explain the key points, detailing significant information in an organized and comprehensible manner.
            - Conclude with a final summary that succinctly encapsulates the key points to leave the audience with a clear understanding of the main message.

            # Output Format

            The summary should have the following structure:

            - **Introduction:** A brief introduction presenting the theme of the video.
            - **Detailed explanation of key points:** A detailed yet concise discussion of the primary elements of the video.
            - **Conclusion:** A succinct summary that ties together the main arguments or points of the video.

            The output should be consistent with the following parameters:
            - Replace `{idioma}` with the correct language (e.g., Spanish, English).
            - Replace `{formato}` with the suitable format (e.g., plaintext, HTML).

            # Examples

            Input: (Fragment of the transcribed video)
            "Hoy les traigo una lista de consejos imprescindibles para mejorar la productividad..."

            Output: 

            **Introducción:** En la actualidad, ser productivo se ha vuelto un desafío importante debido a la cantidad de distracciones y el ritmo acelerado del día a día. A continuación, os presento algunos de los mejores consejos para mejorar nuestra productividad.

            **Puntos clave detallados:**
            1. **Define metas claras:** Es esencial establecer objetivos que sean alcanzables y específicos.
            2. **Elimina distracciones:** Identifica las fuentes de distracción y toma medidas para reducirlas.
            3. **Administra tu tiempo adecuadamente:** Utiliza técnicas como la del Pomodoro para dividir tu trabajo en intervalos manejables.

            **Conclusión:** Estos consejos son fundamentales para ayudarte a mejorar tu productividad en el trabajo y en la vida diaria. Pon en práctica estas recomendaciones y notarás una diferencia significativa. Si quieres saber más, no dudes en ver nuestro video completo.

            # Notes

            - Ensure that the explanation of key points balances between detail and brevity.
            - Adapt tone and language to suit the given `{idioma}` and required `{formato}` to ensure consistency.

        """

        response =get_response_from_openai(system_prompt=system_prompt,prompt=prompt)

        articulo = response

        # Determinar la extensión según el formato
        if formato.lower() == "markdown":
            extension = ".md"
        elif formato.lower() == "html":
            extension = ".html"
        else:
            extension = ".txt"  # Por defecto, si es un formato no especificado

        # Crear el nombre del archivo para el artículo de blog
        carpeta_resumen = os.path.join(directorio_base, 'resumen_' + nombre_video)
        if not os.path.exists(carpeta_resumen):
            os.makedirs(carpeta_resumen)

        ruta_resumen = os.path.join(carpeta_resumen, f'resumen_{nombre_video}{extension}')

        # Guardar el artículo en el formato correspondiente
        with open(ruta_resumen, 'w', encoding='utf-8') as resumen_file:
            resumen_file.write(articulo)

        print(f"Artículo optimizado para SEO guardado en: {ruta_resumen}")
        return ruta_resumen


    def generar_articulo_blog(self, formato="Markdown", idioma="Castellano", MODEL='gpt-4-turbo'):
        path=self.transcription_path
        # Lee el contenido del archivo de texto
        with open(path, 'r', encoding='utf-8') as file:
            prompt = file.read()

        # Extraemos el nombre del video (sin extensión)
        nombre_video = os.path.basename(path).replace('.txt', '')
        directorio_base = os.path.dirname(path)
        
        # Creamos el sistema de prompt para generar un artículo de blog optimizado para SEO
        prompt_system = f"""
        Eres un experto en redacción de artículos de blog optimizados para SEO. 
        A partir del texto proporcionado, que es una transcripción de uno de mis  videos, 
        debes generar un artículo para mi blog y esté optimizado para motores de búsqueda en tono formal y en primera persona 
        para poder generar tráfico de mi blog hacia el vídeo.
        
        **Instrucciones detalladas:**
        - Comienza con una introducción que presente el tema del video y atraiga la atención del lector.
        - Usa subtítulos H2 y H3 para estructurar el contenido y hacerlo escaneable.
        - Incluye una lista de palabras clave relevantes relacionadas con el tema del video.
        - Asegúrate de que cada sección esté bien desarrollada y que las palabras clave estén distribuidas naturalmente a lo largo del artículo.
        - Usa párrafos cortos y sencillos para mejorar la legibilidad.
        - Incluye una conclusión clara que resuma los puntos clave del artículo.
        - Optimiza para SEO usando llamadas a la acción (CTA) relevantes, como "Descubre más", "Visita nuestra página", etc.
        
        El resultado debe estar en formato {formato} y en el idioma {idioma}.
        """
        
        
        # Generar el artículo usando el modelo GPT
        response =get_response_from_openai(system_prompt=prompt_system,prompt=prompt)

        articulo = response

        # Determinar la extensión según el formato
        if formato.lower() == "markdown":
            extension = ".md"
        elif formato.lower() == "html":
            extension = ".html"
        else:
            extension = ".txt"  # Por defecto, si es un formato no especificado

        # Crear el nombre del archivo para el artículo de blog
        carpeta_articulo = os.path.join(directorio_base, 'articulo_' + nombre_video)
        if not os.path.exists(carpeta_articulo):
            os.makedirs(carpeta_articulo)

        ruta_articulo = os.path.join(carpeta_articulo, f'articulo_{nombre_video}{extension}')

        # Guardar el artículo en el formato correspondiente
        with open(ruta_articulo, 'w', encoding='utf-8') as articulo_file:
            articulo_file.write(articulo)

        print(f"Artículo optimizado para SEO guardado en: {ruta_articulo}")
        return ruta_articulo