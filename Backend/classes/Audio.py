from pydub import AudioSegment
import os
import json
import hashlib
from Gpt import transcribe_audio, get_response_from_openai

class Audio:
    REGISTRY_FILE = "transcription_registry.json"

    def __init__(self, path_mp3):
        self.path_mp3 = path_mp3
        self.transcription_path = self.generate_transcription_path()
        self.audio_id = self.get_audio_id()  # ID único basado en hash del archivo

    def generate_transcription_path(self):
        """
        Genera el nombre del archivo de transcripción en el mismo directorio que el archivo MP3.
        """
        base_name = os.path.splitext(os.path.basename(self.path_mp3))[0]
        transcription_file = f"transcripcion_{base_name}.txt"
        return os.path.join(os.path.dirname(self.path_mp3), transcription_file)

    def generate_segment_path(self, segment_index):
        """
        Genera un nombre único para cada segmento de audio.
        """
        base_name = os.path.splitext(os.path.basename(self.path_mp3))[0]
        return os.path.join(os.path.dirname(self.path_mp3), f"{base_name}_segment_{segment_index}.mp3")

    def get_audio_id(self):
        """
        Genera un identificador único para el audio basado en su contenido (hash MD5).
        """
        hasher = hashlib.md5()
        with open(self.path_mp3, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def load_registry(self):
        if os.path.exists(self.REGISTRY_FILE):
            with open(self.REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_registry(self, registry):
        with open(self.REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)

    def check_if_transcribed(self):
        registry = self.load_registry()
        entry = registry.get(self.audio_id)
        return isinstance(entry, dict) and "transcription" in entry

    def register_transcription(self):
        registry = self.load_registry()
        if not isinstance(registry.get(self.audio_id), dict):
            registry[self.audio_id] = {}
        registry[self.audio_id]["transcription"] = self.transcription_path
        self.save_registry(registry)

    def divide_audio(self, segment_length=300):
        """
        Divide el archivo de audio en segmentos de la longitud especificada.
        """
        audio = AudioSegment.from_file(self.path_mp3)
        segments = []
        for i in range(0, len(audio), segment_length * 1000):  # Convertir segundos a milisegundos
            segments.append(audio[i:i + segment_length * 1000])
        return segments

    def save_audio_segments(self, segments):
        """
        Guarda los segmentos de audio como archivos individuales.
        """
        segment_paths = []
        for idx, segment in enumerate(segments):
            segment_path = self.generate_segment_path(idx)
            segment.export(segment_path, format="mp3")
            segment_paths.append(segment_path)
        return segment_paths

    def transcribe_long_audio(self):
        """
        Divide el audio en segmentos, los transcribe y guarda la transcripción completa.
        """
        if self.check_if_transcribed():
            print(f"El archivo '{self.path_mp3}' ya fue transcrito. Leyendo transcripción existente.")
            with open(self.transcription_path, 'r', encoding='utf-8') as f:
                return f.read()

        try:
            segments = self.divide_audio()
            segment_paths = self.save_audio_segments(segments)

            full_transcription = ""
            for segment_path in segment_paths:
                transcription = transcribe_audio(segment_path)
                full_transcription += transcription + "\n"
                os.remove(segment_path)  # Eliminar el archivo de segmento

            with open(self.transcription_path, 'w', encoding='utf-8') as f:
                f.write(full_transcription)
            
            self.register_transcription()
            print(f"Transcripción completa guardada en: {self.transcription_path}")
            return full_transcription

        except Exception as e:
            print(f"Error al transcribir el audio: {e}")
            return None
        
    def tutoria(self,alumno,asistentes="Tutor del centro",idioma="Catalán",context=""):
        print("muntant tutoria")
        system_prompt="""
            Eres un analista de transcripciones y a partir de ellas 
            debes generar lo que se te pida a través de la trascipción
            y la petición de prompt que te hagan.
        """
        with open(self.transcription_path, 'r', encoding='utf-8') as file:
            # Lee el contenido del archivo y lo asigna a una variable
            transcription_content = file.read()

        prompt=f"""
            A partir de la transcipció que he tenido de la tutoria del alumno
            {alumno} con los asistentes {asistentes} quiero la información para 
            completar los campos del formulario de tutoria siguientes:
            - Observacions per a la convocatòria (surt a la web de famílies com a convocatòria i acta):
            - Assistents (surt a la web de famílies si s'ha publicat l'acta):
            - Seguiments acords anteriors (surt a la web de famílies si s'ha publicat l'acta):
            - Temes tractats (surt a la web de famílies si s'ha publicat l'acta):
            - Acords presos (surt a la web de famílies si s'ha publicat l'acta):

            Quiero una informació detallada en base a la transcripción trantado todos los tema a modo de acta.

            TRANSCIPCION DE LA TUTORIA: 
            {transcription_content}

        """
        if context!="":
            prompt += f"\n\nCONTEXTO: {context}"

        resposta = get_response_from_openai(system_prompt,prompt,format="Markdown",idioma=idioma)
        print("--------------------------------")
        print(resposta)
        print("--------------------------------")
        file_name = os.path.splitext(os.path.basename(self.transcription_path))[0]
        markdown_file_name = f"tutoria_{file_name}.md"
        print(markdown_file_name)

        with open(markdown_file_name, 'w', encoding='utf-8') as md_file:
            print("--------------------------------")
            print("escribiendo fichero")
            print("--------------------------------")

            md_file.write(f"# Tutoria: {file_name}\n\n")
            md_file.write(resposta)
        return markdown_file_name
            

    def apunts(self,materia,idioma="Catalán",context=""):
        print("muntant tutoria")
        system_prompt="""
            Eres un analista de transcripciones y a partir de ellas 
            debes generar lo que se te pida a través de la trascipción
            y la petición de prompt que te hagan.
        """
        with open(self.transcription_path, 'r', encoding='utf-8') as file:
            # Lee el contenido del archivo y lo asigna a una variable
            transcription_content = file.read()

        prompt=f"""
            A partir de la transcipció de una de mis classes de la materia de {materia}
            Quiero que hagas unos apuntes que consistan en 
            -Introducción
            -Puntos clave tratados en la clase
            -Desarrollo de los puntos con ejemplos y comandos
            -Conclusión y recomendaciones de estudio
            TRANSCIPCION DE LA clase: 
            {transcription_content}

        """
        if context!="":
            prompt += f"\n\nCONTEXTO: {context}"

        resposta = get_response_from_openai(system_prompt,prompt,format="Markdown",idioma=idioma)
        print("--------------------------------")
        print(resposta)
        print("--------------------------------")
        file_name = os.path.splitext(os.path.basename(self.transcription_path))[0]
        markdown_file_name = f"tutoria_{file_name}.md"
        print(markdown_file_name)

        with open(markdown_file_name, 'w', encoding='utf-8') as md_file:
            print("--------------------------------")
            print("escribiendo fichero")
            print("--------------------------------")

            md_file.write(f"# Tutoria: {file_name}\n\n")
            md_file.write(resposta)
        return markdown_file_name





