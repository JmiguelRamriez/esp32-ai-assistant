import usocket
import urequests
import config
import grabar
import ujson
import os
import gc
import pantalla

def escuchar_y_preguntar(boton):
    grabar.grabar(boton)
    gc.collect()

    pantalla.mostrar_pensando()
    print("Memoria libre:", gc.mem_free())

    # --- ENVÍO DE AUDIO POR SOCKETS (A prueba de fallos de RAM) ---
    try:
        tam = os.stat("audio.wav")[6]
        addr = (config.SERVIDOR, config.PUERTO)
        
        sock = usocket.socket()
        sock.settimeout(20.0) # Le damos 20 segundos de paciencia
        sock.connect(addr)
        
        request = (
            "POST /transcribir HTTP/1.1\r\n"
            "Host: " + config.SERVIDOR + ":" + str(config.PUERTO) + "\r\n"
            "Content-Type: audio/wav\r\n"
            "Content-Length: " + str(tam) + "\r\n\r\n"
        ).encode()
        
        sock.write(request)
        
        # Leemos y enviamos el audio en pedacitos pequeños de 512 bytes
        with open("audio.wav", "rb") as f:
            buf = bytearray(512)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                sock.write(buf[:n])
        
        respuesta = sock.read(2048).decode()
        sock.close()
        gc.collect()
        
        # Cortamos la cabecera HTTP para quedarnos solo con el JSON
        cuerpo = respuesta.split("\r\n\r\n", 1)[1]
        datos = ujson.loads(cuerpo)
        texto = datos['text']
        print("Escuché:", texto)
        
    except Exception as e:
        print("Error transcribiendo (Conexión caída):", e)
        return None

    gc.collect()

    # --- ENVIAMOS EL TEXTO A LA IA ---
    try:
        respuesta_ia = preguntar(texto)
    except Exception as e:
        print("Error en preguntar:", e)
        return None

    return respuesta_ia


def preguntar(texto):
    gc.collect()

    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
        '¿': '', '?': '', '¡': '', '!': '',
        ',': '', '.': '', ':': '', ';': '',
        '"': '', "'": '', '\n': ' ', '\r': ''
    }

    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)
    texto_limpio = texto_limpio.strip()
    print("Texto limpio:", repr(texto_limpio))

    gc.collect()

    try:
        url = "http://" + config.SERVIDOR + ":" + str(config.PUERTO) + "/preguntar"
        body = ujson.dumps({"texto": texto_limpio})
        # Le damos un timeout muy generoso por si Llama 3 tarda en pensar
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=30)
        datos = resp.json()
        resp.close()
        return datos['choices'][0]['message']['content']
    except Exception as e:
        print("Error al conectar con la IA:", e)
        return None


def hablar(texto):
    import reproductor
    gc.collect()

    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)

    try:
        url = "http://" + config.SERVIDOR + ":" + str(config.PUERTO) + "/hablar"
        body = ujson.dumps({"texto": texto_limpio})
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=60)
        
        with open("respuesta.wav", "wb") as f:
            f.write(resp.content)
        resp.close()
        gc.collect()

        reproductor.reproducir("respuesta.wav")

    except Exception as e:
        print("Error al descargar voz:", e)