# 📈 Evolución Arquitectónica Integral: De Monolito a Sistema Distribuido Seguro

Este documento narra la transformación técnica del proyecto **EcoMarket** a lo largo del ciclo de desarrollo. Describe cómo el sistema evolucionó desde un script básico hasta una arquitectura de microservicios segura, resiliente y lista para la nube.

---

## 🗓️ FASE 1: El Monolito Experimental (Talleres 1-2)
**"La etapa de prototipado y fundamentos"**

En el inicio, EcoMarket nació como una prueba de concepto para entender cómo funcionan las comunicaciones en red.

* **Arquitectura:** Monolítica y volátil. Toda la lógica (Inventario y Ventas) vivía en un solo proceso de Python.
* **Almacenamiento:** Variables en memoria RAM (`list` y `dict`).
    * *Problema Crítico:* Si el servidor se reiniciaba, todos los datos se perdían (falta de persistencia).
* **Comunicación:** Implementación cruda de Sockets TCP y UDP para entender el transporte de datos a bajo nivel.
* **Limitaciones:** El sistema no soportaba concurrencia real ni podía escalar. Era un "Juguete Técnico".

---

## 🗓️ FASE 2: Distribución y Desacoplamiento (Talleres 3-6)
**"La etapa de expansión y escalabilidad"**

El negocio requería abrir sucursales. Esto nos obligó a romper el monolito y adoptar una **Arquitectura Distribuida**.

### 2.1. Separación de Responsabilidades (Cliente-Servidor)
Dividimos el código en dos entidades autónomas:
* **Central API:** La "Verdad Única" del inventario.
* **Sucursal API:** Clientes autónomos que pueden operar incluso sin conexión a internet (**Offline-First**) gracias a cachés locales.

### 2.2. Orquestación con Docker
Introdujimos **Docker Compose** para gestionar la infraestructura. Pasamos de correr scripts manuales a tener un ecosistema de contenedores aislados y conectados por una red virtual interna.

### 2.3. Comunicación Asíncrona (Pub/Sub)
Para evitar que una caída en la Central detuviera las ventas en la Sucursal, implementamos patrones de mensajería:
* **RabbitMQ:** Implementamos un Exchange tipo `Fanout` para eventos de dominio (ej. "UsuarioCreado"). Esto permitió desacoplar los servicios; el emisor no necesita saber quién lo escucha.
* **Redis:** Utilizamos colas en memoria para procesar ráfagas de ventas a alta velocidad.

### 2.4. Persistencia y Alta Disponibilidad
* **PostgreSQL Clúster:** Implementamos una base de datos real con replicación (Maestro-Esclavo) para separar las lecturas de las escrituras y garantizar que los datos sobrevivieran a reinicios.
* **Nginx Load Balancer:** Colocamos un proxy inverso frente a la API Central para distribuir la carga entre múltiples réplicas, eliminando el punto único de fallo.

---

## 🗓️ FASE 3: Blindaje y Seguridad (Talleres 7-8 - Hito 2)
**"La etapa de profesionalización y defensa en profundidad"**

Con el sistema escalando, la superficie de ataque creció. La prioridad cambió de "Hacer que funcione" a "Hacer que sea seguro".

### 3.1. Identidad y Control de Acceso (Authentication)
Implementamos **JWT (JSON Web Tokens)**.
* *Antes:* Cualquiera podía enviar un POST a `/inventory`.
* *Ahora:* Implementamos un modelo **Stateless**. El servidor no guarda sesiones; valida criptográficamente la firma del token en cada petición. Esto es vital para que el Balanceador de Carga (Nginx) funcione correctamente sin "Sticky Sessions".

### 3.2. Protección de Datos en Reposo (Secrets Management)
Adoptamos la metodología **12-Factor App**.
* Eliminamos todas las credenciales hardcodeadas (`password123`) del código fuente.
* Implementamos inyección de variables de entorno mediante archivos `.env` no versionados. Esto previene fugas de seguridad si el repositorio se hace público.

### 3.3. Protección de Datos en Tránsito (Network Security)
Implementamos **Terminación SSL** en el Gateway.
* Configuramos Nginx para escuchar en el puerto **443 (HTTPS)** usando certificados TLS.
* Todo el tráfico desde el cliente hasta nuestra nube privada viaja cifrado, protegiendo los Tokens JWT contra ataques de intercepción (Man-in-the-Middle).

---

## 📊 Tabla Comparativa: Antes vs. Después

| Característica | Inicio del Semestre (Fase 1) | Final del Semestre (Fase 3) |
| :--- | :--- | :--- |
| **Topología** | Script único en local | Microservicios en Contenedores Docker |
| **Persistencia** | Memoria RAM (Volátil) | PostgreSQL Replicado + Redis |
| **Comunicación** | Síncrona (Bloqueante) | Asíncrona (RabbitMQ Pub/Sub) |
| **Escalabilidad** | Ninguna | Horizontal (Nginx + Réplicas) |
| **Seguridad** | Texto Plano (HTTP) | Cifrado (HTTPS TLS 1.3) |
| **Autenticación** | Inexistente | JWT Stateless + Hashing bcrypt |
| **Configuración** | Hardcodeada | Variables de Entorno (.env) |

---

## 🧠 Conclusión Técnica

EcoMarket ha completado su ciclo de maduración. Hemos construido una plataforma que cumple con los tres pilares fundamentales de la ingeniería de software moderna:

1.  **Escalabilidad:** Capaz de crecer en demanda agregando más contenedores.
2.  **Resiliencia:** Capaz de soportar fallos de red y caídas de servicios (Circuit Breaker + Colas).
3.  **Seguridad:** Protegida en sus tres capas: Datos (BD), Aplicación (JWT) y Transporte (HTTPS).

El sistema está listo para ser desplegado en un entorno de *Staging* o Nube.

---

### 🧩 Diagrama de Madurez del Proyecto

Este esquema resume visualmente el crecimiento de la plataforma:

```mermaid
graph LR
    F1[Fase 1: Monolito] -->|Docker + BD| F2[Fase 2: Distribuido]
    F2 -->|JWT + HTTPS| F3[Fase 3: Seguro]
    
    style F3 fill:#00c853,stroke:#333,stroke-width:2px,color:white
---

### 📂 Archivo 2: `RETO_IA_5_ARQUITECTURA_SEGURIDAD.md`
*(Este es el archivo nuevo que documenta el diseño de seguridad final. Guárdalo también en la carpeta `Taller8_HTTPS_y_Secretos/`).*

```markdown
# 🏗️ Reto IA #5: Diseño de Arquitectura de Seguridad Final

**Rol:** Arquitecto de Software  
**Sistema:** EcoMarket V.Final

---

## 1. Topología de Red Implementada

El sistema utiliza un patrón de **"Gateway Offloading"** donde Nginx maneja la seguridad perimetral, protegiendo la red interna de microservicios.

```mermaid
graph TD
    Client((📱 Cliente)) -->|HTTPS : 443| Nginx[🔒 Nginx Gateway]
    
    subgraph "EcoMarket Private Network"
        Nginx -->|HTTP : 8000| API[🐍 Central API Cluster]
        API -->|TCP : 5432| DB[(🐘 PostgreSQL)]
        API -->|AMQP : 5672| Queue[🐰 RabbitMQ]
        
        SecretFile[📄 .env] -.->|Inyecta| API
        SecretFile -.->|Inyecta| DB
        SecretFile -.->|Inyecta| Queue
    end
2. Decisiones de Diseño Justificadas
A. SSL Termination en Nginx
Decisión: Descifrar el tráfico HTTPS en el balanceador de carga (Nginx) y hablar HTTP plano dentro de la red Docker interna.

Por qué: Reduce la carga de CPU en los contenedores de Python (FastAPI), permitiéndoles procesar más ventas por segundo. Simplifica la gestión de certificados al centralizarla en un solo punto de entrada.

B. Secretos en Variables de Entorno
Decisión: Usar docker-compose con env_file (.env).

Por qué: Es el estándar de la industria para contenedores (metodología 12-Factor App). Evita que las contraseñas queden "quemadas" (hardcoded) en las imágenes de Docker o expuestas en el historial de Git.

C. Autenticación en Capa de Aplicación
Decisión: El middleware de JWT vive en la API (CentralAPI), no en Nginx.

Por qué: Permite una lógica de autorización más fina y granular (roles específicos, permisos por endpoint) que sería muy compleja y rígida de configurar solo en el servidor web Nginx.
