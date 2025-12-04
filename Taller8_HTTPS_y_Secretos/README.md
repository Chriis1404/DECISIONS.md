# 🔒 **EcoMarket - Taller 8: Comunicación Segura y Secretos**
![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-green?logo=nginx)
![SSL](https://img.shields.io/badge/SSL-HTTPS-blue?logo=letsencrypt)
![Security](https://img.shields.io/badge/Security-12_Factor_App-red)

### 🛡️ *Hito 2: Despliegue Seguro con HTTPS, JWT y Docker*

📅 **Fecha:** 3 de Diciembre de 2025  
👤 **Autores:** Christofer Roberto Esparza Chavero 
📂 **Estado:** Finalizado (Producción Local)

---

## 📝 **Resumen de la Entrega**
Este taller finaliza la unidad de seguridad integrando **Cifrado de Transporte (HTTPS)** y **Gestión de Secretos**.

Hemos eliminado las vulnerabilidades críticas detectadas en etapas anteriores, asegurando que ninguna credencial viva en el código fuente y que todo el tráfico sensible viaje encriptado.

---

## 🛠️ **Guía de Implementación**

### 1. Generación de Certificados (Local)
Se utilizaron certificados autofirmados con OpenSSL para habilitar TLS en desarrollo.
* **Llave Privada:** `certs/nginx-selfsigned.key`
* **Certificado:** `certs/nginx-selfsigned.crt`

### 2. Configuración de Secretos
Se creó un archivo `.env` (ignorado por git) que contiene:
* `POSTGRES_PASSWORD`
* `RABBITMQ_DEFAULT_PASS`
* `JWT_SECRET`

> ℹ️ **Nota para el revisor:** Se incluye un archivo `.env.example` en la raíz como referencia segura.

### 3. Despliegue Seguro
```bash
# 1. Asegurar que el .env existe con las credenciales
# 2. Levantar el entorno con construcción limpia
docker-compose up -d --build
```

## 🧪 Pruebas de Validación (E2E)
**Redirección Forzada:** Acceder a http://localhost redirige automáticamente a https://localhost.

**Verificación TLS:** El navegador muestra el certificado (autofirmado) y la conexión cifrada.

**Protección de Secretos:** Inspección del contenedor demuestra que las variables de entorno se inyectaron correctamente sin estar en el Dockerfile.

---
## 📚 Documentación y Evidencias del Hito 2

Este repositorio incluye la documentación completa de todas las actividades, retos de IA y auditorías solicitadas en la guía de aprendizaje.

### 🏗️ Informes Técnicos y Arquitectura
* [**Evolución del Proyecto (Monolito a Seguro)**](./EVOLUCION_ECOMARKET.md) - Historia técnica de EcoMarket.
* [**Diseño de Arquitectura Segura (Reto IA #5)**](./RETO_IA_5_ARQUITECTURA_SEGURIDAD.md) - Topología de red y justificación de seguridad.
* [**Informe de Flujo E2E Seguro**](./INFORME_FLUJO_E2E_SEGURO.md) - Diagramas de secuencia del Login y Validación.
* [**Conclusión Técnica Final**](./CONCLUSION_INFORME_HITO_2.md) - Análisis de la Tríada CIA y beneficios DevOps.

### 🔍 Auditorías y Diagnósticos
* [**Diagnóstico de Seguridad Inicial (Reto IA #1)**](./DIAGNOSTICO_SEGURIDAD_INICIAL.md) - Estado vulnerable antes del Taller 8.
* [**Auditoría de Código Estática**](./AUDITORIA_CODIGO.md) - Búsqueda de secretos hardcodeados (`grep`).
* [**Auditoría de Configuración de Secretos (Reto IA #3)**](./REPORTE_AUDITORIA_SECRETOS.md) - Validación de `.env` y 12-Factor App.
* [**Auditoría de Cierre y Score (Reto IA Final)**](./AUDITORIA_FINAL_HITO_2.md) - Evaluación final de seguridad (90/100).

### 🧠 Reflexiones y Guías
* [**Análisis de Amenazas (Fase 0)**](./REFLEXION_FASE_0.md) - Reflexión sobre GitHub Leaks y ataques MITM.
* [**Errores Comunes en Gestión de Secretos**](./ERRORES_COMUNES_SECRETOS.md) - Guía de antipatrones evitados.
* [**🆘 Guía de Solución de Dudas**](./GUIA_SOLUCION_DUDAS.md) - Troubleshooting para certificados y Docker.

---

## 🎬 Video de Demostración Final
Demostración completa del Hito 2: HTTPS, Login Seguro y Manejo de Secretos.

👉 [VER VIDEO AQUÍ](https://drive.google.com/file/d/1nJIr0jmzlBhHkmkr-tyZF35jIYJhMnhd/view?usp=sharing)

---
