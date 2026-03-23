# Asistente de IA con ESP32 🤖

### Este proyecto implementa un asistente de voz basado en inteligencia artificial utilizando el microcontrolador ESP32. El asistente puede escuchar tus preguntas, procesarlas a través de un servidor remoto (Flask) usando modelos de transcripción y generación de lenguaje (Groq), y responder conversando por un altavoz además de mostrar expresiones animadas en una pantalla OLED.

## Arquitectura del Sistema

El proyecto está dividido en dos grandes bloques:

1. **Hardware / Firmware Backend (ESP32)**:
   - Se encarga de la interacción directa con el usuario final.
   - Graba el audio a través de un micrófono **I2S**.
   - Muestra expresiones que denotan su estado (reposo, escuchando, pensando, hablando) en una **pantalla OLED I2C**.
   - Se conecta por WiFi y se comunica por Sockets HTTP y APIs con el backend.
   - Reproduce el audio de retorno en formato WAV (8-bits PCM Unsigned) usando los pines **DAC**.

2. **Servidor Backend (Flask + Groq)**:
   - Recibe el audio WAV y lo transcribe a texto usando el modelo Whisper de la API de Groq (`/transcribir` y `/despertar` para el Wake Word).
   - Envía el texto a un LLM (Llama-3.1 alojado en Groq) con un prompt especial para generar una respuesta (`/preguntar`).
   - Mantiene el historial de la conversación en un archivo `.json` para brindar contexto (y permite borrarlo vía `/reset`).
   - Convierte el texto de respuesta en una voz y lo optimiza usando gTTS y PyDub, enviando un WAV compatible de regreso (`/hablar`).

---

## Lista de Materiales (BOM) & Requisitos (Requirements)

### Hardware (BOM)

- **1x Microcontrolador ESP32** (Preferible uno con pines DAC como ESP32 clásico o WROOM-32).
- **1x Pantalla OLED 1.3" I2C SH1106 o similar** (128x64).
- **1x Micrófono I2S (Ej. INMP441)**.
- **1x Amplificador de audio** (Ej. MAX98357A, PAM8403 o LM386) + Altavoz pequeño.
- **1x Botón / Pulsador táctil** para iniciar interacción.
- Resistencias (generalmente el botón usa un pull-up interno del ESP32, o externo).
- Placa PCB (proyecto KiCad disponible en `hardware/`) o Protoboard.
- Cables Dupont o pistas diseñadas.

### Software (Prerequisites)

- **Python 3.9+** instalado en tu PC para uso local.
- **Thonny IDE** (Recomendado) o VSCode con extensión MicroPython para cargar archivos al ESP32.
- **MicroPython Firmware** (flasheado en tu ESP32, ej: `ESP32_GENERIC_v1.2x.bin`).
- Credencial / **API Key de Groq**.

---

## Instrucciones de Instalación (Paso a Paso)

### 1. Configuración del Servidor (Flask)

El servidor puede correr en tu computadora, en una Raspberry Pi o en plataformas en la nube (ej. Render/Heroku).

1. Abre una terminal y colócate en la carpeta `firmware/servidor`.
2. Instala las dependencias requeraledas:
   ```bash
   pip install -r requirements.txt
   ```
   _(Asegúrate de tener instalada la herramienta CLI FFmpeg u otras requeridas por PyDub en tu máquina local si corres esto en tu casa)._
3. Configura tu API Key de Groq creando un archivo `.env` en esa misma carpeta, con este contenido:
   ```env
   GROQ_API_KEY=tu_api_key_aqui
   ```
4. Arranca el servidor:
   ```bash
   python servidor.py
   ```
   _Te dirá que corre en `http://0.0.0.0:5000` (En tu red local)_.

### 2. Configuración del ESP32 (MicroPython)

1. Conecta tu ESP32 por USB y abre Thonny IDE.
2. Asegúrate de tener instalado **MicroPython**.
3. Abre el archivo `config.py` dentro de la carpeta `firmware/` y modifícalo con tus credenciales:
   ```python
   SSID = "TU_REDE_WIFI"
   PASSWORD = "TU_CONTRASEÑA"
   # Si tu servidor se está ejecutando en tu PC dentro de la misma red local,
   # pon la IP local de tu PC. Ej: "192.168.1.100" (y PUERTO=5000)
   # Si subiste el backend a Render, usa el link provisto.
   SERVIDOR = "esp32-ai-assistant-35r2.onrender.com"
   PUERTO = 443
   ```
4. Sube **todos** los archivos de la carpeta `firmware` (exceptuando `/servidor`) a la raíz y memoria principal (`/`) del ESP32.
5. Resetea el ESP32 (presionando EN/RST).

---

## Guía de Uso

1. **Encendido:** Conecta el ESP32 a la corriente. Verás la pantalla OLED encender en "Modo reposo" (carita durmiendo: `(-_-)` Zzz).
2. **Inicia Interacción:** Tienes dos formas de interactuar con el asistente:
   - **Por Botón:** Mantén presionado el botón conectado al Pin 14.
   - **Por Wake Word:** Di la palabra **"Luna"** cerca del micrófono. El asistente detectará tu voz automáticamente.
3. **Habla al Micrófono:** La pantalla mostrará que está sorprendida y atenta escuchando las ondas de voz. 
4. **Espera:** Suelta el botón (o termina de hablar). La cara cambiará a "pensando". El audio se sube al servidor, se transcribe y la IA genera un texto que luego se descarga en voz.
5. **Respuesta Automática:** La cara cambiará a modo "¿Feliz?" o hablando, se moverá la boca simulada, y el altavoz reproducirá tu respuesta.

---

## Estructura del Código

```text
Asistente/
├── firmware/
│   ├── main.py           # Bucle principal de eventos y manejador de flujos del ESP.
│   ├── config.py         # Archivo de configuración Global (SSIDs y Hosts).
│   ├── cliente.py        # Funciones que arman los requests e interactúan con el backend.
│   ├── grabar.py         # Configuración y grabación de audio con I2S (I2S.MONO).
│   ├── reproductor.py    # Manejo de la salida de audio PCM 8-Bit usando Pines DAC internos.
│   ├── pantalla.py       # Primitivas gráficas para la UI / Caritas EMO de la pantalla OLED SH1106.
│   ├── sh1106.py         # Librería del controlador de la pantalla I2C.
│   ├── wifi.py           # Script para manejar la conexión e inicialización WiFi.
│   └── servidor/
│       ├── servidor.py   # API Backend de Flask. Expone /transcribir, /preguntar, /hablar, /despertar y /reset.
│       └── requirements.txt # Dependencias pip para el servidor Python.
└── hardware/
    └── Asistente.kicad_pro y pcbs # Archivos en KiCad de la placa electrónica impresa.
```

¡Disfruta experimentando con tu asistente AI embebido!
