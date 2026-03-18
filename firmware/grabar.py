from machine import Pin, I2S
import struct
import time

def grabar(nombre="audio.wav", segundos=10):
    rate = 8000
    bits = 16
    canales = 1
    muestras = rate * segundos * canales * (bits // 8)
    
    # Encabezado WAV
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', muestras + 36, b'WAVE',
        b'fmt ', 16, 1, canales, rate,
        rate * canales * (bits//8), canales * (bits//8), bits,
        b'data', muestras
    )
    
    mic = I2S(0, sck=Pin(32), ws=Pin(27), sd=Pin(33),
        mode=I2S.RX, bits=bits, format=I2S.MONO,
        rate=rate, ibuf=4096)
    
    print("Grabando...")
    with open(nombre, 'wb') as f:
        f.write(header)
        buf = bytearray(1024)
        grabado = 0
        while grabado < muestras:
            mic.readinto(buf)
            f.write(buf)
            grabado += len(buf)
    
    mic.deinit()
    print("Listo:", nombre)