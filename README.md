# 🌿 **EcoMarket: Arquitectura de Sistemas Distribuidos Seguros**

![Status](https://img.shields.io/badge/Estado-Producción_Local-success?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Backend-FastAPI-yellow?style=for-the-badge&logo=fastapi&logoColor=black)
![Security](https://img.shields.io/badge/Security-JWT_%2B_HTTPS-red?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Infra](https://img.shields.io/badge/Infra-Nginx_%2B_RabbitMQ-blue?style=for-the-badge&logo=nginx)

> **Hito 2 Finalizado:** Transformación completa de un script monolítico a una plataforma de microservicios distribuida, resiliente y blindada con seguridad de grado industrial.

---

## 🏗️ **Arquitectura Final del Sistema (Hito 2)**

El sistema opera bajo un modelo **Zero-Trust Network**, donde todo el tráfico es cifrado y gestionado por un Gateway seguro.

```mermaid
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

---

## 🚀 **Servicios Activos y Accesos**

| Servicio | URL de Acceso | Descripción Técnica |
|---------|---------------|---------------------|
| 🔒 **Secure Gateway** | https://localhost | Punto de entrada único. Terminación SSL + redirección automática. |
| 🛡️ **Central Dashboard** | https://localhost/dashboard | Panel administrativo protegido por JWT. |
| 🏪 **Sucursal Demo** | http://localhost:8002 | Nodo autónomo Offline‑First para ventas. |
| 🐰 **RabbitMQ Admin** | http://localhost:15672 | User: ecomarket_user / Pass: ecomarket_password |
| 📚 **Documentación API** | https://localhost/docs | Swagger UI generado por FastAPI. |

---

## 🛠️ **Guía de Despliegue Rápido**

### **1. Configuración de Secretos**

```bash
cp .env.example .env
```

---

### **2. Despliegue con Docker**

```bash
docker-compose up -d --build
```

---

### **3. Validación**

Accede a: **http://localhost** → Redirige a **HTTPS**.

Credenciales admin:

- Usuario: **admin**  
- Contraseña: **admin123**

---

## 🗺️ **Hoja de Ruta: Evolución del Proyecto**

### 🟢 Fase 1: Fundamentos
- Taller 1: Arquitectura Monolítica  
- Taller 2: Sockets TCP/UDP  

### 🟡 Fase 2: Distribución
- Taller 3: Arquitectura Distribuida  
- Taller 4: Pub/Sub con RabbitMQ  
- Taller 5: Balanceo con Nginx  
- Taller 6: PostgreSQL Distribuido  

### 🔴 Fase 3: Seguridad
- Taller 7: JWT + Hashing  
- Taller 8: HTTPS + Secretos  

---

## 🛡️ **Auditoría de Seguridad (Hito 2)**

- Confidencialidad: TLS 1.3 + secretos fuera del código  
- Integridad: JWT firmados + bcrypt  
- Disponibilidad: Infra redundante  

---

## 👥 **Créditos**

- **Christofer Roberto Esparza Chavero**

Trabajaron solo el 70% del trabajo
- Brian Garcia  
- Juan Cordova  

Proyecto — Programación del Lado del Servidor 2025
