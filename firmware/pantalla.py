from machine import Pin, I2C
import sh1106
import math
import time
import random

# Variables globales - se inicializan en iniciar()
i2c = None
display = None

def iniciar():
    global i2c, display
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    time.sleep(3)        # ← ahora el delay va DESPUÉS de crear el I2C, ANTES de crear la pantalla
    display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3c)
    display.poweron()
    display.fill(0)
    display.show()
    print("Pantalla lista")

def mostrar_reposo():
    display.fill(0)
    ojo(45, 22, 10, 18, semicerrado=True)
    ojo(83, 22, 10, 18, semicerrado=True)
    display.line(50, 50, 78, 50, 1)
    display.show()

def mostrar_escuchando():
    display.fill(0)
    ojo(43, 22, 11, 20)
    ojo(85, 22, 11, 20)
    display.line(52, 50, 76, 50, 1)
    display.show()

def mostrar_pensando():
    display.fill(0)
    ojo(45, 22, 10, 18, semicerrado=True)
    ojo(83, 22, 10, 18, semicerrado=True)
    display.line(36, 3, 54, 3, 1)
    display.line(74, 6, 92, 3, 1)
    display.show()

def mostrar_hablando():
    display.fill(0)
    ojo(43, 20, 11, 19)
    ojo(85, 20, 11, 19)
    boca_abierta(64, 50, 12, 8)
    display.show()