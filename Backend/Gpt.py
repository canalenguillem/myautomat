from openai import OpenAI
from decouple import config


# Cargar la API Key desde el archivo .env
api_key = config('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
def transcribe_audio(file_path):
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Error transcribiendo el archivo {file_path}: {e}")
        return ""
    

def get_response_from_openai(system_prompt, prompt,format="Markdown", idioma="Castellano", MODEL='gpt-4-turbo'):
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': prompt}
    ]
    # Generar el artículo usando el modelo GPT
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=1,
        max_tokens=4096,  # Aumentamos los tokens para generar un artículo completo
        n=1
    )
    return response.choices[0].message.content