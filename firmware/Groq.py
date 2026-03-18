import urequests
import ujson
import config
import time

def preguntas(mnsj):
    url = "https://api.groq.com/openai/v1/chat/completions"
    # IMPORTANTE: Groq necesita estos headers
    headers = {
        "Authorization": "Bearer " + config.API_KEY,
        "Content-Type": "application/json"
    }
    
    cuerpo = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": mnsj}
        ],
        "max_tokens": 200
    }

    try:
        print("Consultando a Groq...")
        # Agregamos headers=headers aquí abajo
        respuesta = urequests.post(url, json=cuerpo, headers=headers, timeout=30)
        
        if respuesta.status_code == 200:
            print("¡Éxito! Respuesta de Groq:")
            # Para extraer solo el texto:
            datos = respuesta.json()
            mensaje_ia = datos['choices'][0]['message']['content']
            print(mensaje_ia)
            return mensaje_ia
        else:
            print(f"Error {respuesta.status_code}: {respuesta.text}")
            
        respuesta.close()
        
    except Exception as e:
        print("Error de conexión:", e)
        time.sleep(2)