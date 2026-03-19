from machine import Pin, I2S
import struct
import time

def grabar(boton, nombre="audio.wav"):
    rate = 8000
    bits = 16
    canales = 1
    
    # ESTE ES EL CAMBIO CLAVE: I2S(1)
    mic = I2S(1, sck=Pin(32), ws=Pin(27), sd=Pin(33),
        mode=I2S.RX, bits=bits, format=I2S.MONO,
        rate=rate, ibuf=4096)
    
    print("Grabando (mantén presionado el botón)...")
    
    with open(nombre, 'wb') as f:
        f.write(bytearray(44))
        
        buf = bytearray(1024)
        grabado = 0
        
        while boton.value() == 0:
            num_bytes = mic.readinto(buf)
            f.write(buf[:num_bytes])
            grabado += num_bytes
            
        muestras = grabado
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', muestras + 36, b'WAVE',
            b'fmt ', 16, 1, canales, rate,
            rate * canales * (bits//8), canales * (bits//8), bits,
            b'data', muestras
        )
        
        f.seek(0)
        f.write(header)
    
    mic.deinit()
    print("Listo:", nombre, "- Bytes grabados:", grabado)