from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.environ.get("GROQ_API_KEY")

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
    try:
        datos = request.get_json(force=True, silent=True)
        if datos is None:
            raw = request.data.decode('utf-8')
            print("Raw recibido:", raw)
            datos = json.loads(raw)
        texto = datos.get('texto', '')
        print("Texto recibido:", texto)
    except Exception as e:
        print("Error parseando:", e)
        return jsonify({"error": str(e)}), 400
    
    respuesta = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + API_KEY},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": texto}],
            "max_tokens": 200
        }
    )
    
    return jsonify(respuesta.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)