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
    return respuesta_ia

def preguntar(texto):
    import gc
    gc.collect()
    
    # 1. Diccionario de reemplazos (El "filtro" limpiador)
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
        '¿': '', '?': '', '¡': '', '!': '',
        ',': '', '.': '', ':': '', ';': '',
        '"': '', "'": '', '\n': ' ', '\r': ''
    }
    
    # 2. Limpiamos el texto letra por letra
    texto_limpio = texto
    for original, nuevo in reemplazos.items():
        texto_limpio = texto_limpio.replace(original, nuevo)
        
    texto_limpio = texto_limpio.strip() # Quitamos espacios en blanco a los lados
    print("Texto limpio a enviar:", repr(texto_limpio))

    # 3. Continuamos con tu código original de conexión
    addr = (config.SERVIDOR, config.PUERTO)
    sock = usocket.socket()
    sock.connect(addr)
    
    cuerpo = ('{"texto":"' + texto_limpio + '"}').encode('utf-8')
    
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
    
    # Extraer la respuesta
    try:
        cuerpo_resp = respuesta.split("\r\n\r\n", 1)[1]
        import ujson
        datos = ujson.loads(cuerpo_resp)
        return datos['choices'][0]['message']['content']
    except Exception as e:
        print("Error en preguntar:", e)
        return None