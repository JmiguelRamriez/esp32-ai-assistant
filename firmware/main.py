import pantalla
import wifi
import cliente
import gc
from machine import Pin
import time

time.sleep(2)
wifi.conectar()
pantalla.iniciar()

# Configuración de tu botón
boton = Pin(14, Pin.IN, Pin.PULL_UP)

pantalla.mostrar_reposo()
print("Estado: Reposo")

while True:
    if boton.value() == 0:
        time.sleep(0.1) # Antirrebote
        
        if boton.value() == 0:
            print("\n--- INICIANDO INTERACCIÓN ---")
            pantalla.mostrar_escuchando()
            print("Estado: Escuchando (Habla ahora y mantén presionado el botón...)")
            
            gc.collect()
            try:
                # ¡Aquí le pasamos el botón a la función!
                respuesta = cliente.escuchar_y_preguntar(boton)
                
                if respuesta:
                    pantalla.mostrar_hablando()
                    print("IA:", respuesta)
                    time.sleep(5) 
                else:
                    print("La IA no devolvió ninguna respuesta.")
                    
            except Exception as e:
                print("Error durante la comunicación:", e)
            
            pantalla.mostrar_reposo()
            print("Estado: Reposo")
            
            # Ya no necesitamos el 'while boton.value() == 0' aquí abajo 
            # porque la función grabar() de grabar.py ya hace esa pausa por nosotros.
                
    time.sleep(0.1)