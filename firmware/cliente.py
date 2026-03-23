import usocket
import urequests
import ssl
import config
import grabar
import ujson
import os
import gc
import pantalla
import time

def escuchar_y_preguntar_wake():
    import grabar as _grabar
    class FakeBoton:
        def __init__(self): 
            self._fin = time.ticks_add(time.ticks_ms(), 4000)
        def value(self): 
            return 0 if time.ticks_diff(self._fin, time.ticks_ms()) > 0 else 1

    _grabar.grabar(FakeBoton(), "audio.wav")
    gc.collect()

    pantalla.mostrar_pensando()
    dominio = config.SERVIDOR.strip()
    texto = ""

    for intento in range(2):
        try:
            tam = os.stat("audio.wav")[6]
            addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.settimeout(20.0)
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
                    if n == 0: break
                    escrito = 0
                    chunk = buf[:n]
                    while escrito < n:
                        res = sock.write(chunk[escrito:])
                        if res: escrito += res

            respuesta_bytes = b""
            while True:
                try:
                    chunk = sock.read(512)
                    if not chunk: break
                    respuesta_bytes += chunk
                except: break
            sock.close()

            respuesta = respuesta_bytes.decode('utf-8')
            gc.collect()
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}') + 1
            if inicio != -1 and fin != -1:
                datos = ujson.loads(respuesta[inicio:fin])
                texto = datos.get('text', '')
                print("Escuché:", texto)
                break
            else:
                raise Exception("JSON invalido")
        except Exception as e:
            print(f"Error transcribiendo wake (Intento {intento+1}):", e)
            if intento == 1:
                pantalla.mostrar_error_servidor()
                return None
            time.sleep(2)

    gc.collect()
    return preguntar(texto)


def escuchar_y_preguntar(boton):
    grabar.grabar(boton)
    gc.collect()
    pantalla.mostrar_pensando()
    dominio = config.SERVIDOR.strip()
    texto = ""

    for intento in range(2):
        try:
            tam = os.stat("audio.wav")[6]
            addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.settimeout(20.0) 
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
                    if n == 0: break
                    chunk = buf[:n]
                    escrito = 0
                    while escrito < n:
                        res = sock.write(chunk[escrito:])
                        if res: escrito += res
                            
            respuesta_bytes = b""
            while True:
                try:
                    chunk = sock.read(512)
                    if not chunk: break
                    respuesta_bytes += chunk
                except: break
            sock.close()
            
            respuesta = respuesta_bytes.decode('utf-8')
            gc.collect()
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}') + 1
            
            if inicio != -1 and fin != -1:
                datos = ujson.loads(respuesta[inicio:fin])
                texto = datos.get('text', '')
                print("Escuché:", texto)
                break
            else:
                raise Exception("JSON invalido")
        except Exception as e:
            print(f"Error en socket manual (Intento {intento+1}):", e)
            if intento == 1:
                pantalla.mostrar_error_servidor()
                return None
            time.sleep(2)

    gc.collect()
    try:
        respuesta_ia = preguntar(texto)
    except Exception as e:
        print("Error en preguntar:", e)
        return None
    return respuesta_ia


def preguntar(texto):
    gc.collect()
    reemplazos = {'"': '', "'": '', '\n': ' ', '\r': ''}
    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)
    texto_limpio = texto_limpio.strip()

    for intento in range(2):
        try:
            url = "https://" + config.SERVIDOR.strip() + "/preguntar"
            body = ujson.dumps({"texto": texto_limpio}).encode('utf-8')
            resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=20.0)
            datos = resp.json()
            resp.close()
            return datos['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error al conectar con la IA (Intento {intento+1}):", e)
            if intento == 1:
                pantalla.mostrar_error_servidor()
                return None
            time.sleep(2)
    return None


def hablar(texto):
    import reproductor
    gc.collect()
    reemplazos = {'"': '', "'": '', '\n': ' ', '\r': ' '}
    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)

    for intento in range(2):
        try:
            url = "https://" + config.SERVIDOR.strip() + "/hablar"
            body = ujson.dumps({"texto": texto_limpio}).encode('utf-8')
            print("Descargando audio de respuesta...")
            resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"}, timeout=20.0)
            
            with open("respuesta.wav", "wb") as f:
                while True:
                    try:
                        chunk = resp.raw.read(1024)
                        if not chunk: break
                        f.write(chunk)
                    except: break
            resp.close()
            gc.collect()
            print("Reproduciendo...")
            reproductor.reproducir("respuesta.wav")
            return
        except Exception as e:
            print(f"Error al descargar voz (Intento {intento+1}):", e)
            if intento == 1:
                pantalla.mostrar_error_servidor()
                return
            time.sleep(2)
