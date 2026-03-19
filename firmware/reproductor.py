from machine import DAC, Pin
import time
import struct
import os
import gc

# LOS PINES SE INICIALIZAN AQUÍ AFUERA (Una sola vez)
dac_l = DAC(Pin(25))
dac_r = DAC(Pin(26))

def reproducir(nombre="respuesta.wav"):
    gc.collect()
    try:
        tamano = os.stat(nombre)[6]
        print(f"Tamaño del audio descargado: {tamano} bytes")
        
        if tamano < 1000:
            print("El archivo es demasiado pequeño, no es un audio válido.")
            return

        with open(nombre, "rb") as f:
            header = f.read(44)
            sample_rate = struct.unpack('<I', header[24:28])[0]
            print("Sample rate detectado:", sample_rate)

            retraso_teorico = 1000000 // sample_rate 
            delay_us = retraso_teorico - 45 
            
            if delay_us < 0: 
                delay_us = 0

            print(f"Reproduciendo con delay compensado: {delay_us} us")

            buf = bytearray(512)
            while True:
                n = f.readinto(buf)
                if n == 0:
                    break
                
                for i in range(n):
                    val = buf[i]
                    dac_l.write(val)
                    dac_r.write(val)
                    time.sleep_us(delay_us)

    except Exception as e:
        print("Error en reproductor:", e)
        
    print("Reproducción terminada")