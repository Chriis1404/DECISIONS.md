# ⚙️ Taller 4: Implementación de Pub/Sub con Fanout Exchange

Este taller demuestra el patrón Publisher/Subscriber, resolviendo el acoplamiento síncrono.

## 🚀 Pasos de Validación

1.  **Asegurar Infraestructura:** Inicia RabbitMQ (asumiendo que está en tu `docker-compose.yml` con el nombre `rabbitmq`).
    ```bash
    docker-compose up -d rabbitmq
    ```

2.  **Iniciar Consumers (Terminales separadas):** Abre dos terminales separadas para ver las reacciones independientes:
    ```bash
    python consumer_notificaciones.py  # Terminal 1: Verá el email
    python consumer_estadisticas.py    # Terminal 2: Verá el conteo
    ```

3.  **Publicar Evento:** Abre una tercera terminal y ejecuta el publisher (simulando que el Servicio de Usuarios ha creado un registro):
    ```bash
    python publisher.py
    ```

## ✅ Evidencia de Desacoplamiento

Una vez publicado, ambas terminales (Notificaciones y Estadísticas) deben mostrar los logs simultáneamente, sin que el servicio de Registro (`publisher.py`) sepa cuántos o quiénes consumen el evento.
