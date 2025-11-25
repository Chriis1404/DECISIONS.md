import socket

HOST = "0.0.0.0"
PORT = 5000

print(f"🚀 [TCP] Iniciando servidor en {HOST}:{PORT}...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"✅ [TCP] Servidor escuchando. Esperando cliente...")
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"🔗 [TCP] Conexión establecida con {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    print(f"❌ [TCP] Cliente {addr} cerró la conexión")
                    break
                print(f"📩 [TCP] Recibido: {data.decode('utf-8')}")
                conn.sendall(data)  # Eco: devuelve lo mismo
