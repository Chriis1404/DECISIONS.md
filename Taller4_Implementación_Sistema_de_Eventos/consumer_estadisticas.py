import pika
import json

# --- CONFIGURACIÓN ---
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'ecomarket_user'
RABBITMQ_PASS = 'ecomarket_password'
EXCHANGE_NAME = 'user_events_fanout'

contador_usuarios = 0

def callback(ch, method, properties, body):
    global contador_usuarios
    data = json.loads(body)
    
    if data.get('event_type') == 'UsuarioCreado':
        contador_usuarios += 1
        print(f" [📊 Estadísticas] Nuevo registro detectado. Total sesión: {contador_usuarios}")
        print(f"     Usuario: {data.get('email')} | ID: {data.get('id')}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)

    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

        # Cola exclusiva para este consumidor
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

        print(' [*] Servicio de ESTADÍSTICAS esperando eventos. Para salir presiona CTRL+C')

        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        channel.start_consuming()

    except KeyboardInterrupt:
        print('Interrumpido')
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_consumer()
