# 🔗 Actividad Integradora: Flujo E2E Seguro

Este documento detalla el flujo completo de seguridad End-to-End (E2E)
implementado en EcoMarket, integrando **HTTPS (TLS)**, **Autenticación
JWT** y **Gestión de Secretos**.

## 1. Diagrama de Secuencia del Flujo Seguro

``` mermaid
sequenceDiagram
    participant Client as 📱 Cliente (Browser)
    participant Nginx as 🔒 Nginx (Gateway)
    participant Auth as 🛡️ Auth Service
    participant API as 🐍 Central API
    participant DB as 🐘 Base de Datos

    Note over Client, Nginx: Canal Seguro (HTTPS / TLS 1.3)

    Client->>Nginx: POST /login {user, pass} (Cifrado)
    Nginx->>Auth: Forward HTTP (Interno)

    Auth->>DB: SELECT user WHERE username=...
    DB-->>Auth: Hash del Password

    Note right of Auth: verify_hash(bcrypt)

    Auth->>Auth: Sign JWT (SECRET_KEY del .env)
    Auth-->>Nginx: 200 OK { "access_token": "..." }
    Nginx-->>Client: 200 OK (Cifrado TLS)

    Note over Client: Cliente guarda Token

    Client->>Nginx: GET /inventory (Authorization: Bearer ...)
    Nginx->>API: Forward Request

    Note right of API: Middleware valida Firma y Expiración

    API-->>Nginx: 200 OK (Datos JSON)
    Nginx-->>Client: 200 OK (Cifrado TLS)
```

## 2. Capas de Protección Explicadas

  --------------------------------------------------------------------------
  Capa              Amenaza Mitigada         Tecnología
  ----------------- ------------------------ -------------------------------
  Transporte        Sniffing /               HTTPS (TLS) en Nginx
                    Man-in-the-Middle        

  Identidad         Suplantación de Usuario  JWT firmado digitalmente

  Datos             Robo de Base de Datos    Hashing bcrypt para contraseñas

  Infraestructura   Fuga de Código Fuente    Variables de entorno (.env)

  --------------------------------------------------------------------------
## 2. Análisis de Seguridad: Capas de Protección y Fallos

Documentación del análisis de riesgo residual para cada componente de seguridad implementado.

### 🔒 ¿Qué protege HTTPS (TLS 1.3)?
* **Función:** Garantiza la **Confidencialidad** e **Integridad** de los datos en tránsito. Cifra todo el tráfico entre el cliente y Nginx.
* **¿Qué pasa si falla? (Riesgo):** Si el certificado expira o se deshabilita TLS, el tráfico viaja en texto plano. Un atacante en la misma red (WiFi pública) podría realizar un ataque *Man-in-the-Middle (MITM)* y leer las contraseñas de login o robar el Token JWT para suplantar la sesión.

### 🔑 ¿Qué protege JWT (JSON Web Token)?
* **Función:** Garantiza la **Identidad** (Autenticación) y **Autorización** del usuario de forma *stateless*. Asegura que quien hace la petición es quien dice ser y tiene los permisos (roles) adecuados.
* **¿Qué pasa si falla? (Riesgo):** Si la validación de firma falla o el secreto es débil, un atacante podría forjar tokens falsos y acceder como administrador (`role: admin`) sin conocer la contraseña, comprometiendo toda la plataforma.

### 📄 ¿Qué protege el archivo .env?
* **Función:** Mantiene los **Secretos** (contraseñas de BD, llaves JWT) fuera del código fuente, siguiendo la metodología *12-Factor App*.
* **¿Qué pasa si falla? (Riesgo):** Si el archivo `.env` se sube al repositorio por error (fallo en `.gitignore`), las credenciales quedan expuestas permanentemente en el historial de Git. Cualquier persona con acceso al repo tendría acceso total a la base de datos y podría generar tokens válidos.

---
*Validación del flujo E2E para el Hito 2.*
------------------------------------------------------------------------

Validación del **Hito 2**.
