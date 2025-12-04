# 🌿 EcoMarket --- Arquitectura de Sistemas Distribuidos Seguros

![Status](https://img.shields.io/badge/Estado-Producción_Local-success?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Backend-FastAPI-yellow?style=for-the-badge&logo=fastapi&logoColor=black)
![Security](https://img.shields.io/badge/Security-JWT_%2B_HTTPS-red?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Infra](https://img.shields.io/badge/Infra-Nginx_%2B_RabbitMQ-blue?style=for-the-badge&logo=nginx)

> ✅ **Hito 2 Finalizado**\
> Transformación completa de un script monolítico a una **plataforma de
> microservicios distribuida, resiliente y blindada con seguridad de
> grado industrial**.

------------------------------------------------------------------------

## 🏗️ Arquitectura Final del Sistema (Hito 2)

El sistema opera bajo un modelo **Zero-Trust Network** simulado, donde
todo el tráfico es **cifrado, validado y controlado** por un Gateway
seguro.

``` mermaid
graph TD
    User((👤 Cliente)) -->|HTTPS / TLS 1.3| Nginx[🔒 Nginx Gateway<br/>(Puerto 443)]

    subgraph "Red Privada (Docker Cluster)"
        Nginx -->|Balanceo| Central[🛡️ Central API<br/>(Cluster)]

        Sucursal[🏪 Sucursal Autónoma] -->|AMQP (Ventas)| Rabbit[🐰 RabbitMQ]
        Sucursal -->|HTTPS (Sync)| Nginx

        Central -->|Persistencia| DB[(🐘 PostgreSQL<br/>Replicado)]
        Central -->|Eventos| Rabbit

        Env[📄 .env] -.->|Inyección de Secretos| Central
        Env -.->|Inyección de Secretos| DB
    end
```

------------------------------------------------------------------------

## 🚀 Servicios Activos y Accesos

  ---------------------------------------------------------------------------------
  Servicio          URL de Acceso                 Descripción Técnica
  ----------------- ----------------------------- ---------------------------------
  🔒 **Secure       https://localhost             Punto de entrada único. Maneja
  Gateway**                                       terminación SSL y redirige
                                                  tráfico HTTP a HTTPS

  🛡️ **Central      https://localhost/dashboard   Panel administrativo protegido
  Dashboard**                                     por JWT. Gestiona el inventario
                                                  maestro

  🏪 **Sucursal     http://localhost:8002         Nodo autónomo (Offline-First).
  Demo**                                          Simula ventas y sincronización
                                                  asíncrona

  🐰 **RabbitMQ     http://localhost:15672        Broker de mensajería --- User:
  Admin**                                         `ecomarket_user` / Pass:
                                                  `ecomarket_password`

  📚                https://localhost/docs        Swagger UI generado
  **Documentación                                 automáticamente con FastAPI
  API**                                           
  ---------------------------------------------------------------------------------

------------------------------------------------------------------------

## 🛠️ Guía de Despliegue Rápido

EcoMarket implementa la metodología **12-Factor App**, manteniendo toda
la configuración externalizada.

### 1️⃣ Configuración de secretos

Crea el archivo `.env` en la raíz del proyecto:

``` bash
cp .env.example .env
# (Opcional) Edita el .env con tus propias claves
```

### 2️⃣ Despliegue con Docker

Construye y levanta todo el ecosistema:

``` bash
docker-compose up -d --build
```

### 3️⃣ Validación

-   Ingresa a `http://localhost` → serás redirigido automáticamente a
    HTTPS\
-   Acepta el certificado autofirmado (válido en entorno local)

**Credenciales admin:**\
Usuario: **admin**\
Contraseña: **admin123**

------------------------------------------------------------------------

## 🗺️ Hoja de Ruta --- Evolución del Proyecto

### 🟢 Fase 1 --- Fundamentos (Monolito)

-   Taller 1: Arquitectura Monolítica\
-   Taller 2: Sockets TCP/UDP

### 🟡 Fase 2 --- Distribución

-   Taller 3: Arquitectura Distribuida\
-   Taller 4: Sistema de Eventos (Pub/Sub)\
-   Taller 5: Alta Disponibilidad\
-   Taller 6: Persistencia Distribuida

### 🔴 Fase 3 --- Seguridad

-   Taller 7: Autenticación JWT\
-   Taller 8: HTTPS y Secretos

------------------------------------------------------------------------

## 🛡️ Auditoría de Seguridad

El sistema cumple con la **Tríada CIA**:

-   **Confidencialidad** --- TLS 1.3, secretos fuera del código\
-   **Integridad** --- JWT HS256, bcrypt\
-   **Disponibilidad** --- Arquitectura tolerante a fallos

------------------------------------------------------------------------

## 👥 Créditos

-   Christofer Roberto Esparza Chavero\
-   Brian Garcia\
-   Juan Cordova

Proyecto académico --- **Programación del Lado del Servidor 2025**
