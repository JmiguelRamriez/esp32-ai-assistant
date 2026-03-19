import pantalla
import wifi
import cliente
import gc
from machine import Pin
import time

# Esperar un poco para estabilizar el sistema antes de iniciar
time.sleep(2)

# Conectar al WiFi usando las credenciales en config.py
wifi.conectar()

# Iniciar la pantalla OLED y mostrar el modo reposo
pantalla.iniciar()

# Configurar el botón de interacción (Pin 14) con resistencia Pull-Up interna
boton = Pin(14, Pin.IN, Pin.PULL_UP)

# Mostrar la cara de reposo (ojos durmiendo) por defecto
pantalla.mostrar_reposo()
print("Estado: Reposo")

# Bucle principal del programa
while True:
    # Si el botón es presionado (valor 0 por el Pull-Up)
    if boton.value() == 0:
        time.sleep(0.1) # Antirrebote (debounce)
        
        # Confirmar que sigue presionado después del antirrebote
        if boton.value() == 0:
            print("\n--- INICIANDO INTERACCIÓN ---")
            # Cambiar la expresión a escuchando
            pantalla.mostrar_escuchando()
            
            # Liberar memoria antes de procesar audio
            gc.collect()
            try:
                # Iniciar la grabación y enviar al servidor para procesar
                respuesta = cliente.escuchar_y_preguntar(boton)
                
                # Si se obtuvo una respuesta válida desde la IA
                if respuesta:
                    pantalla.mostrar_hablando() # Cambiar la expresión a hablando
                    print("IA:", respuesta)
                    # Solicitar y reproducir el audio de la respuesta
                    cliente.hablar(respuesta)
                else:
                    print("La IA no devolvió ninguna respuesta.")
                    
            except Exception as e:
                # Manejo de errores durante la grabación, envío o recepción
                print("Error durante la comunicación:", e)
            
            # Volver al estado de reposo al terminar la interacción
            pantalla.mostrar_reposo()
            print("Estado: Reposo")
                
    time.sleep(0.1) # Pausa corta para no saturar el procesador