# 🔌 **Taller 2: Sockets TCP/UDP**
![Python](https://img.shields.io/badge/Python-Sockets-yellow?logo=python)
![C#](https://img.shields.io/badge/C%23-.NET-purple?logo=dotnet)
![Network](https://img.shields.io/badge/Protocol-TCP%2FUDP-blue)

### 📡 *Fundamentos de Comunicaciones en Red*

📅 **Fecha:** 17 de Octubre de 2025 (Reconstrucción Histórica)
👤 **Autores:** Christofer Roberto Esparza Chavero, Brian Garcia y Juan Cordova

---

## 🎯 **Objetivos**
Comprender la diferencia fundamental entre protocolos orientados a conexión (**TCP**) y no orientados a conexión (**UDP**) mediante la implementación de un sistema Cliente-Servidor de "Eco".

---

## 📂 **Estructura del Taller**

Este taller implementa sockets en dos lenguajes para comparar su comportamiento:

- [📂 **Python Scripts**](./python/) - Implementación rápida y funcional.
- [📂 **C# / .NET**](./dotnet/) - Implementación tipada para entornos empresariales.

---

## 🧪 **Experimentos y Resultados**

### 🆚 Comparativa TCP vs UDP

| Característica | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |
| :--- | :--- | :--- |
| **Conexión** | Requiere "Handshake" (3 vías) antes de enviar datos. | "Fire and forget". Envía sin avisar. |
| **Fiabilidad** | Garantiza que los datos lleguen y en orden. | No garantiza llegada ni orden. |
| **Velocidad** | Más lento (por las verificaciones). | Extremadamente rápido. |
| **Uso ideal** | Web (HTTP), Emails, Archivos. | Streaming, Juegos Online, VoIP. |

### 🔬 Evidencias de Pruebas

#### 1. Prueba de Conexión Caída (TCP)
* **Experimento:** Se conectó el cliente y se apagó el servidor abruptamente.
* **Resultado:** El cliente lanzó una excepción `ConnectionRefusedError` o detectó el cierre del socket inmediatamente. TCP "sabe" cuando el otro lado desaparece.

#### 2. Prueba Sin Servidor (UDP)
* **Experimento:** Se ejecutó el cliente UDP sin prender el servidor.
* **Resultado:** El cliente envió los mensajes **sin dar error**. Simplemente no recibió respuesta (Eco). UDP no sabe si hay alguien escuchando al otro lado.

#### 3. Prueba de Buffer
* **Experimento:** Se redujo el buffer de lectura de 1024 bytes a 8 bytes.
* **Resultado:** Mensajes largos llegaban cortados en fragmentos, requiriendo múltiples ciclos de lectura para reconstruir el mensaje completo.

---

## 🧠 **Preguntas de Reflexión**

**1. ¿Por qué el cliente UDP puede "enviar" aun cuando el servidor no está activo?**
Porque UDP no establece una conexión previa. Simplemente lanza el paquete a la dirección IP indicada. Si nadie lo recibe, el paquete se pierde, pero el emisor no recibe notificación inmediata de fallo.

**2. ¿En qué casos elegirías TCP y en cuáles UDP?**
* **TCP:** Para sistemas bancarios, APIs REST (EcoMarket) o chat de texto, donde perder un solo dato es inaceptable.
* **UDP:** Para videollamadas o monitoreo de sensores en tiempo real, donde importa más la velocidad que perder un frame de video.

---

🎯 **Estado:** ✅ Completado
