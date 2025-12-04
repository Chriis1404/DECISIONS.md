import requests
import time
from collections import Counter

URL = "http://localhost:80" # Apunta al Balanceador
TOTAL_REQUESTS = 50

print(f"🚀 Iniciando prueba de carga: {TOTAL_REQUESTS} peticiones a {URL}...")

responses = []

for i in range(TOTAL_REQUESTS):
    try:
        # Asumimos que la API devuelve un header o body con su ID
        # En CentralAPI.py agregamos: headers={"X-Server-ID": os.getenv("SERVER_NAME")}
        res = requests.get(URL)
        server_id = res.json().get("server_name", "Unknown")
        responses.append(server_id)
        print(f"Req #{i+1}: Atendida por {server_id}")
    except Exception as e:
        print(f"Req #{i+1}: Fallo ({e})")
    time.sleep(0.1)

print("\n📊 RESULTADOS DE BALANCEO:")
counts = Counter(responses)
for server, count in counts.items():
    print(f" -> {server}: {count} peticiones ({count/TOTAL_REQUESTS*100:.1f}%)")
