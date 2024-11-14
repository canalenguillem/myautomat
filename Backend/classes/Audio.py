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

            # Generar el resumen
            system_prompt=f"""
                Resume el contenido de la transcripción de un audio.

                # Parámetros

                - **Idioma del resumen**: El resumen debe ser entregado en el idioma especificado por la variable `{idioma}`.
                - **Formato de salida**: El resumen debe entregarse en el formato deseado según la variable `{format}`.

                # Pasos

                1. Lee toda la transcripción y comprende los puntos clave y el contexto general.
                2. Identifica las ideas principales y la información relevante discutida en el audio.
                3. Condensa esas ideas principales y elimina detalles irrelevantes, garantizando que el resultado sea un resumen conciso pero completo.
                4. Asegúrate de que el resumen mantenga la claridad y transmita las partes clave sin grandes omisiones ni adiciones innecesarias.

                # Output Format

                El resumen debe:

                - **Idioma**: Estar en el idioma especificado por la variable `{idioma}`.
                - **Formato**: La salida estará en el formato que se indique en la variable `{format}`. Por ejemplo:

                ### Parámetros
                `{idioma}`: Español  
                `{format}`: texto simple

                (Asegúrate de que el real ejemplo tenga más o menos el mismo nivel de detalle ajustado al contexto, pudiendo variar en longitud según la complejidad de la transcripción relacionada.)
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
        
    def generate_response_path(self, format="txt"):
        """
        Genera el nombre del archivo de respuesta en el mismo directorio que el archivo MP3.
        Si el formato es Markdown, utiliza la extensión .md.
        """
        base_name = os.path.splitext(os.path.basename(self.path_mp3))[0]
        extension = "md" if format.lower() == "markdown" else "txt"
        response_file = f"respuesta_email_{base_name}.{extension}"
        return os.path.join(os.path.dirname(self.path_mp3), response_file)
    
    def check_if_mail_generated(self):
        """
        Verifica si la respuesta de correo ya ha sido generada consultando el registro.
        """
        registry = self.load_registry()
        entry = registry.get(self.audio_id)
        
        if isinstance(entry, dict) and "mail_response" in entry:
            return entry["mail_response"]
        return None
    
    def register_mail_response(self, response_path):
        """
        Registra la respuesta del correo en el archivo de registro.
        """
        registry = self.load_registry()
        if not isinstance(registry.get(self.audio_id), dict):
            registry[self.audio_id] = {}
        
        registry[self.audio_id]["mail_response"] = response_path
        self.save_registry(registry)
    

    def get_mail(self, idioma="Castellano", format="Markdown", context=None):
        """
        Genera una respuesta de correo electrónico a partir de la transcripción y la guarda en un archivo.
        """
        response_path = self.generate_response_path(format)

        if self.check_if_mail_generated():
            print(f"Respuesta ya existente. Leyendo desde: {response_path}")
            with open(response_path, 'r', encoding='utf-8') as f:
                return f.read()

        transcription_text = ""
        try:
            with open(self.transcription_path, 'r', encoding='utf-8') as f:
                transcription_text = f.read()

            system_prompt = f"""
                Eres un experto en análisis de contenido. A partir de la transcripción proporcionada de una conversación,
                debes generar un documento que explique en detalle lo que se dice, analizando el contenido y proporcionando
                una descripción clara y organizada. 
                
                **Instrucciones detalladas:**
                - Explica con todo detalle los temas principales de la conversación.
                - Explica detalladamente, no resumas lo que se dice en cada parte de la conversación.
                - Usa subtítulos H2 para separar las diferentes secciones temáticas de la conversación.
                - Asegúrate de que el análisis sea claro y exhaustivo.
                - En ningún caso hagas referencia a la transcripción ni a la conversación
                - Utiliza el mimo tiempo verbal
                {context}
                
                El resultado debe estar en formato {format} y en el idioma {idioma}.
                """
            if context:
                system_prompt += f"\n\nContexto adicional:\n\n{context}"

            prompt = transcription_text
            mail_response = get_response_from_openai(system_prompt=system_prompt, prompt=prompt)

            with open(response_path, 'w', encoding='utf-8') as f:
                f.write(mail_response)
            
            self.register_mail_response(response_path)
            print(f"Respuesta de correo guardada en: {response_path}")
            return mail_response

        except Exception as e:
            print(f"Error al generar la respuesta de correo: {e}")
            return None
        
    def get_enunciado(self, idioma="Castellano", format="Markdown", context=None):
        """
        Genera una enunciado de una practia
        """
        response_path = self.generate_response_path(format)

        if self.check_if_mail_generated():
            print(f"Respuesta ya existente. Leyendo desde: {response_path}")
            with open(response_path, 'r', encoding='utf-8') as f:
                return f.read()

        transcription_text = ""
        try:
            with open(self.transcription_path, 'r', encoding='utf-8') as f:
                transcription_text = f.read()

            system_prompt = f"""
                Eres un experto en análisis de contenido. A partir de la transcripción proporcionada de una conversación,
                debes generar un enunciado para un tarea de classroom 
                
                **Instrucciones detalladas:**
                - Haz una introducción de los contenidos de la tarea
                - Explica detalladamente, los pasos que deben realizar los alumnos
                - Usa subtítulos H2 para separar las diferentes secciones temáticas de la tarea.
                - Asegúrate de que el análisis sea claro y exhaustivo.
                - En ningún caso hagas referencia a la transcripción ni a la conversación

                
                {context}
                
                El resultado debe estar en formato {format} y en el idioma {idioma}.
                """
            if context:
                system_prompt += f"\n\nContexto adicional:\n\n{context}"

            prompt = transcription_text
            mail_response = get_response_from_openai(system_prompt=system_prompt, prompt=prompt)

            with open(response_path, 'w', encoding='utf-8') as f:
                f.write(mail_response)
            
            self.register_mail_response(response_path)
            print(f"Respuesta de correo guardada en: {response_path}")
            return mail_response

        except Exception as e:
            print(f"Error al generar la respuesta de correo: {e}")
            return None