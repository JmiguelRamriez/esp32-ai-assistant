import wifi
import urequests

wifi.conectar()

respuesta = urequests.get("https://httpbin.org/ip")
print(respuesta.text)
respuesta.close()