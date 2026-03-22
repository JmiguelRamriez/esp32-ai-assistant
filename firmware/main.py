import pantalla
import wifi
import cliente
import grabar
import gc
import os
import usocket
import ssl
import ujson
import config
from machine import Pin
import time

time.sleep(2)
wifi.conectar()
pantalla.iniciar()
pantalla.sincronizar_hora()

boton = Pin(14, Pin.IN, Pin.PULL_UP)

_t = 0
_ultimo_habla = time.time()  # Inicializar con tiempo real para evitar bug con NTP

pantalla.mostrar_reposo()
print("Esperando: botón o di 'Luna'...")


def verificar_wake_word():
    """Envía wake.wav al servidor y devuelve True si detectó 'Luna'."""
    try:
        tam = os.stat("wake.wav")[6]
        dominio = config.SERVIDOR.strip()
        addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(15.0)
        sock.connect(addr)
        if config.PUERTO == 443:
            sock = ssl.wrap_socket(sock, server_hostname=dominio)

        req = (
            "POST /despertar HTTP/1.0\r\n"
            "Host: " + dominio + "\r\n"
            "Content-Type: audio/wav\r\n"
            "Content-Length: " + str(tam) + "\r\n"
            "Connection: close\r\n\r\n"
        ).encode()
        sock.write(req)

        with open("wake.wav", "rb") as f:
            buf = bytearray(1024)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                sock.write(buf[:n])

        resp = b""
        while True:
            chunk = sock.read(512)
            if not chunk:
                break
            resp += chunk
        sock.close()

        inicio = resp.find(b'{')
        fin = resp.rfind(b'}') + 1
        if inicio != -1 and fin > inicio:
            datos = ujson.loads(resp[inicio:fin])
            return datos.get('detectado', False)
    except Exception as e:
        print("Error wake word:", e)
    return False


def interactuar(modo_wake=False):
    global _ultimo_habla
    pantalla.mostrar_escuchando()
    gc.collect()
    try:
        if modo_wake:
            respuesta = cliente.escuchar_y_preguntar_wake()
        else:
            respuesta = cliente.escuchar_y_preguntar(boton)
        if respuesta:
            pantalla.mostrar_hablando()
            print("IA:", respuesta)
            cliente.hablar(respuesta)
        else:
            print("Sin respuesta.")
    except Exception as e:
        print("Error:", e)
    _ultimo_habla = time.time()


while True:
    # ── Prioridad 1: botón físico ─────────────────────────
    if boton.value() == 0:
        time.sleep(0.05)
        if boton.value() == 0:
            print("Botón presionado")
            interactuar()
            _t = 0
            pantalla.mostrar_reposo()

    # ── Prioridad 2: wake word ────────────────────────────
    elif time.time() - _ultimo_habla > 4:
        if grabar.grabar_wake_con_vad("wake.wav", umbral=300, duracion_ms=2500, timeout_ms=3000):
            gc.collect()
            if verificar_wake_word():
                print("¡Wake word 'Luna' detectado!")
                interactuar(modo_wake=True)
                _t = 0
                pantalla.mostrar_reposo()
        # Animar pantalla tanto si detectó voz como si no
        _t += 1
        pantalla.tick_reposo(_t)

    # ── Reposo: animar pantalla ──────────────────────────
    else:
        _t += 1
        pantalla.tick_reposo(_t)
        time.sleep(0.3)
        continue

    time.sleep(0.05)