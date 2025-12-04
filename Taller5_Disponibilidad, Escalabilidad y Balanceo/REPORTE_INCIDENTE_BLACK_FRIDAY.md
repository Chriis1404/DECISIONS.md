# 🚨 Reporte de Incidente: Caída del Black Friday

**Fecha:** 12 de Noviembre 2025  
**Severidad:** Crítica  
**Duración:** 45 minutos

### Descripción del Evento
A las 09:00 AM, el tráfico aumentó un 400% debido a las ofertas. La instancia única de `central-api` alcanzó el 100% de uso de CPU y dejó de responder. Las sucursales entraron en modo offline, pero la sincronización fallaba.

### Causa Raíz
* Arquitectura no escalable (1 sola instancia).
* Procesamiento síncrono de imágenes en el hilo principal.

### Acciones Correctivas (Taller 5)
1.  Desplegar clúster de 3 réplicas de la API.
2.  Implementar Nginx como punto de entrada único.
3.  Configurar reinicio automático de contenedores (`restart: always`).

### Resultado
Con la nueva arquitectura, el sistema soportó 3x la carga del incidente original sin degradación de servicio.
