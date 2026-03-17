import pantalla
import wifi
import random
import time 

time.sleep(2)
wifi.conectar()
pantalla.iniciar()

ESTADOS = [
    (0, pantalla.cara_reposo,     pantalla.P_REPOSO,     "Reposo"),
    (1, pantalla.cara_escuchando, pantalla.P_ESCUCHANDO, "Escuchando"),
    (2, pantalla.cara_pensando,   pantalla.P_PENSANDO,   "Pensando"),
    (3, pantalla.cara_hablando,   pantalla.P_HABLANDO,   "Hablando"),
]

TRANSICIONES = {
    0: [1],
    1: [2, 2, 3],
    2: [3, 3, 1],
    3: [0, 0, 2],
}

idx = 0
while True:
    _, cara_fn, params, nombre = ESTADOS[idx]
    print("Estado:", nombre)
    cara_fn()

    opciones = TRANSICIONES[idx]
    idx_next = opciones[random.randint(0, len(opciones)-1)]
    _, _, params_next, _ = ESTADOS[idx_next]

    pantalla.morph(params, params_next)
    idx = idx_next