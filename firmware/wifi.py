import config # credenciales wifi
import network # Librería nativa de MicroPython para controlar la antena de red del chip
import time # Libreria para manjar tiempos

def conectar():
    #Creamos el objeto 'wlan' y lo configuramos en modo "Estación" (STA_IF)
    # Esto significa que el ESP32 actuará como un cliente conectándose a tu módem
    wlan = network.WLAN(network.STA_IF) 
    wlan.active(True) # Encendemos el hardware de la antena Wi-Fi
    wlan.connect(config.SSID, config.PASSWORD)# Le damos la orden de conectarse usando las variables de tu archivo config
    
    # Revisa constantamente hasta que se conecte
    while not wlan.isconnected():
        print("Conectando...")
        time.sleep_ms(300)
    print("Conectado:", wlan.ifconfig()[0])