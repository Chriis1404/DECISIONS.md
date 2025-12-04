# 🩺 Reto IA #1: Diagnóstico de Vulnerabilidades (Estado Inicial)

**Fecha:** 3 de Diciembre de 2025  
**Proyecto:** EcoMarket (Pre-Taller 8)  
**Auditoría:** Auto-Evaluación Arquitectónica

---

## 1. Contexto de la Arquitectura (Antes de los cambios)
* **Backend:** Python (FastAPI) expuesto directamente o vía Nginx en puerto 80.
* **Base de Datos:** PostgreSQL Cluster (Taller 6).
* **Mensajería:** RabbitMQ con credenciales por defecto (`ecomarket_user`).
* **Autenticación:** JWT implementado en Taller 7, pero la `SECRET_KEY` residía en el código fuente.
* **Despliegue:** Docker Compose local.

---

## 2. Matriz de Riesgos Detectados

| Riesgo | Nivel | Evidencia en Código | Impacto de Negocio |
| :--- | :---: | :--- | :--- |
| **Credenciales Expuestas** | 🔴 CRÍTICO | Archivo `docker-compose.yml` contenía `POSTGRES_PASSWORD=postgres_pass` y `RABBITMQ_DEFAULT_PASS` en texto plano. | Si el repositorio es público o se comparte, cualquier persona tiene acceso total a la base de datos y al sistema de mensajes. |
| **Tráfico No Cifrado (HTTP)** | 🔴 CRÍTICO | El sistema operaba en `http://localhost:80`. | Un atacante en la misma red (Sniffer) puede capturar el Token JWT en el header `Authorization` y suplantar al administrador. |
| **Secreto de Firma Inseguro** | 🔴 CRÍTICO | `CentralAPI.py` tenía la variable `SECRET_KEY` escrita en el código. | Imposible rotar la clave sin modificar el código y redesplegar. Si se filtra, todos los tokens históricos quedan comprometidos. |

---

## 3. Plan de Remediación (Hoja de Ruta Taller 8)

1.  **Saneamiento de Secretos:** Migrar todas las credenciales a un archivo `.env` excluido del control de versiones (`.gitignore`).
2.  **Cifrado en Tránsito:** Implementar certificados SSL (autofirmados para desarrollo) y configurar Nginx para terminar HTTPS en el puerto 443.
3.  **Inyección Segura:** Configurar `docker-compose` para leer variables de entorno en tiempo de ejecución.

---
*Reporte generado para la validación del Hito 2.*
