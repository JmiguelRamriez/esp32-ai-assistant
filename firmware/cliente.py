import usocket
import urequests
import ssl
import config
import grabar
import ujson
import os
import gc
import pantalla

def escuchar_y_preguntar(boton):
    """
    Coordina el flujo completo: 
    1. Graba el audio.
    2. Envía el WAV al servidor por Sockets puros usando HTTP POST fragmentado 
       (Chunked / Multipart manual) para no agotar la RAM de MicroPython.
    3. Retorna la respuesta generada por la IA como texto.
    """
    # 1. Grabamos el audio desde el I2S(1)
    grabar.grabar(boton)
    gc.collect()

    pantalla.mostrar_pensando()
    print("Memoria libre:", gc.mem_free())
    
    dominio = config.SERVIDOR.strip()
    
    try:
        tam = os.stat("audio.wav")[6]
        print(f"Subiendo {tam} bytes por socket manual...")

        # 2. Configuración de conexión segura para la transcripción
        addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(30.0) 
        
        sock.connect(addr)
        if config.PUERTO == 443:
            sock = ssl.wrap_socket(sock, server_hostname=dominio)
            
        # Petición HTTP/1.0 para cerrar la conexión al terminar
        request = (
            "POST /transcribir HTTP/1.0\r\n"
            "Host: " + dominio + "\r\n"
            "Content-Type: audio/wav\r\n"
            "Content-Length: " + str(tam) + "\r\n"
            "Connection: close\r\n\r\n"
        ).encode()
        
        sock.write(request)
        
        # Enviamos el archivo por pedazos (chunks) para no saturar la RAM
        with open("audio.wav", "rb") as f:
            buf = bytearray(1024)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                
                chunk = buf[:n]
                escrito = 0
                while escrito < n:
                    res = sock.write(chunk[escrito:])
                    if res:
                        escrito += res
                        
        print("Audio enviado, esperando respuesta...")
        
        # Leemos la respuesta del servidor
        respuesta_bytes = b""
        while True:
            try:
                chunk = sock.read(512)
                if not chunk:
                    break
                respuesta_bytes += chunk
            except:
                break
                
        sock.close()
        
        # Extraemos el texto de la transcripción
        respuesta = respuesta_bytes.decode('utf-8')
        gc.collect()
        
        inicio = respuesta.find('{')
        fin = respuesta.rfind('}') + 1
        
        if inicio != -1 and fin != -1:
            cuerpo = respuesta[inicio:fin]
            datos = ujson.loads(cuerpo)
            texto = datos.get('text', '')
            print("Escuché:", texto)
        else:
            print("Error: El servidor no devolvió un JSON.")
            return None
            
    except Exception as e:
        print("Error en socket manual:", e)
        return None

    gc.collect()

    # 3. Consultamos a la IA
    try:
        respuesta_ia = preguntar(texto)
    except Exception as e:
        print("Error en preguntar:", e)
        return None

    return respuesta_ia


def preguntar(texto):
    """
    Realiza una petición HTTP POST al endpoint /preguntar del backend.
    Envia la transcripción de voz para recibir la respuesta cognitiva del LLM.
    """
    gc.collect()

    # Limpiamos caracteres que rompen la estructura del JSON
    reemplazos = {
        '"': '', "'": '', '\n': ' ', '\r': ''
    }

    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)
    texto_limpio = texto_limpio.strip()
    
    print("Texto limpio para IA:", repr(texto_limpio))

    try:
        url = "https://" + config.SERVIDOR.strip() + "/preguntar"
        
        # FIX: Codificamos a bytes UTF-8 para un conteo de longitud exacto
        body = ujson.dumps({"texto": texto_limpio}).encode('utf-8')
        
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=30)
        datos = resp.json()
        resp.close()
        return datos['choices'][0]['message']['content']
    except Exception as e:
        print("Error al conectar con la IA:", e)
        return None


def hablar(texto):
    """
    Toma el texto de respuesta devuelto por la IA, solicita al backend un archivo 
    de audio WAV generado con TTS, lo descarga directamente en memoria flash 
    y luego invoca la función de reproducción DAC.
    """
    import reproductor
    gc.collect()

    # Limpieza para el envío a la síntesis de voz
    reemplazos = {
        '"': '', "'": '', '\n': ' ', '\r': ' '
    }
    
    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)

    try:
        url = "https://" + config.SERVIDOR.strip() + "/hablar"
        
        # FIX: Codificamos a bytes UTF-8 para evitar errores de delimitador JSON
        body = ujson.dumps({"texto": texto_limpio}).encode('utf-8')
        
        print("Descargando audio de respuesta...")
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=60)
        
        # Guardamos el audio por bloques directos a la memoria flash
        with open("respuesta.wav", "wb") as f:
            while True:
                chunk = resp.raw.read(1024)
                if not chunk:
                    break
                f.write(chunk)
                
        resp.close()
        gc.collect()

        print("Reproduciendo...")
        reproductor.reproducir("respuesta.wav")

    except Exception as e:
        print("Error al descargar voz:", e)