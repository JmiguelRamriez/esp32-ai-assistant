import usocket
import ssl
import config
import grabar
import ujson
import os
import gc
import pantalla
import urequests

def escuchar_y_preguntar(boton):
    grabar.grabar(boton)
    gc.collect()

    pantalla.mostrar_pensando()
    print("Memoria libre:", gc.mem_free())
    
    dominio = config.SERVIDOR.strip()
    
    try:
        tam = os.stat("audio.wav")[6]
        print(f"Subiendo {tam} bytes por socket manual...")

        addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(30.0) 
        
        sock.connect(addr)
        if config.PUERTO == 443:
            sock = ssl.wrap_socket(sock, server_hostname=dominio)
            
        request = (
            "POST /transcribir HTTP/1.0\r\n"
            "Host: " + dominio + "\r\n"
            "Content-Type: audio/wav\r\n"
            "Content-Length: " + str(tam) + "\r\n"
            "Connection: close\r\n\r\n"
        ).encode()
        
        sock.write(request)
        
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
        
        respuesta_bytes = b""
        while True:
            try:
                chunk = sock.read(512)
                if not chunk:
                    break
                respuesta_bytes += chunk
            except Exception as e:
                break
                
        sock.close()
        
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
            print("Respuesta cruda:", respuesta)
            return None
            
    except Exception as e:
        print("Error en socket manual:", e)
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

    try:
        url = "https://" + config.SERVIDOR.strip() + "/preguntar"
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
        url = "https://" + config.SERVIDOR.strip() + "/hablar"
        body = ujson.dumps({"texto": texto_limpio})
        
        print("Descargando audio de respuesta...")
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=60)
        
        # Leemos por bloques directos al archivo para no saturar la RAM
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