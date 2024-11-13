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

    def generate_summary_path(self, format="txt"):
        """
        Genera el nombre del archivo de resumen en el mismo directorio que el archivo MP3.
        Si el formato es Markdown, utiliza la extensión .md.
        """
        base_name = os.path.splitext(os.path.basename(self.path_mp3))[0]
        extension = "md" if format.lower() == "markdown" else "txt"
        summary_file = f"summary_{base_name}.{extension}"
        return os.path.join(os.path.dirname(self.path_mp3), summary_file)

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
        """
        Carga el registro de transcripciones desde un archivo JSON.
        """
        if os.path.exists(self.REGISTRY_FILE):
            with open(self.REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_registry(self, registry):
        """
        Guarda el registro de transcripciones en un archivo JSON.
        """
        with open(self.REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)

    def check_if_transcribed(self):
        """
        Verifica si el audio ya fue transcrito consultando el registro.
        """
        registry = self.load_registry()
        entry = registry.get(self.audio_id)
        
        # Asegurarse de que `entry` sea un diccionario
        if isinstance(entry, dict) and "transcription" in entry:
            return entry["transcription"]
        return None

    def check_if_summarized(self):
        """
        Verifica si el resumen del audio ya existe consultando el registro.
        """
        registry = self.load_registry()
        entry = registry.get(self.audio_id)
        
        # Asegurarse de que `entry` sea un diccionario
        if isinstance(entry, dict) and "summary" in entry:
            return entry["summary"]
        return None

    def register_transcription(self):
        """
        Registra la transcripción del audio en el archivo de registro.
        """
        registry = self.load_registry()
        
        # Asegurarse de que la entrada para este audio sea un diccionario
        if not isinstance(registry.get(self.audio_id), dict):
            registry[self.audio_id] = {}
        
        registry[self.audio_id]["transcription"] = self.transcription_path
        self.save_registry(registry)

    def register_summary(self, summary_path):
        """
        Registra el resumen del audio en el archivo de registro.
        """
        registry = self.load_registry()
        
        # Asegurarse de que la entrada para este audio sea un diccionario
        if not isinstance(registry.get(self.audio_id), dict):
            registry[self.audio_id] = {}
        
        registry[self.audio_id]["summary"] = summary_path
        self.save_registry(registry)

    def transcribe(self):
        """
        Transcribe el audio si aún no ha sido transcrito y guarda la transcripción.
        """
        if self.check_if_transcribed():
            print(f"El archivo '{self.path_mp3}' ya fue transcrito. Leyendo transcripción existente.")
            with open(self.transcription_path, 'r', encoding='utf-8') as f:
                return f.read()

        try:
            transcription = transcribe_audio(self.path_mp3)
            with open(self.transcription_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            self.register_transcription()
            print(f"Transcripción guardada en: {self.transcription_path}")
            return transcription

        except Exception as e:
            print(f"Error al transcribir el audio: {e}")
            return None

    def get_summary(self, idioma="Castellano", format="Markdown", context=None):
        """
        Genera un resumen de la transcripción y lo guarda en el mismo directorio con extensión adecuada.
        """
        # Establecer la ruta del archivo de resumen con la extensión correcta
        summary_path = self.generate_summary_path(format)

        if self.check_if_summarized():
            print(f"Resumen ya existente. Leyendo desde: {summary_path}")
            with open(summary_path, 'r', encoding='utf-8') as f:
                return f.read()

        transcription_text = ""
        try:
            with open(self.transcription_path, 'r', encoding='utf-8') as f:
                transcription_text = f.read()

            system_prompt = f"""
                Resume el contenido de la transcripción de un audio.

                # Parámetros
                - **Idioma del resumen**: {idioma}
                - **Formato de salida**: {format}

                # Output
                Genera el resumen en el idioma y formato especificado.
            """
            if context:
                system_prompt += f"\n\nContexto:\n\n{context}"

            prompt = transcription_text
            summary = get_response_from_openai(system_prompt=system_prompt, prompt=prompt)

            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self.register_summary(summary_path)
            print(f"Resumen guardado en: {summary_path}")
            return summary

        except Exception as e:
            print(f"Error al generar el resumen: {e}")
            return None
