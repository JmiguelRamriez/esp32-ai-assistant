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
from machine import Pin, DAC
import time


time.sleep(2)
wifi.conectar()
pantalla.iniciar()
pantalla.sincronizar_hora()

boton = Pin(14, Pin.IN, Pin.PULL_UP)

_t = 0
_ultimo_habla = time.time()
_ultimo_wifi_check = time.ticks_ms()

pantalla.mostrar_reposo()
print("Esperando: di 'Luna'...")

def beep_confirmacion():
    """Genera un beep corto (880Hz, 100ms) usando DAC en pin 25 para feedback."""
    try:
        dac = DAC(Pin(25))
        for _ in range(88):
            dac.write(255)
            time.sleep_us(568)
            dac.write(0)
            time.sleep_us(568)
        # IMPORTANTE: Liberar el DAC escribiendo 0 para no causar ruido estático continuo
        dac.write(0)
    except Exception as e:
        print("Error DAC:", e)


def verificar_wake_word():
    try:
        tam = os.stat("wake.wav")[6]
        dominio = config.SERVIDOR.strip()
        addr = usocket.getaddrinfo(dominio, config.PUERTO, 0, usocket.SOCK_STREAM)[0][-1]
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(20.0)
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
                
                chunk = buf[:n]
                escrito = 0
                while escrito < n:
                    res = sock.write(chunk[escrito:])
                    if res:
                        escrito += res

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
    if modo_wake:
        beep_confirmacion()
        
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
    
    # Prioridad 1: boton fisico
    if boton.value() == 0:
        time.sleep(0.05)
        if boton.value() == 0:
            print("Boton presionado")
            interactuar()
            _t = 0
            pantalla.mostrar_reposo()
            
    # Prioridad 2: wake word (si han pasado 4 segs desde la ultima vez que hablo)
    elif time.time() - _ultimo_habla > 4:
        if grabar.grabar_wake_con_vad("wake.wav", umbral=1200, duracion_ms=2500, timeout_ms=3000):
            gc.collect()
            if verificar_wake_word():
                print("¡Wake word 'Luna' detectado!")
                interactuar(modo_wake=True)
                _t = 0
                pantalla.mostrar_reposo()
        # Animar reposo
        _t += 1
        pantalla.tick_reposo(_t)
    else:
        _t += 1
        pantalla.tick_reposo(_t)
        time.sleep(0.3)
        continue

    # Verificar WiFi cada 30 segundos
    if time.ticks_diff(time.ticks_ms(), _ultimo_wifi_check) > 30000:
        _ultimo_wifi_check = time.ticks_ms()
        wifi.verificar_y_reconectar()

    time.sleep(0.05)