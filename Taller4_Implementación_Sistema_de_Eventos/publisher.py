import pika
import json
import uuid
import time
from datetime import datetime

# --- CONFIGURACIÓN (Extraída de tu docker-compose) ---
# Si corres esto desde tu terminal de Windows, usa 'localhost'.
# Si estuviera dentro de Docker, sería 'rabbitmq'.
RABBITMQ_HOST = 'localhost' 
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'ecomarket_user'
RABBITMQ_PASS = 'ecomarket_password'
EXCHANGE_NAME = 'user_events_fanout'

def publish_event():
    # Datos simulados del usuario
    user_data = {
        "id": str(uuid.uuid4()),
        "nombre": "Usuario Taller 4",
        "email": f"usuario_{int(time.time())}@ecomarket.com",
        "timestamp": datetime.now().isoformat(),
        "event_type": "UsuarioCreado",
        "source": "Script_Publisher_Manual"
    }

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)

    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declaramos el Exchange tipo FANOUT (Broadcast)
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

        # Publicamos el mensaje
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key='', # En Fanout, la routing key se ignora
            body=json.dumps(user_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
            )
        )
        print(f" [x] Evento Enviado: UsuarioCreado ({user_data['email']})")
        connection.close()

    except Exception as e:
        print(f" [!] Error de conexión con RabbitMQ: {e}")
        print("     ¿Está corriendo el contenedor de RabbitMQ? (docker-compose up -d)")

if __name__ == "__main__":
    print("--- Simulador de Servicio de Usuarios (Publisher) ---")
    publish_event()
