---

## 2. Archivo: `INFORME_HITO_2.md`

Copia todo el contenido dentro de este bloque y pégalo en un archivo nuevo llamado `INFORME_HITO_2.md` en la misma carpeta.

```markdown
# 📄 Informe Técnico: Hito 2 - Escalabilidad y Resiliencia en EcoMarket

**Autor:** [Tu Nombre]
**Fecha:** 5 de noviembre de 2025

---

## 1. Justificación de Escalabilidad (Horizontal vs. Vertical)

Para la evolución de la API Central de EcoMarket, se optó por una estrategia de **escalabilidad horizontal** (escalar "hacia afuera") en lugar de una vertical (escalar "hacia arriba").

* **Escalabilidad Vertical** implica aumentar los recursos de una sola máquina (más CPU, más RAM). Aunque es simple de implementar inicialmente, tiene un límite físico, es costoso y presenta un **punto único de fallo** (SPOF). Si esa única máquina falla, todo el servicio de la central se cae.

* **Escalabilidad Horizontal**, la estrategia implementada, implica añadir más instancias del servicio (más contenedores) y distribuir la carga entre ellas.

### Ventajas de la Escalabilidad Horizontal (Lo que logramos):

1.  **Alta Disponibilidad (Resiliencia):** Esta es la ventaja principal. Al tener dos instancias (`central-api-1` y `central-api-2`), si una de ellas falla o se detiene para mantenimiento, el balanceador de carga Nginx la detecta y redirige automáticamente todo el tráfico a la instancia saludable. **El servicio nunca se interrumpe para el usuario**, como se demuestra en el video de prueba.

2.  **Mayor Throughput (Rendimiento):** Podemos manejar un mayor número de peticiones simultáneas. Si una sola instancia podía manejar 100 peticiones/segundo, dos instancias pueden manejar (teóricamente) 200 peticiones/segundo. La carga se reparte, evitando que una sola instancia se sature.

3.  **Costo-Efectividad y Flexibilidad:** Es generalmente más barato añadir múltiples "máquinas" pequeñas que mantener una sola máquina "gigante". Podemos escalar de 2 a 5 instancias durante picos de demanda (como el Black Friday) y volver a 2 en horas valle.

### Retos Abordados:

El principal reto de la escalabilidad horizontal es la **gestión del estado**. Si cada API tuviera su propia base de datos, el sistema sería inconsistente.

Lo solucionamos de la siguiente manera:
* **Estado de Base de Datos (Inventario, Ventas, Usuarios):** Se centralizó en **Redis**. Ambas instancias de la API se conectan a la *misma* base de datos de Redis, asegurando que ambas vean el mismo stock y la misma lista de usuarios.
* **Estado de Tareas (Notificaciones):** Se desacopló usando **RabbitMQ**. Cuando una sucursal envía una venta (Modo 6 - Fanout), RabbitMQ la entrega a *ambas* instancias. Para evitar que ambas procesen la misma venta (duplicando el descuento de stock o el contador de usuarios), se implementó **idempotencia** usando un "lock" en Redis (`sale_lock:` y `user_event_lock:`), asegurando que solo la primera instancia en recibir el mensaje lo procese.

## 2. Distribución Lograda (Resultados)

Se implementó un balanceador de carga Nginx que actúa como proxy reverso para las dos instancias de la API Central.

* **Algoritmo Utilizado:** `Round Robin` (el algoritmo por defecto de Nginx). Este método distribuye cada nueva petición a la siguiente instancia en la lista, en un ciclo.
* **Evidencia (Logs):** Al refrescar el dashboard de la central (`http://localhost/dashboard`) repetidamente, los logs de Docker muestran claramente la alternancia:

    ```bash
    central-api-1 | INFO:  172.18.0.7:55930 - "GET /dashboard HTTP/1.0" 200 OK
    central-api-2 | INFO:  172.18.0.7:49522 - "GET /dashboard HTTP/1.0" 200 OK
    central-api-1 | INFO:  172.18.0.7:55946 - "GET /dashboard HTTP/1.0" 200 OK
    central-api-2 | INFO:  172.18.0.7:49536 - "GET /dashboard HTTP/1.0" 200 OK
    ```

* **Prueba de Fallo:** Al ejecutar `docker stop central-api-1`, se observó que el dashboard seguía funcionando sin errores. Los logs mostraron que el 100% de las peticiones se redirigían instantáneamente a `central-api-2`, validando la configuración de alta disponibilidad.

## 3. Mejoras Futuras

Aunque el sistema actual es robusto, se pueden implementar las siguientes mejoras:

1.  **Auto-scaling:** Utilizar un orquestador más avanzado como **Kubernetes** o **Docker Swarm** para monitorear la carga (CPU/RAM) de las instancias y automáticamente "escalar" (añadir más contenedores) durante picos de demanda y "desescalar" (eliminarlos) cuando la demanda baje.

2.  **Métricas y Monitoreo:** Implementar **Prometheus** y **Grafana**. Prometheus recolectaría métricas detalladas (número de peticiones/seg, tasa de errores 5xx, latencia, longitud de la cola en RabbitMQ) y Grafana las mostraría en dashboards visuales para monitorear la salud del sistema en tiempo real.

3.  **Algoritmo de Balanceo Avanzado:** En producción, cambiar de `Round Robin` a `least_conn` (Menos Conexiones). Este algoritmo envía la nueva petición a la instancia que tenga el menor número de conexiones activas, siendo más eficiente si algunas peticiones son más "pesadas" (tardan más) que otras.
