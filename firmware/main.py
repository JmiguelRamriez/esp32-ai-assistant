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
    # Si detecta que presionaste el botón (Pin a Tierra/GND)
    if boton.value() == 0:
        time.sleep(0.1) # Pequeña pausa antirrebote
        
        # Confirma que el botón sigue presionado (no fue ruido eléctrico)
        if boton.value() == 0:
            print("\n--- INICIANDO INTERACCIÓN ---")
            pantalla.mostrar_escuchando()
            print("Estado: Escuchando (Habla ahora...)")
            
            # Graba el audio y se lo manda al servidor
            gc.collect()
            try:
                respuesta = cliente.escuchar_y_preguntar()
                
                # Si la IA contestó algo válido
                if respuesta:
                    pantalla.mostrar_hablando()
                    print("IA:", respuesta)
                    time.sleep(5) # Deja la cara de hablando 5 segundos para que la veas
                else:
                    print("La IA no devolvió ninguna respuesta.")
                    
            except Exception as e:
                print("Error durante la grabación/comunicación:", e)
            
            # Vuelve a poner la cara de reposo
            pantalla.mostrar_reposo()
            print("Estado: Reposo")
            
            # ESTA ES LA CLAVE: El código se queda "atrapado" aquí 
            # hasta que físicamente sueltes el botón. Así evitamos el bucle.
            while boton.value() == 0:
                time.sleep(0.1)
                
    # Pequeña pausa para no saturar el procesador
    time.sleep(0.1)