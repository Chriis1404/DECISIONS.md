import socket
import time

HOST = "127.0.0.1"
PORT = 5000

print(f"🔄 [TCP] Intentando conectar a {HOST}:{PORT}...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"✅ [TCP] Conectado exitosamente.")
    
    mensajes = ["Hola Mundo", "Esto es TCP", "Adiós"]
    
    for msg in mensajes:
        print(f"📤 [TCP] Enviando: {msg}")
        s.sendall(msg.encode('utf-8'))
        data = s.recv(1024)
        print(f"📥 [TCP] Eco recibido: {data.decode('utf-8')}")
        time.sleep(1)
