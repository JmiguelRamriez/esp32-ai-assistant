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
print("Estado: Reposo")

while True:
    if boton.value() == 0:
        time.sleep(0.1)
        
        if boton.value() == 0:
            print("\n--- INICIANDO INTERACCIÓN ---")
            pantalla.mostrar_escuchando()
            
            gc.collect()
            try:
                respuesta = cliente.escuchar_y_preguntar(boton)
                
                if respuesta:
                    pantalla.mostrar_hablando()
                    print("IA:", respuesta)
                    cliente.hablar(respuesta)
                else:
                    print("La IA no devolvió ninguna respuesta.")
                    
            except Exception as e:
                print("Error durante la comunicación:", e)
            
            pantalla.mostrar_reposo()
            print("Estado: Reposo")
                
    time.sleep(0.1)