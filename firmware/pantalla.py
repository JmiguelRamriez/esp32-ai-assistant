from machine import Pin, SoftI2C
import sh1106
import time
import urandom

# Variables globales
i2c = None
display = None

# Centro de la pantalla (128x64)
CX = 64
CY = 32

def iniciar():
    global i2c, display
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
    time.sleep(3)
    display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3c)
    display.poweron()
    limpiar()
    # ¡Texto actualizado para reflejar el nuevo espíritu alegre!
    print("Pantalla lista")

def limpiar():
    display.fill(0)
    display.show()

# -------------------------------------------------------------------
# PRIMITIVAS BASE
# -------------------------------------------------------------------

def draw_rect_redondeado(x, y, w, h, color=1):
    """Rectángulo con esquinas 'recortadas' de 1px para simular bordes redondeados."""
    # Cara principal
    display.fill_rect(x+1, y,   w-2, h,   color)
    display.fill_rect(x,   y+1, w,   h-2, color)

def draw_ojo_emo(x, y, w=26, h=20, color=1):
    """
    Ojo rectangular base.
    MODIFICACIÓN: ¡Ahora incluye un brillo constante en la esquina superior 
    para una expresión más alegre y tierna por defecto!
    """
    # Relleno sólido
    draw_rect_redondeado(x, y, w, h, color)
    # --- TOQUE ALEGRE/TIERNO: Brillo constante ---
    display.fill_rect(x+3, y+3, 4, 4, 0) # Pequeño brillo vacío/blanco

def draw_ojo_parpadeo(x, y, w=26, color=1):
    """Ojo entrecerrado (línea horizontal gruesa) — frame de parpadeo."""
    display.fill_rect(x+1, y+1, w-2, 3, color)

def draw_ojo_feliz(x, y, w=26, h=20, color=1):
    """
    Ojo con la mitad inferior rellena y la superior vacía → efecto "^^".
    """
    mid = h // 2
    draw_rect_redondeado(x, y + mid, w, mid, color)
    # Borde superior para dar forma
    display.hline(x+1, y + mid - 1, w-2, color)

def draw_ojo_triste(x, y, w=26, h=20, color=1):
    """Ojo con la mitad superior rellena → expresión caída."""
    mid = h // 2
    draw_rect_redondeado(x, y, w, mid + 1, color)

def draw_ojo_dormido(x, y, w=26, color=1):
    """Línea horizontal delgada — ojos cerrados durmiendo."""
    display.fill_rect(x+1, y, w-2, 2, color)

# Primitiva para ojos escuchando/atentos
def draw_ojo_escuchando(x, y, w=26, h=20, color=1):
    """
    Para el estado de escucha: Ojo lleno con destello lateral más grande, 
    atento y dulce.
    """
    draw_rect_redondeado(x, y, w, h, color)
    display.fill_rect(x+3, y+3, 6, 6, 0) # Destello más notable

def draw_z(x, y, size=6, color=1):
    h = size
    w = int(size * 0.8)
    display.hline(x, y, w, color)
    display.line(x+w, y, x, y+h, color)
    display.hline(x, y+h, w, color)

def draw_dot(x, y, color=1):
    display.fill_rect(x, y, 3, 3, color)

# -------------------------------------------------------------------
# POSICIONES DE LOS OJOS MODIFICADAS
# Pantalla 128x64 — dos ojos GRANDES Y ALARGADOS VERTICALMENTE
# -------------------------------------------------------------------
# !!! CAMBIO: Ojos más altos (H=28) que anchos (W=20) !!!
EYE_W  = 20   # Ancho de cada ojo
EYE_H  = 28   # Alto de cada ojo
EYE_GAP = 12  # Espacio entre los dos ojos

# Ojo izquierdo: su X izquierda
EYE_L_X = CX - EYE_GAP//2 - EYE_W   # = 64 - 6 - 20 = 38
EYE_R_X = CX + EYE_GAP//2            # = 64 + 6      = 70
EYE_Y   = CY - EYE_H//2              # = 32 - 14     = 18

# -------------------------------------------------------------------
# ESTADOS
# -------------------------------------------------------------------

def mostrar_reposo():
    """Ojos dormidos (líneas finas) con animación ZZZ intacta."""
    for i in range(4):
        display.fill(0)
        draw_ojo_dormido(EYE_L_X, EYE_Y + EYE_H//2, EYE_W)
        draw_ojo_dormido(EYE_R_X, EYE_Y + EYE_H//2, EYE_W)

        # ZZZ flotando arriba-derecha (coordenadas ajustadas)
        sx = EYE_R_X + EYE_W + 6
        sy = EYE_Y - 8
        if i >= 1: draw_z(sx,     sy+6,  4)
        if i >= 2: draw_z(sx+6,  sy+1,  6)
        if i >= 3: draw_z(sx+14, sy-4,  8)

        display.show()
        time.sleep(0.4)

def mostrar_escuchando():
    """Ojos atentos y dulces (con brillo más grande)."""
    display.fill(0)
    draw_ojo_escuchando(EYE_L_X, EYE_Y, EYE_W, EYE_H)
    draw_ojo_escuchando(EYE_R_X, EYE_Y, EYE_W, EYE_H)
    display.show()

def mostrar_pensando():
    """Ojos normales (con brillo tierno por defecto) + animación de puntitos intacta."""
    for i in range(4):
        display.fill(0)
        draw_ojo_emo(EYE_L_X, EYE_Y, EYE_W, EYE_H)
        draw_ojo_emo(EYE_R_X, EYE_Y, EYE_W, EYE_H)

        # Puntitos debajo de los ojos (coordenadas ajustadas)
        dot_y = EYE_Y + EYE_H + 4
        dot_x = CX - 8
        gap = 8
        if i >= 1: draw_dot(dot_x,       dot_y)
        if i >= 2: draw_dot(dot_x+gap,   dot_y)
        if i >= 3: draw_dot(dot_x+gap*2, dot_y)

        display.show()
        time.sleep(0.35)

def mostrar_hablando():
    """Ojos felices ^^ con animación de boca abierta/cerrada intacta."""
    for i in range(6):
        display.fill(0)
        draw_ojo_feliz(EYE_L_X, EYE_Y, EYE_W, EYE_H)
        draw_ojo_feliz(EYE_R_X, EYE_Y, EYE_W, EYE_H)

        # Boca debajo: alterna abierta/cerrada
        # Coordenadas ajustadas para los nuevos ojos altos
        boca_y = EYE_Y + EYE_H + 4
        boca_x = CX - 8
        if i % 2 == 0:
            # Boca cerrada — línea horizontal
            display.fill_rect(boca_x, boca_y, 16, 3, 1)
        else:
            # Boca abierta — rectángulo pequeño redondeado
            draw_rect_redondeado(boca_x, boca_y, 16, 7, 1)

        # Ondas de sonido intactas (coordenadas ajustadas)
        if i % 2 == 1:
            sx = EYE_R_X + EYE_W + 5
            sy = EYE_Y + 6
            display.line(sx,   sy,   sx+4, sy-4, 1)
            display.line(sx,   sy+6, sx+4, sy+10, 1)
            if i >= 3:
                display.line(sx+6, sy-2, sx+10, sy-7, 1)
                display.line(sx+6, sy+8, sx+10, sy+13, 1)

        display.show()
        time.sleep(0.18)

def mostrar_triste():
    """Ojos caídos — para estados de error."""
    display.fill(0)
    draw_ojo_triste(EYE_L_X, EYE_Y, EYE_W, EYE_H)
    draw_ojo_triste(EYE_R_X, EYE_Y, EYE_W, EYE_H)
    display.show()

def parpadear_una_vez():
    """Anima un parpadeo rápido sin cambiar el estado actual."""
    display.fill_rect(EYE_L_X, EYE_Y, EYE_W, EYE_H, 0)
    display.fill_rect(EYE_R_X, EYE_Y, EYE_W, EYE_H, 0)
    draw_ojo_parpadeo(EYE_L_X, EYE_Y + EYE_H//2 - 1, EYE_W)
    draw_ojo_parpadeo(EYE_R_X, EYE_Y + EYE_H//2 - 1, EYE_W)
    display.show()
    time.sleep(0.08)