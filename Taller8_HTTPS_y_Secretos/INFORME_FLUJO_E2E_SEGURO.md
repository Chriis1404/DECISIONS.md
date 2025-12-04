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

------------------------------------------------------------------------

Validación del **Hito 2**.
