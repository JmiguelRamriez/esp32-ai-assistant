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
    gc.collect()

    pantalla.mostrar_pensando()
    print("Memoria libre:", gc.mem_free())

    try:
        tam = os.stat("audio.wav")[6]
        gc.collect()

        url = "https://" + config.SERVIDOR + "/transcribir"
        resp = urequests.post(
            url,
            data=open("audio.wav", "rb"),
            headers={
                "Content-Type": "audio/wav",
                "Content-Length": str(tam)
            },
            timeout=60
        )
        datos = resp.json()
        resp.close()
        texto = datos['text']
        print("Escuché:", texto)
    except Exception as e:
        print("Error transcribiendo:", e)
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
        url = "https://" + config.SERVIDOR + "/preguntar"
        body = ujson.dumps({"texto": texto_limpio})
        resp = urequests.post(url, data=body, headers={"Content-Type": "application/json"})
        datos = resp.json()
        resp.close()
        return datos['choices'][0]['message']['content']
    except Exception as e:
        print("Error en preguntar:", e)
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
        url = "https://" + config.SERVIDOR + "/hablar"
        body = ujson.dumps({"texto": texto_limpio})
        resp = urequests.post(url, data=body,
                              headers={"Content-Type": "application/json"})
        with open("respuesta.wav", "wb") as f:
            f.write(resp.content)
        resp.close()
        gc.collect()

        reproductor.reproducir("respuesta.wav")

    except Exception as e:
        print("Error en TTS:", e)