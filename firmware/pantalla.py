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
    print("Pantalla lista (Modo EMO Activado)")

def limpiar():
    display.fill(0)
    display.show()

# -------------------------------------------------------------------
# PRIMITIVAS BASE
# -------------------------------------------------------------------

def draw_rect_redondeado(x, y, w, h, color=1):
    """Rectángulo con esquinas 'recortadas' de 1px para simular bordes redondeados."""
    if w <= 0 or h <= 0: return
    display.fill_rect(x+1, y,   w-2, h,   color)
    display.fill_rect(x,   y+1, w,   h-2, color)

def draw_ceja(x, y, w, angle, color=1):
    """
    Dibuja una ceja arriba del ojo.
    angle: 0 (plana), 1 (enojado \ ), -1 (triste / )
    """
    if angle == 0:
        display.fill_rect(x, y, w, 3, color)
    elif angle == 1: # \ para el ojo izquierdo, / para el derecho se invierte
        display.line(x, y, x+w, y+4, color)
        display.line(x, y+1, x+w, y+5, color)
        display.line(x, y+2, x+w, y+6, color)
    elif angle == -1: # /
        display.line(x, y+4, x+w, y, color)
        display.line(x, y+5, x+w, y+1, color)
        display.line(x, y+6, x+w, y+2, color)

def draw_ojo_emo(x, y, w=26, h=20, color=1):
    draw_rect_redondeado(x, y, w, h, color)

def draw_ojo_parpadeo(x, y, w=26, color=1):
    display.fill_rect(x+1, y+1, w-2, 3, color)

def draw_ojo_feliz(x, y, w=26, h=20, color=1):
    mid = h // 2
    draw_rect_redondeado(x, y + mid, w, mid, color)
    display.hline(x+1, y + mid - 1, w-2, color)

def draw_ojo_triste(x, y, w=26, h=20, color=1):
    mid = h // 2
    draw_rect_redondeado(x, y, w, mid + 1, color)

def draw_ojo_dormido(x, y, w=26, color=1):
    display.fill_rect(x+1, y, w-2, 2, color)

def draw_ojo_sorprendido(x, y, w=26, h=20, color=1):
    draw_rect_redondeado(x, y, w, h, color)
    # Pupila contraida / mirada fija
    display.fill_rect(x+w//2-2, y+h//2-2, 4, 4, 0)

def draw_z(x, y, size=6, color=1):
    h = size
    w = int(size * 0.8)
    display.hline(x, y, w, color)
    display.line(x+w, y, x, y+h, color)
    display.hline(x, y+h, w, color)

def draw_dot(x, y, color=1):
    display.fill_rect(x, y, 3, 3, color)

# -------------------------------------------------------------------
# POSICIONES DE LOS OJOS EMO
# -------------------------------------------------------------------
EYE_W  = 22   
EYE_H  = 30   
EYE_GAP = 12  
EYE_L_X = CX - EYE_GAP//2 - EYE_W   
EYE_R_X = CX + EYE_GAP//2           
EYE_Y   = CY - EYE_H//2             

# -------------------------------------------------------------------
# ESTADOS
# -------------------------------------------------------------------

def mostrar_reposo():
    """Ojos dormidos (líneas finas) con cejas suaves y animación ZZZ."""
    for i in range(4):
        display.fill(0)
        draw_ojo_dormido(EYE_L_X, EYE_Y + EYE_H//2, EYE_W)
        draw_ojo_dormido(EYE_R_X, EYE_Y + EYE_H//2, EYE_W)
        
        # Cejas relajadas
        draw_ceja(EYE_L_X, EYE_Y - 4, EYE_W, -1) # /
        draw_ceja(EYE_R_X, EYE_Y - 4, EYE_W, 1)  # \

        sx = EYE_R_X + EYE_W + 4
        sy = EYE_Y - 4
        if i >= 1: draw_z(sx,    sy+6,  4)
        if i >= 2: draw_z(sx+6,  sy+1,  6)
        if i >= 3: draw_z(sx+14, sy-4,  8)

        display.show()
        time.sleep(0.3)

def mostrar_escuchando():
    """Ojos grandes con pupilas atentas y cejas levantadas."""
    display.fill(0)
    # Cejas interesadas
    draw_ceja(EYE_L_X, EYE_Y - 8, EYE_W, 1)  # \
    draw_ceja(EYE_R_X, EYE_Y - 8, EYE_W, -1) # /
    
    draw_ojo_sorprendido(EYE_L_X, EYE_Y, EYE_W, EYE_H)
    draw_ojo_sorprendido(EYE_R_X, EYE_Y, EYE_W, EYE_H)
    display.show()

def mostrar_pensando():
    """Expresión de duda: un ojo normal, el otro entrecerrado."""
    for i in range(4):
        display.fill(0)
        # Ceja izqda plana, ceja drcha baja
        draw_ceja(EYE_L_X, EYE_Y - 6, EYE_W, 0)
        draw_ceja(EYE_R_X, EYE_Y - 2, EYE_W, 1)

        draw_ojo_emo(EYE_L_X, EYE_Y, EYE_W, EYE_H)
        # Ojo derecho más pequeño (pensando)
        draw_rect_redondeado(EYE_R_X, EYE_Y + EYE_H//4, EYE_W, EYE_H//2, 1)

        dot_y = EYE_Y + EYE_H + 6
        dot_x = CX - 8
        gap = 8
        if i >= 1: draw_dot(dot_x,       dot_y)
        if i >= 2: draw_dot(dot_x+gap,   dot_y)
        if i >= 3: draw_dot(dot_x+gap*2, dot_y)

        display.show()
        time.sleep(0.35)

def mostrar_hablando():
    """Ojos muy felices ^^ con cejas altas y boca animada."""
    for i in range(6):
        display.fill(0)
        
        # Cejas altas y felices
        draw_ceja(EYE_L_X, EYE_Y - 6, EYE_W, -1)
        draw_ceja(EYE_R_X, EYE_Y - 6, EYE_W, 1)

        draw_ojo_feliz(EYE_L_X, EYE_Y, EYE_W, EYE_H)
        draw_ojo_feliz(EYE_R_X, EYE_Y, EYE_W, EYE_H)

        # Boca animada redonda
        boca_y = EYE_Y + EYE_H + 2
        boca_x = CX - 6
        if i % 2 == 0:
            draw_rect_redondeado(boca_x, boca_y, 12, 4, 1) # cerrada
        else:
            draw_rect_redondeado(boca_x - 2, boca_y, 16, 10, 1) # abierta (sonora)

        if i % 2 == 1:
            sx = EYE_R_X + EYE_W + 3
            sy = EYE_Y + 4
            display.line(sx,   sy,   sx+4, sy-4, 1)
            display.line(sx,   sy+6, sx+4, sy+10, 1)
            if i >= 3:
                display.line(sx+6, sy-2, sx+10, sy-7, 1)
                display.line(sx+6, sy+8, sx+10, sy+13, 1)

        display.show()
        time.sleep(0.18)

def mostrar_triste():
    """Para errores."""
    display.fill(0)
    draw_ceja(EYE_L_X, EYE_Y - 2, EYE_W, 1)
    draw_ceja(EYE_R_X, EYE_Y - 2, EYE_W, -1)
    draw_ojo_triste(EYE_L_X, EYE_Y, EYE_W, EYE_H)
    draw_ojo_triste(EYE_R_X, EYE_Y, EYE_W, EYE_H)
    display.show()

def parpadear_una_vez():
    display.fill_rect(EYE_L_X, EYE_Y - 8, EYE_W, EYE_H + 8, 0)
    display.fill_rect(EYE_R_X, EYE_Y - 8, EYE_W, EYE_H + 8, 0)
    draw_ojo_parpadeo(EYE_L_X, EYE_Y + EYE_H//2 - 1, EYE_W)
    draw_ojo_parpadeo(EYE_R_X, EYE_Y + EYE_H//2 - 1, EYE_W)
    display.show()
    time.sleep(0.08)