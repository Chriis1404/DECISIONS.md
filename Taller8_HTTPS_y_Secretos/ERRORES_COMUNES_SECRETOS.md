# 🔍 Errores Comunes en Gestión de Secretos (Y Soluciones)

Durante la implementación del Taller 8, evitamos activamente los siguientes antipatrones de seguridad:

### 1. Entropía Baja
* **Error:** Usar claves cortas como `secret123`.
* **Solución:** Generamos claves de 256 bits usando `openssl rand -hex 32`.

### 2. Leak en Logs
* **Error:** Hacer `print(os.environ)` para debuggear.
* **Solución:** Configuramos el logger para no imprimir variables sensibles y eliminamos los prints de depuración en producción.

### 3. Mismo Secreto en Todos los Entornos
* **Error:** Usar la misma `SECRET_KEY` en Desarrollo y Producción.
* **Solución:** El archivo `.env` no se versiona. Cada servidor (Dev, Staging, Prod) tiene su propio archivo `.env` con claves únicas generadas en el momento del despliegue.

### 4. Confiar solo en .gitignore
* **Error:** Subir el `.env` por error y luego borrarlo y agregarlo al gitignore.
* **Realidad:** El archivo sigue en el historial de Git (`.git`).
* **Solución:** Si un secreto toca GitHub, se considera quemado y **DEBE** rotarse inmediatamente.

---
*Guía de referencia para el equipo de desarrollo.*
