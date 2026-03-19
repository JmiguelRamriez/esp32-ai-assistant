from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv

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
    
    # 4. Agregar respuesta de la IA y guardar todo de una vez
    try:
        contenido_ia = datos_respuesta['choices'][0]['message']['content']
        historial.append({"role": "assistant", "content": contenido_ia})
        guardar_historial(historial)
        print(f"IA: {contenido_ia}")
        print(f"[Historial: {len(historial)//2} turnos]")
    except Exception as e:
        print("No se pudo guardar en historial:", e)
    
    return jsonify(datos_respuesta)

@app.route('/reset', methods=['POST'])
def reset():
    global historial
    historial = []
    guardar_historial(historial)
    print("Historial borrado.")
    return jsonify({"status": "ok", "message": "Conversacion reiniciada"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)