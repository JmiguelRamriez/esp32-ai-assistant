import usocket
import ussl
import config
import os

def transcribir(nombre="audio.wav"):
    tam = os.stat(nombre)[6]
    boundary = "boundary123"
    
    parte1 = (
        "--boundary123\r\n"
        "Content-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n"
        "Content-Type: audio/wav\r\n\r\n"
    ).encode()
    
    parte2 = (
        "\r\n--boundary123\r\n"
        "Content-Disposition: form-data; name=\"model\"\r\n\r\n"
        "whisper-large-v3-turbo\r\n"
        "--boundary123--\r\n"
    ).encode()
    
    content_length = len(parte1) + tam + len(parte2)
    
    addr = usocket.getaddrinfo("api.groq.com", 443)[0][-1]
    sock = usocket.socket()
    sock.connect(addr)
    sock = ussl.wrap_socket(sock, server_hostname="api.groq.com")
    
    request = (
        "POST /openai/v1/audio/transcriptions HTTP/1.1\r\n"
        "Host: api.groq.com\r\n"
        "Authorization: Bearer " + config.API_KEY + "\r\n"
        "Content-Type: multipart/form-data; boundary=boundary123\r\n"
        "Content-Length: " + str(content_length) + "\r\n"
        "\r\n"
    ).encode()
    
    sock.write(request)
    sock.write(parte1)
    
    with open(nombre, 'rb') as f:
        buf = bytearray(512)
        while True:
            n = f.readinto(buf)
            if n == 0:
                break
            sock.write(buf[:n])
    
    sock.write(parte2)
    
    respuesta = sock.read(4096).decode()
    print(respuesta)
    sock.close()