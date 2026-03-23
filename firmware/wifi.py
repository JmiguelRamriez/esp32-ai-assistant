import config
import network
import time

def conectar():
    """
    Intenta establecer conexión con la red WiFi configurada en config.py.
    Aplica una secuencia de reinicio de la interfaz de red para 
    evitar estados corruptos comunes en el ESP32.
    """
    wlan = network.WLAN(network.STA_IF) # Modo Estación (Cliente WiFi)
    
    # El truco para limpiar el estado corrupto: apagar, encender y desconectar a la fuerza
    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)
    wlan.disconnect()
    time.sleep(0.5)
    
    print("Intentando conectar a:", config.SSID)
    wlan.connect(config.SSID, config.PASSWORD)
    
    # Agregamos un límite de intentos para que no se quede en un bucle infinito
    intentos = 0
    while not wlan.isconnected() and intentos < 20:
        print("Conectando...")
        time.sleep(0.5)
        intentos += 1
        
    if wlan.isconnected():
        print("¡Conectado exitosamente! IP:", wlan.ifconfig()[0])
    else:
        print("Falló la conexión. Revisa que el nombre y contraseña de tu red de casa sean correctos.")

def verificar_y_reconectar():
    """Comprueba si el WiFi sigue conectado y reconecta si no."""
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi desconectado. Intentando reconectar...")
        conectar()
        if wlan.isconnected():
            import pantalla
            pantalla.sincronizar_hora()