import socket

HOST = "0.0.0.0"
PORT = 5001

print(f"🚀 [UDP] Iniciando servidor en {HOST}:{PORT}...")
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    print(f"✅ [UDP] Servidor listo (Sin conexión, solo espera paquetes).")
    while True:
        data, addr = s.recvfrom(1024)
        print(f"📩 [UDP] De {addr} -> {data.decode('utf-8')}")
        s.sendto(data, addr)  # Eco
