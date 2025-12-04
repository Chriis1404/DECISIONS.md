```markdown
# 🧠 Validación de Aprendizaje

### 1. Conceptos Fundamentales
**¿Qué es un Socket?**
Es una abstracción de software que sirve como punto final ("endpoint") para enviar o recibir datos a través de una red. Se define por la combinación de una **Dirección IP** (quién es la máquina) y un **Puerto** (qué programa es).

**¿Por qué requiere un puerto?**
Porque una computadora puede tener muchos programas usando la red al mismo tiempo (Navegador, Spotify, Zoom, EcoMarket). El puerto (ej. 5000) es el número que le dice al sistema operativo a qué aplicación entregarle el paquete de datos.

---

### 2. Preguntas de Reflexión

**A. ¿Por qué el cliente UDP puede "enviar" aun cuando el servidor no está activo?**
Porque UDP es un protocolo **Connectionless** (Sin conexión). No realiza el saludo de tres vías (*Three-way handshake*) que hace TCP para establecer el canal antes de transmitir. Simplemente empaqueta los datos y los lanza a la red esperando lo mejor.

**B. ¿Qué error aparece al desconectar el servidor TCP? ¿Por qué?**
Aparece `ConnectionRefusedError` (al conectar) o `ConnectionResetError` (durante la transmisión). Sucede porque el sistema operativo del servidor envía un paquete `RST` (Reset) indicando que no hay ningún proceso escuchando en ese puerto o que la conexión se rompió.

**C. ¿En qué casos elegirías TCP y en cuáles UDP?**

| Protocolo | Escenario Real | Justificación |
| :--- | :--- | :--- |
| **TCP** | **EcoMarket (Ventas)** | No podemos permitir que se pierda una orden de compra o que llegue incompleta. La integridad es prioridad. |
| **TCP** | **WhatsApp (Texto)** | Un mensaje debe llegar completo y en orden. |
| **UDP** | **Zoom / Videollamada** | Si se pierde un paquete de video, es mejor que la imagen parpadee un milisegundo a que la llamada se congele esperando retransmitir ese pixel perdido. |
| **UDP** | **Gaming Online** | La posición del jugador debe actualizarse en tiempo real. Datos viejos no sirven. |
