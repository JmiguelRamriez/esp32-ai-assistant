from machine import DAC, Pin
import time
import struct

dac_l = DAC(Pin(25))
dac_r = DAC(Pin(26))

def reproducir(nombre="respuesta.wav"):
    with open(nombre, "rb") as f:
        # Leer header WAV para obtener sample rate
        header = f.read(44)
        sample_rate = struct.unpack('<I', header[24:28])[0]
        print("Sample rate:", sample_rate)

        delay_us = 1000000 // sample_rate  # 125µs para 8kHz

        buf = bytearray(256)
        while True:
            n = f.readinto(buf)
            if n == 0:
                break
            for i in range(n):
                dac_l.write(buf[i])
                dac_r.write(buf[i])
                time.sleep_us(delay_us)

    print("Reproducción terminada")