import pantalla
import wifi
import cliente
import time
import gc
from machine import Pin

time.sleep(2)
wifi.conectar()
pantalla.iniciar()

boton = Pin(14, Pin.IN, Pin.PULL_UP)

while True:
    # Mostrar cara reposo mientras espera
    pantalla.cara_reposo(frames=10)
    
    # Esperar que se presione el botón
    if boton.value() == 0:  # 0 = presionado (PULL_UP)
        print("Botón presionado, escuchando...")
        
        # Cara escuchando mientras graba
        pantalla.morph(pantalla.P_REPOSO, pantalla.P_ESCUCHANDO)
        
        # Grabar y obtener respuesta
        gc.collect()
        respuesta = cliente.escuchar_y_preguntar()
        
        # Cara pensando mientras procesa
        pantalla.morph(pantalla.P_ESCUCHANDO, pantalla.P_PENSANDO)
        pantalla.cara_pensando(frames=10)
        
        # Cara hablando con la respuesta
        pantalla.morph(pantalla.P_PENSANDO, pantalla.P_HABLANDO)
        pantalla.cara_hablando(frames=50)
        
        # Volver a reposo
        pantalla.morph(pantalla.P_HABLANDO, pantalla.P_REPOSO)