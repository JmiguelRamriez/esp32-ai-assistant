import usocket
import config
import grabar
import ujson
import os
import gc

def escuchar_y_preguntar():
    grabar.grabar()
    gc.collect()
    
    tam = os.stat("audio.wav")[6]
    addr = (config.SERVIDOR, config.PUERTO)
    sock = usocket.socket()
    sock.connect(addr)
    
    request = (
        "POST /transcribir HTTP/1.1\r\n"
        "Host: " + config.SERVIDOR + "\r\n"
        "Content-Type: audio/wav\r\n"
        "Content-Length: " + str(tam) + "\r\n\r\n"
    ).encode()
    
    sock.write(request)
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
    
    try:
        cuerpo = respuesta.split("\r\n\r\n", 1)[1]
        datos = ujson.loads(cuerpo)
        texto = datos['text']
        print("Escuché:", texto)
    except Exception as e:
        print("Error al parsear:", e)
        print("Respuesta raw:", respuesta)
        return
    
    print("Memoria libre:", gc.mem_free())
    try:
        respuesta_ia = preguntar(texto)
        print("Respuesta:", respuesta_ia)
    except Exception as e:
        print("Error en preguntar:", e)

def preguntar(texto):
    import ujson
    gc.collect()
    
    # Limpiamos el salto de línea que rompe el JSON
    texto_limpio = texto.strip()
    print("Texto limpio a enviar:", repr(texto_limpio))

    addr = (config.SERVIDOR, config.PUERTO)
    sock = usocket.socket()
    sock.connect(addr)
    
    # Empaquetamos todo de forma segura
    payload = {"texto": texto_limpio}
    cuerpo = ujson.dumps(payload).encode('utf-8')
    
    header = (
        "POST /preguntar HTTP/1.1\r\n"
        "Host: " + config.SERVIDOR + "\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: " + str(len(cuerpo)) + "\r\n\r\n"
    ).encode()
    
    sock.write(header)
    sock.write(cuerpo)
    respuesta = sock.read(2048).decode()
    sock.close()
    
    print("RAW:", respuesta)
    
    try:
        cuerpo_resp = respuesta.split("\r\n\r\n", 1)[1]
        datos = ujson.loads(cuerpo_resp)
        return datos['choices'][0]['message']['content']
    except Exception as e:
        print("Error extrayendo la respuesta del servidor:", e)
        return None