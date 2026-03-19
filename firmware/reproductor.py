from machine import DAC, Pin
import time
import struct
import os
import gc

# LOS PINES SE INICIALIZAN AQUÍ AFUERA (Una sola vez)
# Usaremos DAC (Digital to Analog Converter) integrado en ESP32
# Pines 25 y 26 son los habilitados para DAC r y l (Canal derecho e izquierdo)
dac_l = DAC(Pin(25))
dac_r = DAC(Pin(26))

def reproducir(nombre="respuesta.wav"):
    """
    Reproduce un archivo WAV en los pines DAC del ESP32.
    El audio debe estar a 8 bits sin signo (PCM unsigned 8-bit) para 
    ser compatible con el DAC integrado del ESP32.
    """
    gc.collect() # Liberar RAM antes de iniciar la reproducción
    try:
        tamano = os.stat(nombre)[6]
        print(f"Tamaño del audio descargado: {tamano} bytes")
        
        # Validación de que se tenga un audio sustancial y no un error vacío
        if tamano < 1000:
            print("El archivo es demasiado pequeño, no es un audio válido.")
            return

        with open(nombre, "rb") as f:
            # Leer cabecera WAV
            header = f.read(44)
            # Extraer el Sample Rate del byte 24-28
            sample_rate = struct.unpack('<I', header[24:28])[0]
            print("Sample rate detectado:", sample_rate)

            # Cálculo de tiempo de espera entre cada muestra en microsegundos
            # Se compensa por el tiempo de ejecución del propio ciclo de Python (~45us)
            retraso_teorico = 1000000 // sample_rate 
            delay_us = retraso_teorico - 45 
            
            if delay_us < 0: 
                delay_us = 0

            print(f"Reproduciendo con delay compensado: {delay_us} us")

            # Buffer de lectura en trozos para no consumir toda la RAM
            buf = bytearray(512)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                
                # Escribir cada byte extraído a ambos canales DAC
                for i in range(n):
                    val = buf[i]
                    dac_l.write(val)
                    dac_r.write(val)
                    time.sleep_us(delay_us)

    except Exception as e:
        print("Error en reproductor:", e)
        
    print("Reproducción terminada")