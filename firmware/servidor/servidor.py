from flask import Flask, request, jsonify, send_file
import requests
import json
import os
import io
from dotenv import load_dotenv
from gtts import gTTS
from pydub import AudioSegment

load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("GROQ_API_KEY")

HISTORIAL_FILE = "historial.json"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_historial(h):
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

historial = cargar_historial()

SYSTEM_PROMPT = """Eres un asistente de voz inteligente 
Mi nombre es Miguel y tengo 20 años, cumplo el 21 de octubre, me gusta el anime y los videojuegos,
estudio robotica en cuarto semestre del tecnologico de Monterrey, te pedire ayuda
con cosas muy cotidianas o preguntas sobre mi carrera.
Respondes de forma concisa y clara, puedes hablar perfectamente varios idiomas. 
Tus respuestas no deben superar 3-5 oraciones. 
Tienes una personalidad amigable, un poco juguetona pero muy inteligente"""

MAX_TURNOS = 10

@app.route('/transcribir', methods=['POST'])
def transcribir():
    """
    Endpoint que recibe el archivo temporal de audio porciones enviadas desde ESP32,
    las guarda localmente y hace un request a la API de Groq para transcripción (Whisper).
    """
    audio = request.data
    with open('temp.wav', 'wb') as f:
        f.write(audio)
    
    with open('temp.wav', 'rb') as f:
        respuesta = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": "Bearer " + API_KEY},
            files={"file": ("audio.wav", f, "audio/wav")},
            data={"model": "whisper-large-v3-turbo"}
        )
    
    return jsonify(respuesta.json())

@app.route('/preguntar', methods=['POST'])
def preguntar():
    """
    Alimenta la solicitud de texto (transcripción) al historial actual
    y consulta a una IA de generación de texto en Groq.
    Retorna la respuesta en JSON.
    """
    global historial
    
    try:
        datos = request.get_json(force=True, silent=True)
        if datos is None:
            raw = request.data.decode('utf-8')
            datos = json.loads(raw)
        texto = datos.get('texto', '')
        print(f"Usuario: {texto}")
    except Exception as e:
        print("Error parseando:", e)
        return jsonify({"error": str(e)}), 400
    
    # 1. Agregar mensaje del usuario
    historial.append({"role": "user", "content": texto})
    
    # 2. Recortar si es muy largo
    if len(historial) > MAX_TURNOS * 2:
        historial = historial[-(MAX_TURNOS * 2):]
    
    # 3. Construir mensajes y llamar a Groq
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}] + historial
    
    respuesta = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + API_KEY},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": mensajes,
            "max_tokens": 200
        }
    )
    
    datos_respuesta = respuesta.json()
    
    # 4. Agregar respuesta de la IA y guardar
    try:
        contenido_ia = datos_respuesta['choices'][0]['message']['content']
        historial.append({"role": "assistant", "content": contenido_ia})
        guardar_historial(historial)
        print(f"IA: {contenido_ia}")
        print(f"[Historial: {len(historial)//2} turnos]")
    except Exception as e:
        print("No se pudo guardar en historial:", e)
    
    return jsonify(datos_respuesta)

@app.route('/hablar', methods=['POST'])
def hablar():
    """
    Convierte el texto recibido a un archivo de audio MP3 usando gTTS, luego
    lo convierte a un WAV sin signo (8-bits PCM_U8, 8000Hz mono) usando pyDub
    para que sea compatible con los pines DAC integrados en el ESP32.
    """
    try:
        # 1. Obtener el texto que envió el ESP32
        datos = request.get_json(force=True, silent=True)
        if datos is None:
            raw = request.data.decode('utf-8')
            datos = json.loads(raw)
            
        texto = datos.get('texto', 'Error al recibir el texto')
        print(f"Generando audio para: {texto}")
        
        # 2. Generar voz con gTTS (Acento mexicano)
        tts = gTTS(text=texto, lang='es', tld='com.mx')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # 3. Convertir con pydub a WAV, normalizar y empaquetar
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        
        # Pydub: Normalizar el volumen para que Luna siempre suene al maximo
        from pydub.effects import normalize
        audio = normalize(audio)
        
        # 8000 Hz, 1 canal (Mono), 1 byte (8 bits)
        audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(1) 
        
        wav_fp = io.BytesIO()
        # pcm_u8 es VITAL: El DAC del ESP32 solo lee valores positivos (0-255)
        audio.export(wav_fp, format="wav", codec="pcm_u8")
        wav_fp.seek(0)
        
        # 4. Enviar el archivo WAV de vuelta al ESP32
        return send_file(wav_fp, mimetype="audio/wav")
        
    except Exception as e:
        print("Error en ruta /hablar:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/despertar', methods=['POST'])
def despertar():
    audio = request.data
    with open('temp_wake.wav', 'wb') as f:
        f.write(audio)
        
    with open('temp_wake.wav', 'rb') as f:
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": "Bearer " + API_KEY},
            files={"file": ("audio.wav", f, "audio/wav")},
            data={
                "model": "whisper-large-v3-turbo",
                "prompt": "Luna, una, duna. Luna.",
                "language": "es"
            }
        )
        
    # Todo esto va alineado a la misma altura que el bloque "with"
    texto = resp.json().get('text', '').lower()
    print(f"--> Transcripción bruta de Wake Word: '{texto}'") 
    
    # Tolerancia a errores comunes de Whisper con la palabra "Luna" además de la puntuación
    posibles_coincidencias = ['luna', 'una', 'duna', 'bruna']
    # Eliminar signos de puntuación comunes que Whisper puede agregar
    texto_limpio = texto.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip()
    detectado = any(palabra in texto_limpio.split() or palabra == texto_limpio for palabra in posibles_coincidencias)
    
    print(f"Wake word check: '{texto}' → '{texto_limpio}' → {detectado}")
    return jsonify({"detectado": detectado})



@app.route('/reset', methods=['POST'])
def reset():
    global historial
    historial = []
    guardar_historial(historial)
    print("Historial borrado.")
    return jsonify({"status": "ok", "message": "Conversacion reiniciada"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)