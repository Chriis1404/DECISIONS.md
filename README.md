# 🌿 **EcoMarket: Arquitectura de Sistemas Distribuidos Seguros**

![Status](https://img.shields.io/badge/Estado-Producción_Local-success?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Backend-FastAPI-yellow?style=for-the-badge&logo=fastapi&logoColor=black)
![Security](https://img.shields.io/badge/Security-JWT_%2B_HTTPS-red?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Infra](https://img.shields.io/badge/Infra-Nginx_%2B_RabbitMQ-blue?style=for-the-badge&logo=nginx)

> **Hito 2 Finalizado:** Transformación completa de un script monolítico
> a una plataforma de microservicios distribuida, resiliente y blindada
> con seguridad de grado industrial.

------------------------------------------------------------------------

## 🏗️ **Arquitectura Final del Sistema (Hito 2)**

El sistema opera bajo un modelo **Zero-Trust Network** simulado, donde
el tráfico es cifrado y gestionado por un Gateway seguro.

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

  -------------------------------------------------------------------------------
  Servicio        URL de Acceso                 Descripción Técnica
  --------------- ----------------------------- ---------------------------------
  🔒 Secure       https://localhost             Punto de entrada único. Maneja
  Gateway                                       Terminación SSL y redirige
                                                tráfico HTTP a HTTPS.

  🛡️ Central      https://localhost/dashboard   Panel administrativo protegido
  Dashboard                                     por JWT. Gestiona el inventario
                                                maestro.

  🏪 Sucursal     http://localhost:8002         Nodo cliente autónomo
  Demo                                          (Offline-First). Simula ventas y
                                                sincronización asíncrona.

  🐰 RabbitMQ     http://localhost:15672        Broker de mensajería. User:
  Admin                                         ecomarket_user / Pass:
                                                ecomarket_password

  📚              https://localhost/docs        Swagger UI automático generado
  Documentación                                 por FastAPI.
  API                                           
  -------------------------------------------------------------------------------

------------------------------------------------------------------------

## 🛠️ Guía de Despliegue Rápido

El proyecto implementa la metodología **12-Factor App**, por lo que la
configuración está externalizada.

### 1. Configuración de Secretos

Crea un archivo `.env` en la raíz basado en la plantilla segura:

``` bash
cp .env.example .env
# (Opcional) Edita .env con tus propias claves si lo deseas
```

### 2. Despliegue con Docker

Construye y levanta la infraestructura completa:

``` bash
docker-compose up -d --build
```

### 3. Validación

-   Accede a `http://localhost` → El navegador te redirigirá a HTTPS.
-   Acepta el certificado autofirmado (generado para desarrollo local).
-   Credenciales Admin:\
    Usuario: **admin**\
    Contraseña: **admin123**

------------------------------------------------------------------------

## 🗺️ Hoja de Ruta: Evolución del Proyecto

Este repositorio documenta la historia técnica de EcoMarket a través de
8 talleres intensivos.

### 🟢 Fase 1: Fundamentos (Monolito)

-   Taller 1: Arquitectura Monolítica - API básica en memoria.
-   Taller 2: Sockets TCP/UDP - Comunicación de bajo nivel.

### 🟡 Fase 2: Distribución (Escalabilidad)

-   Taller 3: Arquitectura Distribuida - Separación Cliente-Servidor y
    Circuit Breaker.
-   Taller 4: Sistema de Eventos (Pub/Sub) - Desacoplamiento con
    RabbitMQ y Redis.
-   Taller 5: Alta Disponibilidad - Balanceo de carga con Nginx.
-   Taller 6: Persistencia Distribuida - Clúster de Base de Datos
    PostgreSQL.

### 🔴 Fase 3: Seguridad (Blindaje Final)

-   Taller 7: Autenticación JWT - Identidad Stateless y Hashing.
-   Taller 8: HTTPS y Secretos - Cifrado de transporte y gestión de
    configuración.

------------------------------------------------------------------------

## 🛡️ Auditoría de Seguridad (Hito 2)

El sistema cumple con los pilares de la **Tríada CIA**:

-   **Confidencialidad:** Tráfico 100% cifrado vía TLS 1.3. Secretos
    fuera del código fuente.
-   **Integridad:** Tokens JWT firmados (HS256) y contraseñas hasheadas
    (bcrypt).
-   **Disponibilidad:** Arquitectura redundante capaz de soportar la
    caída de contenedores individuales.

➡️ Ver Informe Técnico Completo y Auditoría

------------------------------------------------------------------------

## 👥 Créditos

Desarrollado por el equipo de Ingeniería de Software:

-   Christofer Roberto Esparza Chavero\
-   Brian Garcia\
-   Juan Cordova

Proyecto para la asignatura de **Programación del Lado del Servidor -
2025**.
