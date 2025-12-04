# 🌿 **EcoMarket: Arquitectura de Sistemas Distribuidos**

![Status](https://img.shields.io/badge/Estado-Finalizado-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-yellow)
![Docker](https://img.shields.io/badge/Infra-Docker_Compose-blue)
![Security](https://img.shields.io/badge/Security-JWT_%2B_HTTPS-red)

**EcoMarket** es un proyecto integral de ingeniería de software diseñado para explorar, implementar y asegurar una arquitectura de sistemas distribuidos escalable. A lo largo del semestre, el sistema evolucionó desde un script monolítico hasta una plataforma de microservicios segura y resiliente.

---

## 🗺️ **Mapa del Proyecto (Evolución Semanal)**

Este repositorio documenta la transformación técnica del sistema a través de hitos clave. Cada carpeta contiene el código, la documentación y las evidencias correspondientes a esa fase.

### 🏗️ **Fase 1: Fundamentos**
* **[Taller 1: Arquitectura Monolítica](./Taller1_Arquitectura_Monolitica)**
    * *Objetivo:* Crear la primera API REST básica en memoria.
    * *Tech:* Python, FastAPI (Sin BD).
* **[Taller 2: Comunicación de Bajo Nivel](./Taller2_Sockets_TCP_UDP)**
    * *Objetivo:* Entender cómo viajan los datos implementando Sockets TCP/UDP.
    * *Tech:* Scripts de Python y C# (.NET).

### 📡 **Fase 2: Distribución y Escalabilidad**
* **[Taller 3: Arquitectura Distribuida](./Taller3_Arquitectura_Distribuida)**
    * *Objetivo:* Desacoplar el sistema en Central y Sucursal.
    * *Logro:* Implementación de **Autonomía Local (Offline-First)** y patrón **Circuit Breaker**.
* **[Taller 4: Comunicación Asíncrona (Pub/Sub)](./Taller4_Implementacion_Sistema_Distribuido)**
    * *Objetivo:* Implementar colas de mensajería para desacoplamiento total.
    * *Tech:* **RabbitMQ** (Fanout Exchange) y **Redis**.
* **[Taller 5: Alta Disponibilidad](./Taller5_Disponibilidad_Escalabilidad_Balanceo)**
    * *Objetivo:* Escalar la API Central horizontalmente.
    * *Tech:* **Nginx** como Balanceador de Carga (Load Balancer).
* **[Taller 6: Persistencia Distribuida](./Taller6_Distribucion)**
    * *Objetivo:* Implementar un clúster de base de datos real.
    * *Tech:* **PostgreSQL** con replicación Maestro-Esclavo.

### 🛡️ **Fase 3: Seguridad y Blindaje (Hito 2)**
* **[Taller 7: Autenticación y Autorización](./Taller7_Seguridad_JWT)**
    * *Objetivo:* Proteger el sistema contra accesos no autorizados.
    * *Tech:* **JWT (JSON Web Tokens)**, Hashing de contraseñas (`bcrypt`) y Middleware de seguridad.
* **[Taller 8: HTTPS y Secretos (Final)](./Taller8_HTTPS_y_Secretos)**
    * *Objetivo:* Cifrar el transporte y proteger la configuración.
    * *Tech:* **SSL/TLS (HTTPS)** con Nginx y gestión de secretos con `.env` (12-Factor App).

---

## 🚀 **Cómo Ejecutar la Versión Final (Segura)**

Para levantar el sistema completo con todas las mejoras de seguridad y distribución:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/Chriis1404/DECISIONS.md.git](https://github.com/Chriis1404/DECISIONS.md.git)
    cd DECISIONS.md
    ```

2.  **Configurar Secretos:**
    Copia el archivo de ejemplo para crear tus variables de entorno locales.
    ```bash
    cp .env.example .env
    ```

3.  **Desplegar con Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Acceder al Sistema:**
    * **Dashboard Seguro:** `https://localhost` (Acepta el certificado autofirmado).
    * **Credenciales Admin:** Usuario: `admin` / Contraseña: `admin123`.

---

## 👥 **Equipo de Desarrollo**
* **Christofer Roberto Esparza Chavero**
* Brian Garcia
* Juan Cordova

---
*Proyecto desarrollado para la materia de Programación del Lado del Servidor - 2025.*
