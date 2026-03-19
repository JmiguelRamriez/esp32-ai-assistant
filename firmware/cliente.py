import usocket
import urequests
import ssl  # <-- NUEVO: Librería necesaria para conectarse a Render
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

    # --- ENVÍO DE AUDIO POR SOCKETS ENCRIPTADOS (Para la Nube) ---
    try:
        tam = os.stat("audio.wav")[6]
        
        # Resolvemos la IP de Render
        addr = usocket.getaddrinfo(config.SERVIDOR, config.PUERTO)[0][-1]
        
        sock = usocket.socket()
        sock.settimeout(20.0)
        sock.connect(addr)
        
        # --- LA MAGIA: Envolvemos el socket en SSL para que Render lo acepte ---
        if config.PUERTO == 443:
            sock = ussl.wrap_socket(sock, server_hostname=config.SERVIDOR)
        
        # Quitamos el puerto de la cabecera Host, Render prefiere solo el dominio
        request = (
            "POST /transcribir HTTP/1.1\r\n"
            "Host: " + config.SERVIDOR + "\r\n"
            "Content-Type: audio/wav\r\n"
            "Content-Length: " + str(tam) + "\r\n"
            "Connection: close\r\n\r\n"
        ).encode()
        
        sock.write(request)
        
        with open("audio.wav", "rb") as f:
            buf = bytearray(512)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                sock.write(buf[:n])
        
        # Leemos la respuesta de forma segura
        respuesta_bytes = b""
        while True:
            chunk = sock.read(512)
            if not chunk:
                break
            respuesta_bytes += chunk
            
        sock.close()
        respuesta = respuesta_bytes.decode()
        gc.collect()
        
        cuerpo = respuesta.split("\r\n\r\n", 1)[1]
        datos = ujson.loads(cuerpo)
        texto = datos['text']
        print("Escuché:", texto)
        
    except Exception as e:
        print("Error transcribiendo (Conexión caída):", e)
        return None

    gc.collect()

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
        # --- CAMBIO: Usamos "https://" y quitamos la inserción del puerto ---
        url = "https://" + config.SERVIDOR + "/preguntar"
        
        body = ujson.dumps({"texto": texto_limpio})
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
        # --- CAMBIO: Usamos "https://" y quitamos la inserción del puerto ---
        url = "https://" + config.SERVIDOR + "/hablar"
        
        body = ujson.dumps({"texto": texto_limpio})
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=60)
        
        with open("respuesta.wav", "wb") as f:
            f.write(resp.content)
        resp.close()
        gc.collect()

        reproductor.reproducir("respuesta.wav")

    except Exception as e:
        print("Error al descargar voz:", e)