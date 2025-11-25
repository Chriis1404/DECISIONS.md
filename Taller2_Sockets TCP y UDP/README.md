# 🔌 **Taller 2: Sockets TCP/UDP**
![Python](https://img.shields.io/badge/Python-Sockets-yellow?logo=python)
![C#](https://img.shields.io/badge/C%23-.NET-purple?logo=dotnet)
![Network](https://img.shields.io/badge/Protocol-TCP%2FUDP-blue)

### 📡 *Fundamentos de Comunicaciones en Red*

📅 **Fecha:** 17 de Octubre de 2025 (Reconstrucción Histórica)  
👤 **Autores:** Christofer Roberto Esparza Chavero, Brian Garcia y Juan Cordova

---

## 🎯 **Objetivos**
Comprender la diferencia fundamental entre protocolos orientados a conexión (**TCP**) y no orientados a conexión (**UDP**) mediante la implementación de un sistema Cliente-Servidor de "Eco" en dos lenguajes diferentes.

---

## 📚 **Conceptos Clave**

Antes de la implementación, definimos los componentes base:

* **Socket:** Punto final de comunicación bidireccional (IP + Puerto).
* **Puerto:** Número que identifica a un proceso dentro de una máquina (ej. 5000).
* **Buffer:** Memoria temporal para almacenar datos mientras se transmiten.

---

## 📂 **Estructura del Taller**

Este taller implementa sockets en dos lenguajes para comparar su comportamiento:

- [📂 **Python Scripts**](./python/) - Implementación rápida y funcional.
- [📂 **C# / .NET**](./dotnet/) - Implementación tipada para entornos empresariales.

---

## 🛠️ **Instrucciones de Ejecución**

Para probar el sistema de Eco:

1. **Servidor (Terminal 1):**
    ```bash
    python python/tcp_server.py
    ```

2. **Cliente (Terminal 2):**
    ```bash
    python python/tcp_client.py
    ```

---

## 🧪 **Experimentos y Resultados**

### 🆚 Comparativa TCP vs UDP

| Característica | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |
| :--- | :--- | :--- |
| **Conexión** | Requiere "Handshake" antes de enviar. | Envía sin establecer conexión ("Fire and forget"). |
| **Fiabilidad** | Garantiza llegada y orden. | No garantiza llegada ni orden. |
| **Velocidad** | Más lento por verificaciones. | Extremadamente rápido. |
| **Uso ideal** | Web, Emails, Transferencia de archivos. | Streaming, Juegos online, VoIP. |

---

## 🔬 **Evidencias de Pruebas (Logs)**

### 1️⃣ Prueba de Conexión Caída (TCP)

**Experimento:** Se conectó el cliente y luego se cerró el servidor abruptamente.

```text
🔄 [TCP] Intentando conectar a 127.0.0.1:5000...
✅ [TCP] Conectado exitosamente.
📤 [TCP] Enviando: Hola Mundo
📥 [TCP] Eco recibido: Hola Mundo
... (Servidor se apaga) ...
❌ Error: ConnectionResetError: [WinError 10054] Se ha forzado la interrupción de una conexión existente.
```

---

### 2️⃣ Prueba Sin Servidor (UDP)

**Experimento:** Se ejecutó el cliente UDP sin levantar servidor.

**Resultado:** El cliente envió sin error, pero no hubo respuesta.

```text
🚀 [UDP] Cliente listo para enviar a 127.0.0.1:5001
📤 [UDP] Enviando: Mensaje 1 UDP
⚠️ [UDP] Tiempo de espera agotado (Paquete perdido o servidor apagado).
📤 [UDP] Enviando: Mensaje 2 UDP
```

---

### 3️⃣ Prueba de Buffer (Fragmentación)

**Experimento:** Se redujo el buffer de 1024 bytes a 8 bytes.

**Resultado:** Los mensajes llegaron fragmentados.

```text
Mensaje enviado: "Hola este es un mensaje largo"
Recibido (Parte 1): "Hola est"
Recibido (Parte 2): "e es un "
Recibido (Parte 3): "mensaje "
```

---

## 🧠 **Reflexión Final**

1. **¿Por qué UDP puede enviar aun sin servidor?**  
   Porque no establece conexión previa. Si nadie recibe el paquete, simplemente se pierde y el cliente no lo sabe inmediatamente.

2. **¿Cuándo elegir TCP y cuándo UDP?**

   - **TCP:**  
     Para transacciones críticas donde la integridad es prioridad (APIs, banca, chats, EcoMarket).
   - **UDP:**  
     Para comunicaciones en tiempo real donde es mejor perder datos antes que tener retraso (streaming, sensores IoT, videollamadas).

---

### 🎯 Estado del Taller: **✅ Completado**
