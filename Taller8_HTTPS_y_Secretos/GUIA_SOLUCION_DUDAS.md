# 🆘 Guía de Solución de Problemas y Preguntas Frecuentes

Este documento explica comportamientos esperados y soluciones a dudas comunes durante la validación del Taller 8.

---

## 1. 🚨 ¿Por qué el navegador dice "No es seguro"?

Al acceder a `https://localhost`, verás una pantalla roja o un candado tachado.
* **Causa:** Estamos usando un **Certificado Autofirmado** (`openssl`) generado por nosotros mismos, no por una autoridad certificadora global (como Verisign o Let's Encrypt).
* **¿Es un error?** **NO.** Esto es el comportamiento correcto y esperado en un entorno de desarrollo local.
* **Estado del Cifrado:** A pesar de la advertencia, **tu tráfico SÍ está cifrado**. Nadie en la red puede leer tus datos.

**Solución para entrar:**
1.  Haz clic en "Configuración avanzada" o "Más información".
2.  Selecciona "Continuar a localhost (no seguro)".
3.  Verás el Dashboard funcionando.

---

## 2. 📊 ¿Dónde está mi Dashboard?

En la arquitectura final con Nginx, todo el tráfico entra por el puerto estándar seguro **443**.
* **URL Correcta:** `https://localhost/dashboard`
* **Nota:** No necesitas especificar el puerto `:443` porque es el default de HTTPS.

Si intentas entrar a `http://localhost` (puerto 80), Nginx te redirigirá automáticamente a la versión segura.

---

## 3. 🦈 Prueba de Seguridad con Wireshark (Opcional)

Para demostrar que el tráfico viaja cifrado y que las contraseñas no son legibles:

**Paso 1: Captura Insegura (Antes)**
* Si apagaras Nginx y usaras HTTP directo (`:8000`), verías el JSON plano:
  `POST /login ... {"password": "admin123"}` (Texto legible ❌).

**Paso 2: Captura Segura (Ahora)**
1.  Abre Wireshark y filtra por puerto: `tcp.port == 443`.
2.  Haz Login en el Dashboard.
3.  **Resultado:** Solo verás paquetes **TLSv1.2 / TLSv1.3**.
4.  Si inspeccionas el contenido ("Follow Stream"), verás caracteres basura ilegibles.
  `......` (Datos Cifrados ✅).

---

## 4. 🚫 ¿Por qué no puedo entrar directo al puerto 8000?

Si intentas acceder a `http://localhost:8000` desde tu navegador y falla, depende de tu configuración de Docker.
* En nuestra arquitectura de seguridad ideal (Zero Trust), los contenedores de la API (`central1`, `central2`) **no deberían exponer puertos al host**.
* Solo **Nginx** debe ser accesible desde afuera. Esto obliga a que todo el tráfico pase por el "Control de Seguridad" (SSL Termination) y nadie pueda saltarse las reglas.

---

## 5. 🛠️ Error: "Connection Refused" o "Bad Gateway"

Si Nginx te da un error `502 Bad Gateway`:
1.  Significa que Nginx está vivo, pero la API Central (`central1`) no responde.
2.  **Causa común:** La API está tardando en arrancar o falló la conexión a la Base de Datos.
3.  **Solución:** Revisa los logs:
    ```bash
    docker-compose logs central1
    ```
    Espera unos segundos a que la API diga "Application startup complete".

---
*Guía elaborada para el equipo de EcoMarket - Hito 2.*
