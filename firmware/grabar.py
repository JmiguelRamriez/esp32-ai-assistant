from machine import Pin, I2S
import struct
import time

# ── Micrófono persistente ──────────────────────────────────────────────────────
# Lo mantenemos siempre abierto para evitar interferencia en el bus I2C
# cada vez que se inicializa/destruye el periférico I2S.
_mic = None

def _get_mic():
    global _mic
    if _mic is None:
        _mic = I2S(1, sck=Pin(32), ws=Pin(27), sd=Pin(33),
                   mode=I2S.RX, bits=16, format=I2S.MONO,
                   rate=8000, ibuf=4096)
    return _mic


# ── Grabación principal (botón) ────────────────────────────────────────────────

def grabar(boton, nombre="audio.wav"):
    """
    Graba audio mientras el botón esté presionado y lo guarda como WAV.
    """
    rate    = 8000
    bits    = 16
    canales = 1

    mic = _get_mic()
    print("Grabando (mantén presionado el botón)...")

    with open(nombre, 'wb') as f:
        f.write(bytearray(44))

        buf     = bytearray(1024)
        grabado = 0

        while boton.value() == 0:
            n = mic.readinto(buf)
            f.write(buf[:n])
            grabado += n

        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', grabado + 36, b'WAVE',
            b'fmt ', 16, 1, canales, rate,
            rate * canales * (bits // 8), canales * (bits // 8), bits,
            b'data', grabado
        )
        f.seek(0)
        f.write(header)

    print("Listo:", nombre, "- Bytes grabados:", grabado)


# ── Detección de voz (VAD simple) ─────────────────────────────────────────────

def hay_voz(umbral=500):
    """
    Lee una pequeña muestra del micrófono y devuelve True si la
    amplitud máxima supera el umbral. Ajusta según tu entorno.
    """
    mic = _get_mic()
    buf = bytearray(512)
    mic.readinto(buf)

    maximo = 0
    for i in range(0, len(buf) - 1, 2):
        val = buf[i] | (buf[i + 1] << 8)
        if val > 32767:
            val -= 65536
        if abs(val) > maximo:
            maximo = abs(val)

    return maximo > umbral


# ── Grabación corta para wake word ────────────────────────────────────────────

def grabar_wake(nombre="wake.wav", duracion_ms=2000):
    """
    Graba un audio corto de duración fija para verificar el wake word.
    """
    rate     = 8000
    bits     = 16
    canales  = 1
    objetivo = int(rate * duracion_ms / 1000) * 2

    mic = _get_mic()

    with open(nombre, 'wb') as f:
        f.write(bytearray(44))

        buf     = bytearray(1024)
        grabado = 0

        while grabado < objetivo:
            n = mic.readinto(buf)
            f.write(buf[:n])
            grabado += n

        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', grabado + 36, b'WAVE',
            b'fmt ', 16, 1, canales, rate,
            rate * canales * (bits // 8), canales * (bits // 8), bits,
            b'data', grabado
        )
        f.seek(0)
        f.write(header)

def grabar_wake_con_vad(nombre="wake.wav", umbral=1500, duracion_ms=2500, timeout_ms=500):
    """
    Escucha por hasta timeout_ms. Si detecta voz, graba y retorna True.
    Si no detecta nada, retorna False sin bloquear.
    """
    rate    = 8000
    bits    = 16
    canales = 1
    objetivo = int(rate * duracion_ms / 1000) * 2

    mic = _get_mic()
    buf = bytearray(512)

    # Intentar detectar voz durante el timeout
    intentos = timeout_ms // 10
    voz_detectada = False
    for _ in range(intentos):
        mic.readinto(buf)
        maximo = 0
        for i in range(0, len(buf) - 1, 2):
            val = buf[i] | (buf[i + 1] << 8)
            if val > 32767: val -= 65536
            if abs(val) > maximo: maximo = abs(val)
        if maximo > umbral:
            voz_detectada = True
            break

    if not voz_detectada:
        return False

    # Voz detectada — grabar incluyendo el chunk actual
    with open(nombre, 'wb') as f:
        f.write(bytearray(44))
        grabado = 0
        f.write(buf)
        grabado += len(buf)

        buf2 = bytearray(1024)
        while grabado < objetivo:
            n = mic.readinto(buf2)
            f.write(buf2[:n])
            grabado += n

        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', grabado + 36, b'WAVE',
            b'fmt ', 16, 1, canales, rate,
            rate * canales * (bits // 8), canales * (bits // 8), bits,
            b'data', grabado)
        f.seek(0)
        f.write(header)


    return True