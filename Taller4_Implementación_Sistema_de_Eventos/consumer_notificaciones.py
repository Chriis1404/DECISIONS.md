import pika
import json
import time

# --- CONFIGURACIÓN ---
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'ecomarket_user'
RABBITMQ_PASS = 'ecomarket_password'
EXCHANGE_NAME = 'user_events_fanout'

def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f" [📧 Notificaciones] Recibido evento para: {data.get('email')}")
    
    # Simular tiempo de procesamiento (enviar email)
    time.sleep(1) 
    
    print(f" [✅] Email de bienvenida enviado a {data.get('nombre')}.")
    # Confirmar que procesamos el mensaje correctamente
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)

    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Aseguramos que el exchange exista
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

        # Creamos una cola TEMPORAL y EXCLUSIVA para este consumidor
        # Esto es clave en Pub/Sub: cada consumidor tiene su propia cola
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        # "Suscribimos" la cola al exchange
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

        print(' [*] Servicio de NOTIFICACIONES esperando eventos. Para salir presiona CTRL+C')

        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        channel.start_consuming()

    except KeyboardInterrupt:
        print('Interrumpido')
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_consumer()
