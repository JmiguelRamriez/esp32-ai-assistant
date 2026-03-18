import pantalla
import wifi
import cliente
import gc
from machine import Pin
import time

time.sleep(2)
wifi.conectar()
pantalla.iniciar()

boton = Pin(14, Pin.IN, Pin.PULL_UP)
pantalla.mostrar_reposo()

while True:
    if boton.value() == 0:
        print("Escuchando...")
        pantalla.morph(pantalla.P_REPOSO, pantalla.P_ESCUCHANDO)
        pantalla.mostrar_escuchando()
        
        gc.collect()
        respuesta = cliente.escuchar_y_preguntar()
        
        pantalla.morph(pantalla.P_ESCUCHANDO, pantalla.P_PENSANDO)
        pantalla.mostrar_pensando()
        
        pantalla.morph(pantalla.P_PENSANDO, pantalla.P_HABLANDO)
        pantalla.mostrar_hablando()
        
        time.sleep(2)
        
        pantalla.morph(pantalla.P_HABLANDO, pantalla.P_REPOSO)
        pantalla.mostrar_reposo()
        print("Listo.")
    
    time.sleep_ms(50)