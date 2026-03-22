from machine import Pin, SoftI2C
import sh1106
import time

# ─── Variables globales ────────────────────────────────────────────────────────
i2c     = None
display = None

CX = 64   # Centro X de la pantalla (128px)
CY = 32   # Centro Y de la pantalla (64px)

# Geometría de los ojos — sin cejas, más compactos
EYE_W   = 24          # Ancho de cada ojo
EYE_H   = 30          # Alto de cada ojo
EYE_GAP = 14          # Separación entre ojos
EYE_L_X = CX - EYE_GAP // 2 - EYE_W   # X del ojo izquierdo
EYE_R_X = CX + EYE_GAP // 2            # X del ojo derecho
EYE_Y   = CY - EYE_H // 2 - 4         # Y común (ligeramente arriba para el reloj)

# Offset horario — México Centro (Querétaro) UTC-6, sin horario de verano
UTC_OFFSET = -6

_hora_ok = False  # True si NTP fue exitoso


# ─── Inicialización ────────────────────────────────────────────────────────────

def iniciar():
    global i2c, display
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
    time.sleep(3)
    display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3c)
    display.poweron()
    limpiar()
    print("Pantalla lista")

def sincronizar_hora():
    """Sincronizar reloj interno con NTP (llamar después de conectar WiFi)."""
    global _hora_ok
    try:
        import ntptime
        ntptime.settime()
        _hora_ok = True
        print("Hora NTP sincronizada")
    except Exception as e:
        _hora_ok = False
        print("NTP falló:", e)

def limpiar():
    display.fill(0)
    display.show()


# ─── Primitivas de dibujo ──────────────────────────────────────────────────────

def _r(x, y, w, h, c=1):
    """Rectángulo con esquinas ligeramente redondeadas."""
    if w <= 0 or h <= 0:
        return
    display.fill_rect(x + 1, y,     w - 2, h,     c)
    display.fill_rect(x,     y + 1, w,     h - 2, c)


# ─── Formas de ojo ────────────────────────────────────────────────────────────

def _ojo_abierto(x, y, w=EYE_W, h=EYE_H, c=1):
    """Ojo rectangular con pupila centrada."""
    _r(x, y, w, h, c)
    # Pupila (cuadradito invertido de color)
    display.fill_rect(x + w // 2 - 2, y + h // 2 - 2, 4, 4, 1 - c)

def _ojo_sorprendido(x, y, w=EYE_W, h=EYE_H, c=1):
    """Ojo muy abierto — pupila pequeña para expresar sorpresa."""
    _r(x, y, w, h, c)
    display.fill_rect(x + w // 2 - 1, y + h // 2 - 1, 2, 2, 1 - c)

def _ojo_feliz(x, y, w=EYE_W, h=EYE_H, c=1):
    """Ojo ^^ — solo mitad inferior rellena."""
    mid = h // 2
    _r(x, y + mid, w, mid, c)
    display.hline(x + 1, y + mid - 1, w - 2, c)

def _ojo_triste(x, y, w=EYE_W, h=EYE_H, c=1):
    """Ojo caído — solo mitad superior."""
    mid = h // 2
    _r(x, y, w, mid + 1, c)

def _ojo_dormido(x, y, w=EYE_W, c=1):
    """Ojo cerrado — línea delgada."""
    display.fill_rect(x + 1, y, w - 2, 2, c)

def _ojo_lateral(x, y, lado, w=EYE_W, h=EYE_H, c=1):
    """Ojo con pupila desplazada: lado -1=izq, 0=centro, 1=der."""
    _r(x, y, w, h, c)
    offset = lado * (w // 4)
    px = x + w // 2 - 2 + offset
    display.fill_rect(px, y + h // 2 - 2, 4, 4, 1 - c)

def _ojo_cerrado_anim(x, y, apertura, w=EYE_W, h=EYE_H, c=1):
    """Ojo con altura variable (para animación de parpadeo)."""
    if apertura <= 0:
        return
    y_off = (h - apertura) // 2
    _r(x, y + y_off, w, apertura, c)


# ─── Boca ─────────────────────────────────────────────────────────────────────

def _boca(cx, y, estado, c=1):
    """estado: 0=cerrada, 1=abierta redondeada."""
    x = cx - 10
    if estado == 0:
        display.fill_rect(x, y, 20, 3, c)
    else:
        _r(x - 2, y, 24, 10, c)


# ─── Auxiliares ───────────────────────────────────────────────────────────────

def _z(x, y, s=6, c=1):
    """Dibuja una 'Z' de tamaño s."""
    w = int(s * 0.8)
    display.hline(x, y, w, c)
    display.line(x + w, y, x, y + s, c)
    display.hline(x, y + s, w, c)

def _dot(x, y, c=1):
    display.fill_rect(x, y, 3, 3, c)

def _hora_texto():
    """Devuelve la hora local como string 'HH:MM'."""
    try:
        t = time.localtime()
        h = (t[3] + UTC_OFFSET) % 24
        return "{:02d}:{:02d}".format(h, t[4])
    except:
        return ""

def _dibujar_reloj():
    """Dibuja la hora centrada en la línea inferior de la pantalla."""
    if not _hora_ok:
        return
    s = _hora_texto()
    x = CX - len(s) * 4
    display.text(s, x, 55, 1)


# ─── Transición ───────────────────────────────────────────────────────────────

def _transicion():
    """Parpadeo suave como transición entre estados."""
    pasos = 4
    # Cerrar ojos
    for i in range(pasos):
        display.fill(0)
        h = EYE_H - (EYE_H // pasos) * (i + 1)
        if h > 0:
            y_off = (EYE_H - h) // 2
            _ojo_cerrado_anim(EYE_L_X, EYE_Y, h)
            _ojo_cerrado_anim(EYE_R_X, EYE_Y, h)
        display.show()
        time.sleep_ms(35)

    display.fill(0)
    display.show()
    time.sleep_ms(50)

    # Abrir ojos
    for i in range(pasos):
        display.fill(0)
        h = (EYE_H // pasos) * (i + 1)
        _ojo_cerrado_anim(EYE_L_X, EYE_Y, h)
        _ojo_cerrado_anim(EYE_R_X, EYE_Y, h)
        display.show()
        time.sleep_ms(35)


# ─── Estados ──────────────────────────────────────────────────────────────────

def mostrar_reposo():
    """Prepara el estado de reposo (primer frame)."""
    _transicion()
    tick_reposo(0)

def tick_reposo(t):
    """
    Llamar desde main.py en cada ciclo del while.
    't' es el contador del loop (incrementa cada 0.3 s aprox).
    Actualiza la animación ZZZ y el reloj sin bloquear.
    """
    display.fill(0)

    # Ojos durmiendo
    ey = EYE_Y + EYE_H // 2
    _ojo_dormido(EYE_L_X, ey)
    _ojo_dormido(EYE_R_X, ey)

    # ZZZ — aparecen de a poco y se reinician
    fase = (t // 2) % 5
    sx = EYE_R_X + EYE_W + 4
    sy = EYE_Y + 2
    if fase >= 1: _z(sx,      sy + 8,  4)
    if fase >= 2: _z(sx + 6,  sy + 2,  6)
    if fase >= 3: _z(sx + 13, sy - 4,  8)

    # Reloj
    _dibujar_reloj()

    display.show()


def mostrar_escuchando():
    """Ojos muy abiertos y sorprendidos — atención total."""
    _transicion()
    display.fill(0)
    _ojo_sorprendido(EYE_L_X, EYE_Y)
    _ojo_sorprendido(EYE_R_X, EYE_Y)
    display.show()


def mostrar_pensando():
    """Ojos que miran a los lados con puntos de carga."""
    _transicion()
    dot_y = EYE_Y + EYE_H + 7
    dot_x = CX - 12

    for ciclo in range(3):
        for lado in [-1, 0, 1, 0]:
            display.fill(0)
            _ojo_lateral(EYE_L_X, EYE_Y, lado)
            _ojo_lateral(EYE_R_X, EYE_Y, lado)
            # Puntos de carga que avanzan
            for d in range(min(ciclo + 1, 3)):
                _dot(dot_x + d * 10, dot_y)
            display.show()
            time.sleep_ms(280)

    # Guiño rápido al final como "ya casi"
    display.fill(0)
    _ojo_feliz(EYE_L_X, EYE_Y)
    _ojo_dormido(EYE_R_X, EYE_Y + EYE_H // 2)
    display.show()
    time.sleep_ms(200)


def mostrar_hablando():
    """Ojos felices ^^ con boca animada y ondas de sonido."""
    _transicion()
    boca_y = EYE_Y + EYE_H + 3
    boca_cx = CX

    for i in range(10):
        display.fill(0)
        _ojo_feliz(EYE_L_X, EYE_Y)
        _ojo_feliz(EYE_R_X, EYE_Y)
        _boca(boca_cx, boca_y, i % 2)

        # Ondas de sonido a la derecha
        if i % 2 == 1:
            sx = EYE_R_X + EYE_W + 3
            sy = EYE_Y + 6
            display.line(sx,     sy,     sx + 4, sy - 4, 1)
            display.line(sx,     sy + 6, sx + 4, sy + 10, 1)
            if i >= 4:
                display.line(sx + 6,  sy - 2,  sx + 10, sy - 7, 1)
                display.line(sx + 6,  sy + 8,  sx + 10, sy + 13, 1)

        display.show()
        time.sleep_ms(160)


def mostrar_triste():
    """Ojos caídos — para errores."""
    _transicion()
    display.fill(0)
    _ojo_triste(EYE_L_X, EYE_Y)
    _ojo_triste(EYE_R_X, EYE_Y)
    display.show()