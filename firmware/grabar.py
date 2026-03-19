from machine import Pin, I2S
import struct
import time

def grabar(boton, nombre="audio.wav"):
    """
    Graba audio desde el micrófono I2S mientras el botón esté presionado
    y lo guarda en un archivo WAV en el sistema de archivos (flash).
    """
    # Configuración de audio WAV: 8000 Hz, 16 bits, Mono
    rate = 8000
    bits = 16
    canales = 1
    
    # Inicialización del micrófono I2S en el bus 1
    # Pines: SCK (Clock), WS (Word Select / LRCLK), SD (Serial Data)
    mic = I2S(1, sck=Pin(32), ws=Pin(27), sd=Pin(33),
        mode=I2S.RX, bits=bits, format=I2S.MONO,
        rate=rate, ibuf=4096)
    
    print("Grabando (mantén presionado el botón)...")
    
    # Abrir archivo para escritura binaria
    with open(nombre, 'wb') as f:
        # Reservar 44 bytes para la cabecera WAV que se llenará al final
        f.write(bytearray(44))
        
        buf = bytearray(1024) # Buffer de lectura I2S
        grabado = 0
        
        # Leer desde I2S y escribir a flash mientras el botón siga presionado
        while boton.value() == 0:
            num_bytes = mic.readinto(buf)
            f.write(buf[:num_bytes])
            grabado += num_bytes
            
        muestras = grabado
        
        # Construir la cabecera WAV estándar con struct
        # Formato RIFF/WAVE, especificando frecuencias y tamaño de datos
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', muestras + 36, b'WAVE',
            b'fmt ', 16, 1, canales, rate,
            rate * canales * (bits//8), canales * (bits//8), bits,
            b'data', muestras
        )
        
        # Volver al inicio del archivo y escribir la cabecera correcta
        f.seek(0)
        f.write(header)
    
    # Desinicializar I2S para liberar recursos de hardware
    mic.deinit()
    print("Listo:", nombre, "- Bytes grabados:", grabado)