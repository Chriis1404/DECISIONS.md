import socket
import time

HOST = "127.0.0.1"
PORT = 5001

print(f"🚀 [UDP] Cliente listo para enviar a {HOST}:{PORT}")
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    mensajes = ["Mensaje 1 UDP", "Mensaje 2 UDP", "Mensaje 3 UDP"]
    
    for msg in mensajes:
        print(f"📤 [UDP] Enviando: {msg}")
        s.sendto(msg.encode('utf-8'), (HOST, PORT))
        
        # Esperamos respuesta (eco)
        try:
            s.settimeout(2) # Timeout por si se pierde el paquete
            data, _ = s.recvfrom(1024)
            print(f"📥 [UDP] Eco recibido: {data.decode('utf-8')}")
        except socket.timeout:
            print("⚠️ [UDP] Paquete perdido o servidor apagado.")
        
        time.sleep(1)
