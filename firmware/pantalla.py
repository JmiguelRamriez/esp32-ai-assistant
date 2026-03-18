from machine import Pin, I2C
import sh1106
import time

# Variables globales
i2c = None
display = None

def iniciar():
    global i2c, display
    # ¡Regresamos a tus pines originales de ESP32!
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    time.sleep(3) # El delay necesario para que la pantalla encienda
    display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3c)
    display.poweron()
    display.fill(0)
    display.show()
    print("Pantalla lista")

# --- Funciones de Dibujo ---

def ojo(x, y, r, color=1):
    # Algoritmo matemático para dibujar un círculo lleno sin fallos
    f = 1 - r
    ddf_x = 1
    ddf_y = -2 * r
    temp_x = 0
    temp_y = r
    display.line(x, y - r, x, y + r, color)
    
    while temp_x < temp_y:
        if f >= 0:
            temp_y -= 1
            ddf_y += 2
            f += ddf_y
        temp_x += 1
        ddf_x += 2
        f += ddf_x
        
        display.line(x + temp_x, y - temp_y, x + temp_x, y + temp_y, color)
        display.line(x - temp_x, y - temp_y, x - temp_x, y + temp_y, color)
        display.line(x + temp_y, y - temp_x, x + temp_y, y + temp_x, color)
        display.line(x - temp_y, y - temp_x, x - temp_y, y + temp_x, color)

# --- Funciones de Animación (Estados de la IA) ---

def mostrar_reposo():
    display.fill(0) 
    # Ojos pequeños
    ojo(44, 25, 6, 1) 
    ojo(84, 25, 6, 1) 
    # Boca cerrada 
    display.hline(44, 50, 40, 1)
    display.show()

def mostrar_escuchando():
    display.fill(0) 
    # Ojos muy grandes
    ojo(44, 25, 10, 1) 
    ojo(84, 25, 10, 1) 
    # Boca cerrada 
    display.hline(44, 50, 40, 1)
    display.show()

def mostrar_pensando():
    display.fill(0) 
    # Ojos como líneas gruesas (pensando)
    display.line(34, 25, 54, 25, 1) 
    display.line(34, 26, 54, 26, 1)
    display.line(74, 25, 94, 25, 1) 
    display.line(74, 26, 94, 26, 1)
    # Boca cerrada 
    display.hline(44, 50, 40, 1)
    display.show()

def mostrar_hablando():
    display.fill(0) 
    # Ojos normales
    ojo(44, 25, 8, 1) 
    ojo(84, 25, 8, 1) 
    # Boca abierta (usamos un pequeño rectángulo sólido)
    display.fill_rect(58, 46, 14, 8, 1) 
    display.show()