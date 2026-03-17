from machine import Pin, I2C
import sh1106
import math
import time
import random

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3c)
display.poweron()

# ─── Utilidades base (tu estilo) ────────────────────────────

def circulo(cx, cy, r):
    for dy in range(-r, r+1):
        dx = int(math.sqrt(max(0, r*r - dy*dy)))
        display.line(cx-dx, cy+dy, cx+dx, cy+dy, 1)

def elipse(cx, cy, rx, ry):
    for dy in range(-ry, ry+1):
        if ry == 0: continue
        dx = int(rx * math.sqrt(max(0, 1-(dy/ry)**2)))
        display.line(cx-dx, cy+dy, cx+dx, cy+dy, 1)

def elipse_hueca(cx, cy, rx, ry):
    """Solo el contorno de la elipse."""
    steps = max(rx, ry) * 4
    for i in range(steps):
        a = 2 * math.pi * i / steps
        x = int(cx + rx * math.cos(a))
        y = int(cy + ry * math.sin(a))
        if 0 <= x < 128 and 0 <= y < 64:
            display.pixel(x, y, 1)

def ojo(cx, cy, rx, ry, cerrado=False, semicerrado=False):
    """
    Ojo elíptico vertical.
    cerrado      = línea horizontal
    semicerrado  = mitad inferior solamente
    """
    if cerrado:
        display.line(cx-rx, cy, cx+rx, cy, 1)
        display.line(cx-rx, cy+1, cx+rx, cy+1, 1)
    elif semicerrado:
        # Solo mitad inferior de la elipse
        for dy in range(0, ry+1):
            if ry == 0: continue
            dx = int(rx * math.sqrt(max(0, 1-(dy/ry)**2)))
            display.line(cx-dx, cy+dy, cx+dx, cy+dy, 1)
        display.line(cx-rx, cy, cx+rx, cy, 1)
    else:
        elipse(cx, cy, rx, ry)
        # Highlight
        display.pixel(cx-rx//2,   cy-ry//3,   0)
        display.pixel(cx-rx//2-1, cy-ry//3,   0)
        display.pixel(cx-rx//2,   cy-ry//3-1, 0)

def boca_abierta(cx, cy, rx, ry):
    """Elipse con interior negro."""
    elipse(cx, cy, rx, ry)
    irx = max(1, rx-2)
    iry = max(1, ry-2)
    for dy in range(-iry, iry+1):
        dx = int(irx * math.sqrt(max(0, 1-(dy/iry)**2)))
        display.line(cx-dx, cy+dy, cx+dx, cy+dy, 0)

# ─── Transición morph ────────────────────────────────────────

def lerp(a, b, t):
    return a + (b-a)*t

def ease(t):
    return t*t*(3-2*t)

def morph(params_a, params_b, pasos=12, delay_ms=40):
    """
    Interpola suavemente entre dos sets de parámetros.
    Cada set: (cx, cy, rx, ry, cerrado, semicerrado)
    """
    for i in range(pasos+1):
        t  = ease(i/pasos)
        display.fill(0)

        # Ojos
        for lado in ['l', 'r']:
            cx = int(lerp(params_a[f'cx_{lado}'], params_b[f'cx_{lado}'], t))
            cy = int(lerp(params_a[f'cy_{lado}'], params_b[f'cy_{lado}'], t))
            rx = max(1, int(lerp(params_a['rx'], params_b['rx'], t)))
            ry_full = max(1, int(lerp(params_a['ry'], params_b['ry'], t)))
            ap = lerp(params_a['apertura'], params_b['apertura'], t)

            if ap <= 0.08:
                ojo(cx, cy, rx, ry_full, cerrado=True)
            elif ap <= 0.45:
                ry_vis = max(1, int(ry_full * ap * 2))
                ojo(cx, cy, rx, ry_vis, semicerrado=True)
            else:
                ry_vis = max(1, int(ry_full * ap))
                ojo(cx, cy, rx, ry_vis)

        # Boca — solo aparece al acercarse al estado 'hablando'
        boca_t = params_b.get('boca_t', 0.0)
        boca_a = params_a.get('boca_t', 0.0)
        bt = lerp(boca_a, boca_t, t)
        if bt > 0.1:
            bry = max(1, int(8 * bt))
            boca_abierta(64, 50, int(lerp(10, 12, bt)), bry)

        display.show()
        time.sleep_ms(delay_ms)

# ─── Caras ───────────────────────────────────────────────────

# Parámetros de cada cara para el morph
P_REPOSO = {
    'cx_l': 45, 'cy_l': 22,
    'cx_r': 83, 'cy_r': 22,
    'rx': 10,   'ry': 18,
    'apertura': 0.3,
    'boca_t': 0.0,
}
P_ESCUCHANDO = {
    'cx_l': 43, 'cy_l': 22,
    'cx_r': 85, 'cy_r': 22,
    'rx': 11,   'ry': 20,
    'apertura': 1.0,
    'boca_t': 0.0,
}
P_PENSANDO = {
    'cx_l': 45, 'cy_l': 22,
    'cx_r': 83, 'cy_r': 22,
    'rx': 10,   'ry': 18,
    'apertura': 0.2,
    'boca_t': 0.0,
}
P_HABLANDO = {
    'cx_l': 43, 'cy_l': 20,
    'cx_r': 85, 'cy_r': 20,
    'rx': 11,   'ry': 19,
    'apertura': 1.0,
    'boca_t': 1.0,
}

# ─── Estado: Reposo ──────────────────────────────────────────

def cara_reposo(frames=60):
    for f in range(frames):
        display.fill(0)

        # Ojos semicerrados (adormilados)
        ojo(45, 22, 10, 18, semicerrado=True)
        ojo(83, 22, 10, 18, semicerrado=True)

        # Boca: línea simple
        display.line(50, 50, 78, 50, 1)

        # Z flotantes con parpadeo alterno
        t_ms = time.ticks_ms()
        if (t_ms // 500) % 2 == 0:
            display.text('z', 100, 14, 1)
        if (t_ms // 750) % 2 == 0:
            display.text('Z', 109,  6, 1)

        display.show()
        time.sleep_ms(80)

        # Parpadeo ocasional
        if f % 55 == 0:
            for _ in range(3):
                display.fill(0)
                ojo(45, 22, 10, 18, cerrado=True)
                ojo(83, 22, 10, 18, cerrado=True)
                display.line(50, 50, 78, 50, 1)
                display.show()
                time.sleep_ms(60)

# ─── Estado: Escuchando ──────────────────────────────────────

def cara_escuchando(frames=50):
    for f in range(frames):
        display.fill(0)

        # Ojos bien abiertos
        ojo(43, 22, 11, 20)
        ojo(85, 22, 11, 20)

        # Boca cerrada neutra
        display.line(52, 50, 76, 50, 1)

        # Ondas de sonido entrantes (izquierda)
        amp = int(abs(math.sin(f * 0.2)) * 3)
        for r in [8+amp, 14+amp]:
            steps = 20
            for i in range(steps+1):
                a = -0.6 + 1.2 * i / steps
                x = int(6 + r * math.cos(a))
                y = int(22 + r * math.sin(a))
                if 0 <= x < 128 and 0 <= y < 64:
                    display.pixel(x, y, 1)

        display.show()
        time.sleep_ms(80)

        # Parpadeo ocasional
        if f % 45 == 0:
            display.fill(0)
            ojo(43, 22, 11, 20, cerrado=True)
            ojo(85, 22, 11, 20, cerrado=True)
            display.line(52, 50, 76, 50, 1)
            display.show()
            time.sleep_ms(80)

# ─── Estado: Pensando ────────────────────────────────────────

def cara_pensando(frames=65):
    for f in range(frames):
        display.fill(0)

        # Ojos entrecerrados
        ojo(45, 22, 10, 18, semicerrado=True)
        ojo(83, 22, 10, 18, semicerrado=True)

        # Cejas: solo aquí aparecen
        # Izquierda: plana
        display.line(36, 3,  54, 3,  1)
        display.line(36, 4,  54, 4,  1)
        # Derecha: inclinada (escéptico)
        display.line(74, 6,  92, 3,  1)
        display.line(74, 7,  92, 4,  1)

        # Boca torcida
        display.line(50, 51, 60, 49, 1)
        display.line(60, 49, 78, 52, 1)

        # Tres puntos animados
        n = (f // 15) % 4
        for i in range(3):
            cx_d = 50 + i*14
            if i < n:
                circulo(cx_d, 59, 3)
            else:
                elipse_hueca(cx_d, 59, 3, 3)

        display.show()
        time.sleep_ms(80)

# ─── Estado: Hablando ────────────────────────────────────────

_boca_fases = [
    (12, 8),   # abierta grande
    (8,  4),   # mediana
    (13, 9),   # muy abierta
    (7,  3),   # pequeña
]

def cara_hablando(frames=70):
    for f in range(frames):
        display.fill(0)

        # Ojos abiertos, ligeramente más arriba para dar espacio a la boca
        ojo(43, 20, 11, 19)
        ojo(85, 20, 11, 19)

        # Boca animada: cicla entre 4 formas
        fase = (f // 10) % 4
        rx_b, ry_b = _boca_fases[fase]
        boca_abierta(64, 50, rx_b, ry_b)

        # Ondas de sonido salientes (derecha)
        amp = int(abs(math.sin(f * 0.2)) * 3)
        for r in [8+amp, 14+amp]:
            steps = 20
            for i in range(steps+1):
                a = math.pi - 0.6 + 1.2 * i / steps
                x = int(122 + r * math.cos(a))
                y = int(50  + r * math.sin(a))
                if 0 <= x < 128 and 0 <= y < 64:
                    display.pixel(x, y, 1)

        # Parpadeo ocasional
        if f % 50 == 0 and f > 0:
            display.fill(0)
            ojo(43, 20, 11, 19, cerrado=True)
            ojo(85, 20, 11, 19, cerrado=True)
            boca_abierta(64, 50, rx_b, ry_b)
            display.show()
            time.sleep_ms(70)
            continue

        display.show()
        time.sleep_ms(70)


def iniciar():
    display.fill(0)
    display.show()
    print("Pantalla lista")